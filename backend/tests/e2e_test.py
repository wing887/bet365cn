# bet365cn E2E 自动化测试 — 20轮全流程验证
"""
每轮流程:
1. 清空测试数据
2. 创建5场虚拟比赛(含完整赔率)
3. test001对所有盘口下注
4. 随机比分结算
5. 验证数据一致性
"""
import sys, os, random, json, hashlib, time
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, '/mnt/c/Users/admin/Desktop/bet365cn/backend')

from app import create_app
from config import DevelopmentConfig
from models import db, Match, Odds, Bet, UserAccount, CoinTransaction

app = create_app(DevelopmentConfig)

# ============================================================
# 测试配置
# ============================================================
ROUNDS = 20
BET_AMOUNT = 100  # 每注100金币

TEAMS = [
    ('英超', 'England - Premier League', 'england-premier-league',
     [('曼城', 'Manchester City', '65'), ('阿森纳', 'Arsenal', '57'),
      ('利物浦', 'Liverpool', '64'), ('切尔西', 'Chelsea', '61'),
      ('曼联', 'Manchester United', '66'), ('热刺', 'Tottenham Hotspur', '73')]),
    ('西甲', 'Spain - LaLiga', 'spain-laliga',
     [('皇家马德里', 'Real Madrid', '86'), ('巴塞罗那', 'FC Barcelona', '81'),
      ('马德里竞技', 'Atlético Madrid', '78'), ('塞维利亚', 'Sevilla FC', '559')]),
    ('德甲', 'Germany - Bundesliga', 'germany-bundesliga',
     [('拜仁慕尼黑', 'Bayern Munich', '5'), ('多特蒙德', 'Borussia Dortmund', '4'),
      ('勒沃库森', 'Bayer Leverkusen', '3'), ('莱比锡红牛', 'RB Leipzig', '721')]),
    ('意甲', 'Italy - Serie A', 'italy-serie-a',
     [('尤文图斯', 'Juventus', '109'), ('国际米兰', 'Inter Milan', '108'),
      ('AC米兰', 'AC Milan', '98'), ('那不勒斯', 'Napoli', '113')]),
    ('法甲', 'France - Ligue 1', 'france-ligue-1',
     [('巴黎圣日耳曼', 'Paris Saint-Germain', '524'), ('里昂', 'Olympique Lyonnais', '523'),
      ('摩纳哥', 'AS Monaco', '548'), ('马赛', 'Olympique Marseille', '516')]),
]


def make_odds(home_stronger=True):
    """生成一套完整赔率"""
    if home_stronger:
        ml = {'home': round(random.uniform(1.3, 2.0), 2),
              'draw': round(random.uniform(3.0, 5.0), 2),
              'away': round(random.uniform(3.5, 7.0), 2)}
        hdp = random.choice([0.5, 0.75, 1.0, 1.25])
        spread = {'hdp': hdp, 'home': round(random.uniform(1.8, 2.1), 2),
                  'away': round(random.uniform(1.7, 2.0), 2)}
    else:
        ml = {'home': round(random.uniform(3.5, 7.0), 2),
              'draw': round(random.uniform(3.0, 5.0), 2),
              'away': round(random.uniform(1.3, 2.0), 2)}
        hdp = random.choice([-0.5, -0.75, -1.0])
        spread = {'hdp': hdp, 'home': round(random.uniform(1.7, 2.0), 2),
                  'away': round(random.uniform(1.8, 2.1), 2)}

    totals_hdp = random.choice([2.0, 2.25, 2.5, 2.75, 3.0, 3.25])
    totals = {'hdp': totals_hdp, 'over': round(random.uniform(1.75, 2.1), 2),
              'under': round(random.uniform(1.72, 2.05), 2)}

    scores = []
    for s in ['1-0', '2-0', '2-1', '1-1', '0-0', '3-0', '3-1', '0-1', '1-2', '0-2']:
        scores.append({'label': s, 'odds': round(random.uniform(5.0, 25.0), 2)})
    scores.sort(key=lambda x: x['odds'])

    return {
        'ML': ml, 'Spread': spread, 'Totals': totals,
        'CS': {'scores': scores[:10]}
    }


def clear_test_data():
    """清空测试相关数据，保留用户和管理员"""
    Bet.query.delete()
    CoinTransaction.query.delete()
    Odds.query.delete()
    Match.query.delete()
    # 确保 test001 存在
    user = UserAccount.query.filter_by(username='test001').first()
    if not user:
        user = UserAccount(
            username='test001',
            password_hash=hashlib.sha256('123456'.encode()).hexdigest(),
            nickname='测试001', coin_balance=100000, status='active'
        )
        db.session.add(user)
    else:
        user.coin_balance = 100000
    db.session.commit()


def create_matches():
    """创建5场虚拟比赛"""
    matches = []
    base_date = datetime.utcnow().replace(second=0, microsecond=0) + timedelta(minutes=5)

    for i, (cn_league, en_league, slug, teams_list) in enumerate(TEAMS):
        h_cn, h_en, h_logo = random.choice(teams_list)
        a_cn, a_en, a_logo = random.choice([t for t in teams_list if t[0] != h_cn])

        match_date = base_date + timedelta(minutes=i * 3)
        match = Match(
            event_id=f'test_round_{i}',
            home_team=h_en,
            away_team=a_en,
            league_name=en_league,
            league_slug=slug,
            match_date=match_date,
            status='pending',
        )
        db.session.add(match)
        matches.append({'match': match, 'home_cn': h_cn, 'away_cn': a_cn,
                        'home_logo': h_logo, 'away_logo': a_logo, 'league_cn': cn_league})

    db.session.commit()
    return matches


def create_odds(matches_data):
    """为每场比赛创建4种盘口赔率"""
    for md in matches_data:
        match = md['match']
        odds = make_odds(home_stronger=random.choice([True, False]))
        for market_type, odds_json in odds.items():
            o = Odds(
                match_id=match.id,
                bookmaker='Bet365',
                market_type=market_type,
                odds_data=odds_json,
            )
            db.session.add(o)
        md['odds'] = odds
    db.session.commit()


def place_bets(matches_data):
    """test001 对5场比赛所有盘口下注"""
    user = UserAccount.query.filter_by(username='test001').first()

    total_bets = 0
    for md in matches_data:
        match = md['match']
        odds = md['odds']

        # ML: 下3注 (home/draw/away)
        for sel in ['home', 'draw', 'away']:
            odd_val = odds['ML'].get(sel, 2.0)
            if odd_val <= 0:
                continue
            bet = Bet(user_id=user.id, match_id=match.id, market_type='ML',
                      selection=sel, odds_value=odd_val, bet_amount=BET_AMOUNT,
                      potential_win=round(BET_AMOUNT * odd_val), status='pending')
            db.session.add(bet)
            user.coin_balance -= BET_AMOUNT
            total_bets += 1

        # Spread: 下2注 (home/away)
        for sel in ['home', 'away']:
            odd_val = odds['Spread'].get(sel, 2.0)
            bet = Bet(user_id=user.id, match_id=match.id, market_type='Spread',
                      selection=sel, odds_value=odd_val, bet_amount=BET_AMOUNT,
                      potential_win=round(BET_AMOUNT * odd_val), status='pending')
            db.session.add(bet)
            user.coin_balance -= BET_AMOUNT
            total_bets += 1

        # Totals: 下2注 (over/under)
        for sel in ['over', 'under']:
            odd_val = odds['Totals'].get(sel, 2.0)
            bet = Bet(user_id=user.id, match_id=match.id, market_type='Totals',
                      selection=sel, odds_value=odd_val, bet_amount=BET_AMOUNT,
                      potential_win=round(BET_AMOUNT * odd_val), status='pending')
            db.session.add(bet)
            user.coin_balance -= BET_AMOUNT
            total_bets += 1

        # CS: 下2注 (随机选2个比分)
        cs_list = odds['CS']['scores']
        chosen = random.sample(cs_list, min(2, len(cs_list)))
        for cs in chosen:
            bet = Bet(user_id=user.id, match_id=match.id, market_type='CS',
                      selection=cs['label'], odds_value=cs['odds'], bet_amount=BET_AMOUNT,
                      potential_win=round(BET_AMOUNT * cs['odds']), status='pending')
            db.session.add(bet)
            user.coin_balance -= BET_AMOUNT
            total_bets += 1

    db.session.commit()
    return total_bets


def settle_matches(matches_data):
    """随机生成比分并结算"""
    scores_list = []
    for md in matches_data:
        match = md['match']
        # 随机比分 0-4球
        home_score = random.randint(0, 4)
        away_score = random.randint(0, 4)
        match.status = 'settled'
        match.scores_home = home_score
        match.scores_away = away_score
        match.updated_at = datetime.utcnow()
        scores_list.append((home_score, away_score))

    db.session.commit()

    # 逐场结算
    from services.settlement import calculate_settlement
    results = []
    for i, md in enumerate(matches_data):
        match = md['match']
        settlement = calculate_settlement(match.id)
        home_score, away_score = scores_list[i]

        # 更新每笔下注状态 + 用户金币
        for detail in settlement['bets_detail']:
            bet = Bet.query.get(detail['bet_id'])
            bet.status = detail['result']
            bet.win_amount = detail['win_amount']
            bet.settled_at = datetime.utcnow()

            # 赢了的加金币
            if detail['result'] in ('won', 'push') and detail['win_amount'] > 0:
                user = UserAccount.query.get(detail['user_id'])
                user.coin_balance += detail['win_amount']

        results.append({
            'match': f"{md['home_cn']} vs {md['away_cn']} [{md['league_cn']}]",
            'score': f"{home_score}-{away_score}",
            'total_bets': settlement['total_bets'],
            'won': sum(1 for d in settlement['bets_detail'] if d['result'] == 'won'),
            'lost': sum(1 for d in settlement['bets_detail'] if d['result'] == 'lost'),
            'push': sum(1 for d in settlement['bets_detail'] if d['result'] == 'push'),
            'payout': settlement['total_payout'],
        })
        md['score'] = f"{home_score}-{away_score}"

    db.session.commit()
    return results


def verify_round(round_num, matches_data, initial_balance):
    """验证数据一致性"""
    errors = []
    user = UserAccount.query.filter_by(username='test001').first()

    # 1. 检查所有下注状态都已结算
    pending = Bet.query.filter_by(status='pending').count()
    if pending > 0:
        errors.append(f"仍有{pending}笔未结算下注")

    # 2. 检查下注金额+余额+赢取=初始余额
    total_bet = sum(b.bet_amount for b in Bet.query.all())
    total_won = sum(b.win_amount for b in Bet.query.filter(Bet.status.in_(['won', 'push'])).all())
    expected_balance = initial_balance - total_bet + total_won
    if user and user.coin_balance != expected_balance:
        errors.append(f"金币不一致: 实际={user.coin_balance}, 预期={expected_balance}, 下注={total_bet}, 赢取={total_won}")

    # 3. 检查每笔won的bet都有对应的赢取
    won_bets = Bet.query.filter_by(status='won').all()
    for b in won_bets:
        if b.win_amount <= 0:
            errors.append(f"Bet#{b.id} won但win_amount={b.win_amount}")

    # 4. 检查所有match状态为settled
    unsettled = Match.query.filter(Match.status != 'settled').count()
    if unsettled > 0:
        errors.append(f"仍有{unsettled}场比赛未settled")

    return errors


def run_test():
    """运行20轮测试"""
    print("=" * 70)
    print("  bet365cn E2E 自动化测试 — 20轮全流程")
    print("=" * 70)
    print(f"  测试账号: test001  每注: {BET_AMOUNT}金币  每场: 9注")
    print(f"  每轮: 5场×9注=45注  每轮下注总额: {5 * 9 * BET_AMOUNT}金币")
    print("=" * 70)

    all_results = []
    total_errors = 0
    start_time = time.time()

    for r in range(1, ROUNDS + 1):
        round_start = time.time()
        errors = []

        with app.app_context():
            try:
                # Step 1: 清空
                clear_test_data()
                initial_balance = UserAccount.query.filter_by(username='test001').first().coin_balance

                # Step 2: 创建比赛+赔率
                matches_data = create_matches()
                create_odds(matches_data)

                # Step 3: 下注
                total_bets = place_bets(matches_data)
                after_bet_balance = UserAccount.query.filter_by(username='test001').first().coin_balance

                # Step 4: 结算
                settle_result = settle_matches(matches_data)

                # Step 5: 验证
                final_balance = UserAccount.query.filter_by(username='test001').first().coin_balance
                errors = verify_round(r, matches_data, initial_balance)

                round_time = time.time() - round_start
                won_total = sum(s['won'] for s in settle_result)
                lost_total = sum(s['lost'] for s in settle_result)
                payout_total = sum(s['payout'] for s in settle_result)

                status = "✅ PASS" if not errors else "❌ FAIL"
                print(f"\n  第{r:2d}轮 {status} ({round_time:.1f}s)")
                print(f"    初始金币: {initial_balance} → 下注后: {after_bet_balance} → 结算后: {final_balance}")
                print(f"    下注: {total_bets}注  赢: {won_total}  输: {lost_total}  赔付: {payout_total}")

                for s in settle_result:
                    print(f"    {s['match']} {s['score']} [赢{s['won']}/输{s['lost']}/走水{s['push']}] 赔付{s['payout']}")

                if errors:
                    total_errors += len(errors)
                    for e in errors:
                        print(f"    ❌ {e}")

                all_results.append({
                    'round': r, 'status': 'PASS' if not errors else 'FAIL',
                    'initial': initial_balance, 'after_bet': after_bet_balance,
                    'final': final_balance, 'errors': errors,
                    'matches': [{'name': s['match'], 'score': s['score'],
                                 'won': s['won'], 'lost': s['lost'], 'payout': s['payout']}
                                for s in settle_result],
                })

            except Exception as e:
                print(f"\n  第{r:2d}轮 ❌ EXCEPTION: {e}")
                import traceback
                traceback.print_exc()
                all_results.append({'round': r, 'status': 'ERROR', 'error': str(e)})
                total_errors += 1

    # ============================================================
    # 汇总报告
    # ============================================================
    total_time = time.time() - start_time
    passed = sum(1 for r in all_results if r['status'] == 'PASS')
    failed = sum(1 for r in all_results if r['status'] != 'PASS')

    print(f"\n{'=' * 70}")
    print(f"  测试完成: {passed}/{ROUNDS} 通过, {failed} 失败, {total_errors} 个错误")
    print(f"  总耗时: {total_time:.0f}s  平均: {total_time/ROUNDS:.1f}s/轮")
    print(f"{'=' * 70}")

    # 保存详细报告
    report = {
        'test_time': datetime.utcnow().isoformat(),
        'rounds': ROUNDS, 'passed': passed, 'failed': failed,
        'total_errors': total_errors, 'duration_seconds': total_time,
        'config': {'bet_amount': BET_AMOUNT, 'matches_per_round': 5, 'bets_per_match': 9},
        'results': all_results,
    }

    report_path = '/mnt/c/Users/admin/Desktop/bet365cn-测试报告.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  详细报告: {report_path}")

    return passed == ROUNDS


if __name__ == '__main__':
    success = run_test()
    sys.exit(0 if success else 1)
