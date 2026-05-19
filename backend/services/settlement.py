# bet365cn — 结算计算引擎
from models import Bet, Match, Odds, UserAccount


def calculate_settlement(match_id: int) -> dict:
    """
    计算一场比赛的结算结果
    返回：每笔下注的输赢判定 + 汇总
    """
    match = Match.query.get(match_id)
    if not match or match.status != 'settled':
        return {'total_bets': 0, 'total_users': 0, 'total_payout': 0,
                'total_win_users': 0, 'bets_detail': []}

    home = match.scores_home
    away = match.scores_away
    total = home + away

    bets = Bet.query.filter_by(match_id=match_id, status='pending').all()
    if not bets:
        return {'total_bets': 0, 'total_users': 0, 'total_payout': 0,
                'total_win_users': 0, 'bets_detail': []}

    users = set()
    total_payout = 0
    total_win_users = set()
    details = []

    for bet in bets:
        result, win_amount = _settle_one(bet, home, away, total)
        users.add(bet.user_id)
        if result == 'won':
            total_payout += win_amount
            total_win_users.add(bet.user_id)

        details.append({
            'bet_id': bet.id,
            'user_id': bet.user_id,
            'market_type': bet.market_type,
            'selection': bet.selection,
            'odds_value': bet.odds_value,
            'bet_amount': bet.bet_amount,
            'result': result,
            'win_amount': win_amount,
        })

    return {
        'total_bets': len(bets),
        'total_users': len(users),
        'total_payout': total_payout,
        'total_win_users': len(total_win_users),
        'bets_detail': details,
    }


def _settle_one(bet, home: int, away: int, total: int) -> tuple:
    """判定单笔下注输赢，返回 (result, win_amount)"""
    result = 'lost'
    win_amount = 0

    if bet.market_type == 'ML':
        winner = 'home' if home > away else ('away' if away > home else 'draw')
        if bet.selection == winner:
            result = 'won'

    elif bet.market_type == 'Spread':
        # 获取盘口
        odds = Odds.query.filter_by(match_id=bet.match_id, bookmaker='Bet365',
                                    market_type='Spread').first()
        hdp = odds.odds_data.get('hdp', 0) if odds else 0
        adjusted = home - hdp  # hdp>0 主队让球
        if adjusted == away:
            result = 'push'
        elif (bet.selection == 'home' and adjusted > away) or \
             (bet.selection == 'away' and adjusted < away):
            result = 'won'

    elif bet.market_type == 'Totals':
        odds = Odds.query.filter_by(match_id=bet.match_id, bookmaker='Bet365',
                                    market_type='Totals').first()
        hdp = odds.odds_data.get('hdp', 2.5) if odds else 2.5
        if total == hdp:
            result = 'push'
        elif (bet.selection == 'over' and total > hdp) or \
             (bet.selection == 'under' and total < hdp):
            result = 'won'

    elif bet.market_type == 'CS':
        actual = f'{home}-{away}'
        if bet.selection == actual:
            result = 'won'

    # 计算赢取金额
    if result == 'won':
        win_amount = round(bet.bet_amount * bet.odds_value)
    elif result == 'push':
        win_amount = bet.bet_amount  # 退回本金

    return result, win_amount
