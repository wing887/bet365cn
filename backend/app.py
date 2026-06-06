# bet365cn Backend — Flask 应用入口
from flask import Flask, jsonify
from flask_cors import CORS
from config import DevelopmentConfig, ProductionConfig
from models import db
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)


def create_app(config=None):
    app = Flask(__name__)

    if config is None:
        env = os.environ.get('FLASK_ENV', 'development')
        config = DevelopmentConfig if env == 'development' else ProductionConfig

    app.config.from_object(config)

    # SQLAlchemy
    db.init_app(app)

    # CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    with app.app_context():
        db.create_all()
        
        # SQLite WAL 模式（允许读写并发）
        from sqlalchemy import text
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            db.session.execute(text('PRAGMA journal_mode=WAL'))
            db.session.commit()

        # ===== 基础路由 =====
        @app.route('/')
        def index():
            return {'status': 'ok', 'app': 'bet365cn', 'version': '1.0.0'}

        @app.route('/api/health')
        def health():
            return {'status': 'healthy'}

        # ===== 注册蓝图 =====
        from routes.user_auth import user_auth_bp
        from routes.matches import matches_bp
        from routes.bets import bets_bp
        from routes.user_center import user_center_bp
        
        app.register_blueprint(user_auth_bp)
        app.register_blueprint(matches_bp)
        app.register_blueprint(bets_bp)
        app.register_blueprint(user_center_bp)

        # 管理端蓝图
        from admin.admin_auth import admin_auth_bp
        from admin.users import users_bp
        from admin.coins import coins_bp
        from admin.settlements import settlements_bp
        from admin.admins import admins_bp
        from admin.logs import logs_bp
        from admin.agents import agents_bp
        from admin.customer_stats import customer_stats_bp
        from admin.config import config_bp
        from admin.matches import matches_bp as admin_matches_bp
        from admin.odds import odds_bp as admin_odds_bp
        from admin.bets import bets_bp as admin_bets_bp

        app.register_blueprint(admin_auth_bp)
        app.register_blueprint(users_bp)
        app.register_blueprint(coins_bp)
        app.register_blueprint(settlements_bp)
        app.register_blueprint(admins_bp)
        app.register_blueprint(logs_bp)
        app.register_blueprint(agents_bp)
        app.register_blueprint(customer_stats_bp)
        app.register_blueprint(config_bp)
        app.register_blueprint(admin_matches_bp)
        app.register_blueprint(admin_odds_bp)
        app.register_blueprint(admin_bets_bp)

        # ===== 手动触发同步（后台执行，避免超时）=====
        import threading
        
        @app.route('/api/sync/matches')
        def api_sync_matches():
            def _run():
                with app.app_context():
                    try:
                        from services.sync_service import sync_matches
                        sync_matches()
                        logger.info('sync_matches 后台完成')
                    except Exception as e:
                        logger.error(f'sync_matches 失败: {e}')
            threading.Thread(target=_run, daemon=True).start()
            return {'status': 'ok', 'action': 'sync_matches', 'note': 'running in background'}

        @app.route('/api/sync/odds')
        def api_sync_odds():
            def _run():
                with app.app_context():
                    try:
                        from services.sync_service import sync_odds
                        sync_odds()
                        logger.info('sync_odds 后台完成')
                    except Exception as e:
                        logger.error(f'sync_odds 失败: {e}')
            threading.Thread(target=_run, daemon=True).start()
            return {'status': 'ok', 'action': 'sync_odds', 'note': 'running in background'}

        @app.route('/api/sync/status')
        def api_sync_status():
            """查询同步进度"""
            return {
                'matches_count': __import__('models').Match.query.count(),
                'odds_count': __import__('models').Odds.query.count(),
            }

        # ===== 启动定时任务 =====
        try:
            from scheduler import create_scheduler
            app.scheduler = create_scheduler(app)
            logger.info('定时任务已启动')
        except Exception as e:
            logger.warning(f'定时任务启动失败: {e}')
            app.scheduler = None

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)
