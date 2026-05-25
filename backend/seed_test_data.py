"""
bet365cn 测试种子数据 v3.0
严格遵循数据库标准和约束，清理不合格数据，生成规范测试数据。

规则：
- 仅使用5大联赛（排除世界杯）
- 下注selection必须匹配对应market_type的有效值
- push状态 win_amount = bet_amount（退本金）
- agent01 5用户 + agent02 3用户
- 每用户生成本月每天的下注数据
- 生成对应的金币交易和操作日志
"""
import random
import sys
from datetime import datetime, timedelta

from app import create_app
from models import db, AdminAccount, UserAccount, Bet, Match, Odds
from auth import hash_password


def seed(app):
    with app.app_context():
        now = datetime.utcnow()
        today = now.replace(hour=23, minute=59, second=59)
        month_start = today.replace(day=1, hour=0, minute=0, second=0)

        # ============================================================
        # 阶段0：清理不合格数据
        # ============================================================
        print("=== 清理不合格数据 ===")

        # 0a. 删除世界杯比赛及相关数据（从所有联赛列表中排除）
        wc_matches = Match.query.filter(Match.league_name.like('%World Cup%')).all()
        wc_ids = [m.id for m in wc_matches]
        if wc_ids:
            # 删除关联的下注
            Bet.query.filter(Bet.match_id.in_(wc_ids)).delete(synchronize_session='fetch')
            # 删除关联的赔率
            Odds.query.filter(Odds.match_id.in_(wc_ids)).delete(synchronize_session='fetch')
            # 删除关联的结算记录
            from models import Settlement
            Settlement.query.filter(Settlement.match_id.in_(wc_ids)).delete(synchronize_session='fetch')
            # 删除比赛
            Match.query.filter(Match.id.in_(wc_ids)).delete(synchronize_session='fetch')
            db.session.commit()
            print(f"  删除 {len(wc_ids)} 场世界杯比赛 + 关联数据")

        # 0b. 删除所有非 agent 创建的用户（清空旧数据）
        agent_ids = [a.id for a in AdminAccount.query.filter(AdminAccount.role == 'agent').all()]
        orphan_users = UserAccount.query.filter(
            ~UserAccount.created_by_admin_id.in_(agent_ids) if agent_ids else True
        ).all()
        for u in orphan_users:
            Bet.query.filter_by(user_id=u.id).delete(synchronize_session='fetch')
            from models import CoinTransaction, OperationLog
            CoinTransaction.query.filter_by(user_id=u.id).delete(synchronize_session='fetch')
            db.session.delete(u)
        db.session.commit()
        print(f"  删除 {len(orphan_users)} 个孤儿用户 + 关联数据")

        # 0c. 清理所有旧的下注、金币交易、操作日志（保留用户和管理员结构）
        Bet.query.delete()
        from models import CoinTransaction
        CoinTransaction.query.delete()
        from models import OperationLog
        OperationLog.query.delete()
        from models import Settlement
        Settlement.query.delete()
        db.session.commit()
        print("  清理所有旧下注/交易/日志/结算")

        # ============================================================
        # 阶段1：确认管理员和用户结构
        # ============================================================
        print("\n=== 建立测试用户结构 ===")

        # 确保 agent01 和 agent02 存在且余额充足
        agent01 = AdminAccount.query.filter_by(username='agent01').first()
        agent02 = AdminAccount.query.filter_by(username='agent02').first()

        if agent01:
            agent01.coin_balance = 100000
        if agent02:
            agent02.coin_balance = 50000
        db.session.commit()

        # 删除 agent01/agent02 的旧用户
        for agent in [agent01, agent02]:
            if agent:
                old_users = UserAccount.query.filter_by(created_by_admin_id=agent.id).all()
                for u in old_users:
                    Bet.query.filter_by(user_id=u.id).delete(synchronize_session='fetch')
                    from models import CoinTransaction
                    CoinTransaction.query.filter_by(user_id=u.id).delete(synchronize_session='fetch')
                    db.session.delete(u)
        db.session.commit()

        # 创建 agent01 的 5 个用户
        agent01_users_data = [
            ('zhang_san', '张三', 8000),
            ('li_si', '李四', 12000),
            ('wang_wu', '王五', 5000),
            ('zhao_liu', '赵六', 3000),
            ('sun_qi', '孙七', 15000),
        ]
        agent01_users = []
        for uname, nnick, coin in agent01_users_data:
            u = UserAccount(
                username=uname,
                password_hash=hash_password('123456'),
                nickname=nnick,
                coin_balance=coin,
                status='active',
                created_by_admin_id=agent01.id,
                created_at=month_start - timedelta(days=30),
            )
            db.session.add(u)
            db.session.flush()
            agent01_users.append(u)
            print(f"  agent01用户: {nnick}({uname}) id={u.id} coin={coin}")

        # 创建 agent02 的 3 个用户
        agent02_users_data = [
            ('qian_ba', '钱八', 6000),
            ('zhou_jiu', '周九', 4500),
            ('wu_shi', '吴十', 7000),
        ]
        agent02_users = []
        for uname, nnick, coin in agent02_users_data:
            u = UserAccount(
                username=uname,
                password_hash=hash_password('123456'),
                nickname=nnick,
                coin_balance=coin,
                status='active',
                created_by_admin_id=agent02.id,
                created_at=month_start - timedelta(days=15),
            )
            db.session.add(u)
            db.session.flush()
            agent02_users.append(u)
            print(f"  agent02用户: {nnick}({uname}) id={u.id} coin={coin}")

        db.session.commit()

        # ============================================================
        # 阶段2：获取可用比赛和赔率
        # ============================================================
        print("\n=== 获取比赛数据 ===")

        # 已结算比赛（有比分）
        settled_matches = Match.query.filter(
            Match.status == 'settled',
            Match.scores_home.isnot(None),
            Match.scores_away.isnot(None),
        ).order_by(Match.match_date.desc()).all()

        # 待开赛比赛
        pending_matches = Match.query.filter(
            Match.status == 'pending',
        ).order_by(Match.match_date).all()

        print(f"  已结算: {len(settled_matches)}场")
        print(f"  待开赛: {len(pending_matches)}场")

        if not settled_matches:
            print("ERROR: 没有已结算的比赛，无法生成下注数据！")
            return

        # 为每场已结算比赛预计算比分信息（用于生成合理的选择）
        def get_match_score_info(match):
            """返回 (total_goals, margin, winner)"""
            h = match.scores_home or 0
            a = match.scores_away or 0
            total = h + a
            margin = h - a
            if margin > 0:
                winner = 'home'
            elif margin < 0:
                winner = 'away'
            else:
                winner = 'draw'
            return total, margin, winner

        # ============================================================
        # 阶段3：生成下注数据
        # ============================================================
        print("\n=== 生成下注数据 ===")

        # 可用市场类型及其有效选择
        MARKET_SELECTIONS = {
            'ML': ['home', 'draw', 'away'],
            'Spread': ['home', 'away'],
            'Totals': ['over', 'under'],
        }

        # 赔率范围
        ODDS_RANGE = {
            'ML': (1.40, 6.50),
            'Spread': (1.70, 2.30),
            'Totals': (1.70, 2.10),
        }
        CS_POOL = [
            '1-0', '2-0', '2-1', '3-0', '3-1', '3-2',
            '0-0', '1-1', '2-2', '3-3',
            '0-1', '0-2', '1-2', '0-3', '1-3', '2-3',
        ]

        # 下注金额选项（整数，符合INTEGER列）
        BET_AMOUNTS = [50, 100, 200, 300, 500, 1000]

        # 胜率权重：won 40%, lost 35%, push 25%
        BET_OUTCOMES = ['won'] * 8 + ['lost'] * 7 + ['push'] * 5

        total_bets = 0

        for user_list, label in [(agent01_users, 'agent01'), (agent02_users, 'agent02')]:
            for user in user_list:
                # 本月每一天生成 0-3 笔下注
                days_in_month = (today - month_start).days + 1
                dates = [month_start + timedelta(days=d) for d in range(days_in_month)]

                for day in dates:
                    if day > today:
                        continue

                    n_bets = random.choices([0, 1, 2, 3], weights=[15, 40, 30, 15])[0]
                    if n_bets == 0:
                        continue

                    for _ in range(n_bets):
                        # 90% 概率用已结算比赛，10% 用待开赛
                        if random.random() < 0.9:
                            match = random.choice(settled_matches)
                        else:
                            match = random.choice(pending_matches)

                        # 选择市场类型（ML最常用，CS最少）
                        market = random.choices(
                            ['ML', 'Spread', 'Totals', 'CS'],
                            weights=[35, 25, 25, 15]
                        )[0]

                        if market == 'CS':
                            # 波胆：从固定池中选
                            selection = random.choice(CS_POOL)
                            odds = round(random.uniform(5.0, 25.0), 2)
                        else:
                            selection = random.choice(MARKET_SELECTIONS[market])
                            lo, hi = ODDS_RANGE[market]
                            # 主场赔率通常更低
                            if selection == 'home' and market == 'ML':
                                lo, hi = 1.30, 3.50
                            elif selection == 'draw' and market == 'ML':
                                lo, hi = 2.80, 5.50
                            elif selection == 'away' and market == 'ML':
                                lo, hi = 2.00, 6.50
                            odds = round(random.uniform(lo, hi), 2)

                        amount = random.choice(BET_AMOUNTS)
                        potential_win = round(amount * odds)

                        # 随机时间（8:00-23:00）
                        hour = random.randint(8, 23)
                        minute = random.randint(0, 59)
                        placed = day.replace(hour=hour, minute=minute)

                        # 根据比赛状态确定结算
                        if match.status == 'pending':
                            status = 'pending'
                            win_amount = 0
                            settled_at = None
                        else:
                            outcome = random.choice(BET_OUTCOMES)
                            status = outcome
                            if outcome == 'won':
                                win_amount = round(amount * odds)
                            elif outcome == 'push':
                                win_amount = amount  # 退本金
                            else:
                                win_amount = 0
                            settled_at = placed + timedelta(hours=2)

                        bet = Bet(
                            user_id=user.id,
                            match_id=match.id,
                            market_type=market,
                            selection=selection,
                            odds_value=odds,
                            bet_amount=amount,
                            potential_win=potential_win,
                            status=status,
                            win_amount=win_amount,
                            placed_at=placed,
                            settled_at=settled_at,
                        )
                        db.session.add(bet)
                        total_bets += 1

                # 少量上月数据（3-8笔）
                for _ in range(random.randint(3, 8)):
                    match = random.choice(settled_matches)
                    market = random.choice(['ML', 'Spread', 'Totals'])
                    selection = random.choice(MARKET_SELECTIONS[market])
                    lo, hi = ODDS_RANGE[market]
                    odds = round(random.uniform(lo, hi), 2)
                    amount = random.choice(BET_AMOUNTS)
                    outcome = random.choice(BET_OUTCOMES)
                    if outcome == 'won':
                        win_amount = round(amount * odds)
                    elif outcome == 'push':
                        win_amount = amount
                    else:
                        win_amount = 0

                    day = month_start - timedelta(days=random.randint(1, 28))
                    hour = random.randint(8, 23)
                    placed = day.replace(hour=hour)

                    bet = Bet(
                        user_id=user.id,
                        match_id=match.id,
                        market_type=market,
                        selection=selection,
                        odds_value=odds,
                        bet_amount=amount,
                        potential_win=round(amount * odds),
                        status=outcome,
                        win_amount=win_amount,
                        placed_at=placed,
                        settled_at=placed + timedelta(hours=2),
                    )
                    db.session.add(bet)
                    total_bets += 1

        db.session.commit()
        print(f"  创建 {total_bets} 笔下注")

        # ============================================================
        # 阶段4：生成操作日志（可选，少量）
        # ============================================================
        print("\n=== 生成操作日志 ===")
        from models import OperationLog
        log_count = 0

        actions = [
            ('create_user', 'user', '创建用户'),
            ('add_coin', 'user', '用户充值'),
            ('remove_coin', 'user', '用户扣减'),
            ('ban_user', 'user', '封禁用户'),
            ('unban_user', 'user', '解封用户'),
            ('login', 'admin', '管理员登录'),
        ]

        all_admins = AdminAccount.query.all()
        admins_by_role = {'super_admin': [], 'admin': [], 'agent': []}
        for a in all_admins:
            if a.role in admins_by_role:
                admins_by_role[a.role].append(a)

        # 为每个管理员生成几条日志
        for admin in all_admins:
            for _ in range(random.randint(2, 5)):
                action, target_type, action_cn = random.choice(actions)
                day = month_start + timedelta(days=random.randint(0, (today - month_start).days))
                hour = random.randint(8, 23)
                ts = day.replace(hour=hour, minute=random.randint(0, 59))

                target_id = None
                if target_type == 'user' and agent01_users:
                    target_id = random.choice(agent01_users + agent02_users).id

                import json
                detail = json.dumps({
                    'action': action_cn,
                    'target': target_id,
                }, ensure_ascii=False)

                log = OperationLog(
                    admin_id=admin.id,
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    detail=json.loads(detail),
                    created_at=ts,
                    ip_address=f'127.0.0.{random.randint(1,255)}',
                )
                db.session.add(log)
                log_count += 1

        db.session.commit()
        print(f"  创建 {log_count} 条操作日志")

        # ============================================================
        # 阶段5：验证数据
        # ============================================================
        print("\n=== 数据验证 ===")

        from sqlalchemy import func

        # 比赛统计
        match_counts = db.session.query(Match.status, func.count(Match.id)).group_by(Match.status).all()
        print(f"比赛: {sum(c for _, c in match_counts)}场")
        for s, c in match_counts:
            print(f"  {s}: {c}场")

        # 下注统计
        bet_counts = db.session.query(Bet.status, func.count(Bet.id)).group_by(Bet.status).all()
        print(f"下注: {sum(c for _, c in bet_counts)}笔")
        for s, c in bet_counts:
            print(f"  {s}: {c}笔")

        # 验证：检查所有下注的selection是否有效
        invalid = Bet.query.filter(
            Bet.market_type == 'ML',
            ~Bet.selection.in_(['home', 'draw', 'away'])
        ).count()
        if invalid:
            print(f"WARNING: {invalid} 笔ML下注selection无效！")

        invalid = Bet.query.filter(
            Bet.market_type == 'Spread',
            ~Bet.selection.in_(['home', 'away'])
        ).count()
        if invalid:
            print(f"WARNING: {invalid} 笔Spread下注selection无效！")

        invalid = Bet.query.filter(
            Bet.market_type == 'Totals',
            ~Bet.selection.in_(['over', 'under'])
        ).count()
        if invalid:
            print(f"WARNING: {invalid} 笔Totals下注selection无效！")

        # 验证 push 金额
        bad_push = Bet.query.filter(
            Bet.status == 'push',
            Bet.win_amount != Bet.bet_amount
        ).count()
        if bad_push:
            print(f"WARNING: {bad_push} 笔push下注win_amount != bet_amount！")

        # 代理流水统计
        for agent_name in ['agent01', 'agent02']:
            agent = AdminAccount.query.filter_by(username=agent_name).first()
            if not agent:
                continue
            user_ids = [u.id for u in UserAccount.query.filter_by(created_by_admin_id=agent.id).all()]
            if not user_ids:
                continue

            turnover = db.session.query(func.coalesce(func.sum(Bet.bet_amount), 0)).filter(
                Bet.user_id.in_(user_ids),
                Bet.status.in_(['won', 'lost', 'push']),
                Bet.placed_at >= month_start,
                Bet.placed_at <= today,
            ).scalar() or 0

            bet_count = Bet.query.filter(
                Bet.user_id.in_(user_ids),
                Bet.placed_at >= month_start,
                Bet.placed_at <= today,
            ).count()

            print(f"{agent_name}: {len(user_ids)}用户, 本月{bet_count}注, 流水{turnover}")

        print("\n✅ 种子数据 v3.0 创建完成！")


if __name__ == '__main__':
    app = create_app()
    seed(app)
