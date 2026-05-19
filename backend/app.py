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

        # ===== 手动触发同步（调试用）=====
        @app.route('/api/sync/matches')
        def api_sync_matches():
            try:
                from services.sync_service import sync_matches
                sync_matches()
                return {'status': 'ok', 'action': 'sync_matches'}
            except Exception as e:
                logger.error(f'sync_matches 失败: {e}')
                return {'status': 'error', 'message': str(e)}, 500

        @app.route('/api/sync/odds')
        def api_sync_odds():
            try:
                from services.sync_service import sync_odds
                sync_odds()
                return {'status': 'ok', 'action': 'sync_odds'}
            except Exception as e:
                logger.error(f'sync_odds 失败: {e}')
                return {'status': 'error', 'message': str(e)}, 500

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
