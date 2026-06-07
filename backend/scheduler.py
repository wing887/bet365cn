# bet365cn — 定时任务调度器
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import redis

logger = logging.getLogger(__name__)

# 尝试 Redis 连接（可选，开发环境没有 Redis 也能跑）
try:
    redis_client = redis.Redis.from_url('redis://localhost:6379/0', socket_connect_timeout=2)
    redis_client.ping()
    HAS_REDIS = True
    logger.info('Redis 已连接，启用分布式锁')
except Exception:
    redis_client = None
    HAS_REDIS = False
    logger.info('Redis 未连接，定时任务无分布式锁（仅单 worker 安全）')


def _acquire_lock(lock_name: str, ttl: int = 600) -> bool:
    """获取 Redis 分布式锁"""
    if not HAS_REDIS:
        return True
    return redis_client.set(f'lock:{lock_name}', '1', nx=True, ex=ttl)


def _release_lock(lock_name: str):
    """释放 Redis 分布式锁"""
    if not HAS_REDIS:
        return
    redis_client.delete(f'lock:{lock_name}')


def create_scheduler(app):
    """创建定时任务调度器"""
    scheduler = BackgroundScheduler()

    def fetch_matches_job():
        """定时拉取比赛数据"""
        if not _acquire_lock('fetch_matches', ttl=600):
            return
        try:
            with app.app_context():
                from services.sync_service import sync_matches
                sync_matches()
        except Exception as e:
            logger.error(f'fetch_matches 失败: {e}')
        finally:
            _release_lock('fetch_matches')

    def fetch_odds_job():
        """定时拉取赔率数据"""
        if not _acquire_lock('fetch_odds', ttl=600):
            return
        try:
            with app.app_context():
                from services.sync_service import sync_odds
                sync_odds()
        except Exception as e:
            logger.error(f'fetch_odds 失败: {e}')
        finally:
            _release_lock('fetch_odds')

    def check_settled_job():
        """定时检测已结算比赛"""
        if not _acquire_lock('check_settled', ttl=600):
            return
        try:
            with app.app_context():
                from services.sync_service import check_settled
                check_settled()
        except Exception as e:
            logger.error(f'check_settled 失败: {e}')
        finally:
            _release_lock('check_settled')

    # 注册定时任务（100次/小时限额：2+60+4=66次，留有余量）
    scheduler.add_job(fetch_matches_job, 'interval', minutes=30, id='fetch_matches')
    scheduler.add_job(fetch_odds_job, 'interval', minutes=30, id='fetch_odds')  # ~30场×2次/时=60
    scheduler.add_job(check_settled_job, 'interval', minutes=15, id='check_settled')
    
    # 滚球实时赔率同步（30秒/次，~120次/h，需关注 Key 配额）
    def live_poll_job():
        if not _acquire_lock('live_poll', ttl=60):
            return
        try:
            with app.app_context():
                from services.live_poller import live_poll
                live_poll()
        except Exception as e:
            logger.error(f'live_poll 失败: {e}')
        finally:
            _release_lock('live_poll')
    
    scheduler.add_job(live_poll_job, 'interval', seconds=app.config.get('LIVE_POLL_INTERVAL', 30), id='live_poll')

    scheduler.start()
    logger.info(f'APScheduler 已启动（4个定时任务，含滚球 {app.config.get("LIVE_POLL_INTERVAL", 30)}s）')
    return scheduler
