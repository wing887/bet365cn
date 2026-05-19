# bet365cn Backend — 数据库初始化
"""
初始化数据库：创建表 + 默认超管 + 种子数据
运行: python init_db.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from models import db, AdminAccount, TeamNameMap
from auth import hash_password


def init():
    app = create_app()
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✓ 数据库表已创建")

        # 创建默认超级管理员
        if not AdminAccount.query.filter_by(username='superadmin').first():
            admin = AdminAccount(
                username='superadmin',
                password_hash=hash_password('admin123'),
                role='super_admin',
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ 默认超管已创建: superadmin / admin123")

        # 导入五大联赛球队中文名（种子数据）
        seed_team_names()
        print("✓ 球队名映射已导入")

    print("\n数据库初始化完成！")


def seed_team_names():
    """导入五大联赛主要球队的中文名"""
    teams = {
        'England - Premier League': {
            'Manchester City': '曼城',
            'Arsenal': '阿森纳',
            'Liverpool': '利物浦',
            'Chelsea': '切尔西',
            'Manchester United': '曼联',
            'Tottenham Hotspur': '热刺',
            'Newcastle United': '纽卡斯尔联',
            'Aston Villa': '阿斯顿维拉',
            'Brighton & Hove Albion': '布莱顿',
            'West Ham United': '西汉姆联',
            'AFC Bournemouth': '伯恩茅斯',
            'Crystal Palace': '水晶宫',
            'Everton': '埃弗顿',
            'Fulham': '富勒姆',
            'Nottingham Forest': '诺丁汉森林',
            'Wolverhampton Wanderers': '狼队',
            'Brentford': '布伦特福德',
            'Leicester City': '莱斯特城',
            'Southampton': '南安普顿',
            'Ipswich Town': '伊普斯维奇',
        },
        'Germany - Bundesliga': {
            'Bayern Munich': '拜仁慕尼黑',
            'Borussia Dortmund': '多特蒙德',
            'RB Leipzig': '莱比锡红牛',
            'Bayer Leverkusen': '勒沃库森',
            'VfB Stuttgart': '斯图加特',
            'Eintracht Frankfurt': '法兰克福',
            'VfL Wolfsburg': '沃尔夫斯堡',
            'Borussia Mönchengladbach': '门兴格拉德巴赫',
            'SC Freiburg': '弗赖堡',
            'TSG Hoffenheim': '霍芬海姆',
            'FC Augsburg': '奥格斯堡',
            'Werder Bremen': '云达不莱梅',
            '1. FC Union Berlin': '柏林联合',
            'FSV Mainz 05': '美因茨',
        },
        'Spain - LaLiga': {
            'Real Madrid': '皇家马德里',
            'FC Barcelona': '巴塞罗那',
            'Atlético Madrid': '马德里竞技',
            'Sevilla FC': '塞维利亚',
            'Real Sociedad': '皇家社会',
            'Athletic Bilbao': '毕尔巴鄂竞技',
            'Real Betis': '皇家贝蒂斯',
            'Villarreal CF': '比利亚雷亚尔',
            'Valencia CF': '瓦伦西亚',
            'Celta Vigo': '塞尔塔',
            'RCD Mallorca': '马洛卡',
            'Getafe CF': '赫塔费',
            'Deportivo Alavés': '阿拉维斯',
            'CA Osasuna': '奥萨苏纳',
            'RCD Espanyol': '西班牙人',
            'Girona FC': '赫罗纳',
            'UD Las Palmas': '拉斯帕尔马斯',
            'Rayo Vallecano': '巴列卡诺',
        },
        'Italy - Serie A': {
            'Juventus': '尤文图斯',
            'Inter Milan': '国际米兰',
            'AC Milan': 'AC米兰',
            'Napoli': '那不勒斯',
            'AS Roma': '罗马',
            'Lazio': '拉齐奥',
            'Atalanta': '亚特兰大',
            'Fiorentina': '佛罗伦萨',
            'Bologna': '博洛尼亚',
            'Torino': '都灵',
            'Udinese': '乌迪内斯',
            'Genoa': '热那亚',
            'Cagliari': '卡利亚里',
            'Lecce': '莱切',
            'Monza': '蒙扎',
            'Parma': '帕尔马',
            'Como': '科莫',
            'Venezia': '威尼斯',
        },
        'France - Ligue 1': {
            'Paris Saint-Germain': '巴黎圣日耳曼',
            'Olympique Marseille': '马赛',
            'Olympique Lyonnais': '里昂',
            'AS Monaco': '摩纳哥',
            'Lille OSC': '里尔',
            'OGC Nice': '尼斯',
            'Stade Rennais': '雷恩',
            'RC Lens': '朗斯',
            'Stade de Reims': '兰斯',
            'Montpellier HSC': '蒙彼利埃',
            'Toulouse FC': '图卢兹',
            'Stade Brestois': '布雷斯特',
            'FC Nantes': '南特',
            'AJ Auxerre': '欧塞尔',
            'Le Havre AC': '勒阿弗尔',
            'RC Strasbourg': '斯特拉斯堡',
            'FC Lorient': '洛里昂',
            'FC Metz': '梅斯',
        },
    }

    count = 0
    for league, team_map in teams.items():
        for name_en, name_cn in team_map.items():
            existing = TeamNameMap.query.filter_by(
                league_name=league, name_en=name_en
            ).first()
            if not existing:
                t = TeamNameMap(league_name=league, name_en=name_en, name_cn=name_cn)
                db.session.add(t)
                count += 1
    db.session.commit()
    print(f"  导入 {count} 条球队映射")


if __name__ == '__main__':
    init()
