# bet365cn Backend — JWT 三级认证体系
import jwt
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Tuple
from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash

# 角色层级
ROLE_SUPER_ADMIN = 'super_admin'
ROLE_ADMIN = 'admin'
ROLE_AGENT = 'agent'

ROLE_HIERARCHY = {ROLE_SUPER_ADMIN: 3, ROLE_ADMIN: 2, ROLE_AGENT: 1}


def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码（自动加盐）"""
    return generate_password_hash(password)


def _sha256_hash(password: str) -> str:
    """旧版 SHA256 哈希（仅用于兼容迁移）"""
    return 'sha256:' + hashlib.sha256(password.encode()).hexdigest()


def check_password(password: str, password_hash: str) -> str | bool:
    """验证密码，返回 True/False；若成功但为旧格式 SHA256，返回新 bcrypt hash"""
    # werkzeug 新格式（scrypt: 或 bcrypt $2b$/$2a$）
    if password_hash.startswith('scrypt:') or password_hash.startswith('$2'):
        return check_password_hash(password_hash, password)
    # 旧格式 SHA256（纯 hex 或带 sha256: 前缀）
    sha256_raw = password_hash.replace('sha256:', '')
    expected = hashlib.sha256(password.encode()).hexdigest()
    if sha256_raw == expected:
        return generate_password_hash(password)  # 返回新 hash 供升级
    return False


def create_token(user_id: int, role: str, is_admin: bool = False) -> dict:
    """生成 JWT token"""
    exp = datetime.utcnow() + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
    payload = {
        'sub': str(user_id),
        'role': role,
        'is_admin': is_admin,
        'exp': exp.timestamp(),
        'iat': datetime.utcnow().timestamp(),
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return {'access_token': token, 'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES']}


def decode_token(token: str) -> dict:
    """解码 JWT token"""
    return jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])


def is_token_blacklisted(token: str) -> bool:
    """检查 token 是否在黑名单中"""
    from models import TokenBlacklist
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    blacklisted = TokenBlacklist.query.filter_by(token_hash=token_hash).first()
    if blacklisted:
        # 自动清理过期记录
        now = datetime.utcnow()
        if blacklisted.expires_at < now:
            from models import db
            db.session.delete(blacklisted)
            db.session.commit()
            return False
        return True
    return False


def blacklist_token(token: str, expires_at: datetime):
    """将 token 加入黑名单"""
    from models import db, TokenBlacklist
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if not TokenBlacklist.query.filter_by(token_hash=token_hash).first():
        db.session.add(TokenBlacklist(
            token_hash=token_hash,
            expires_at=expires_at,
        ))
        db.session.commit()


def get_client_ip() -> str:
    """获取客户端真实 IP"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    return request.remote_addr or '127.0.0.1'


# ============================================================
# 权限辅助函数
# ============================================================

def _check_disabled(admin) -> Optional[Tuple]:
    """检查管理员是否被封禁，返回 (error, status_code) 或 None"""
    if admin.status == 'disabled':
        return jsonify({'error': '该账号已被封禁'}), 403
    return None


def can_manage_user(admin, target_user) -> bool:
    """
    检查管理员是否有权管理目标用户。
    super_admin: 可管理所有用户
    admin: 可管理代理和用户（但不能管理其他管理员）
    agent: 只能管理自己创建的用户
    """
    if admin.role == ROLE_SUPER_ADMIN:
        return True
    if admin.role == ROLE_ADMIN:
        # 管理不能操作超管账号
        return True  # admin 可以管理所有用户
    if admin.role == ROLE_AGENT:
        return target_user.created_by_admin_id == admin.id
    return False


def can_view_user(admin, target_user) -> bool:
    """
    检查管理员是否有权查看目标用户。
    super_admin: 查看所有
    admin: 查看所有
    agent: 只看自己创建的
    """
    if admin.role in (ROLE_SUPER_ADMIN, ROLE_ADMIN):
        return True
    if admin.role == ROLE_AGENT:
        return target_user.created_by_admin_id == admin.id
    return False


def can_create_role(admin, target_role: str) -> bool:
    """
    检查管理员是否有权创建指定角色。
    super_admin: 可创建 admin/agent/user
    admin: 可创建 agent/user
    agent: 只能创建 user
    """
    hierarchy = {
        ROLE_SUPER_ADMIN: [ROLE_ADMIN, ROLE_AGENT, 'user'],
        ROLE_ADMIN: [ROLE_AGENT, 'user'],
        ROLE_AGENT: ['user'],
    }
    return target_role in hierarchy.get(admin.role, [])


def can_ban_admin(admin, target_admin) -> bool:
    """
    检查能否封禁目标管理员。
    super_admin: 可封禁 admin 和 agent
    admin: 可封禁 agent
    agent: 不能封禁管理员
    """
    if admin.role == ROLE_SUPER_ADMIN and target_admin.role != ROLE_SUPER_ADMIN:
        return True
    if admin.role == ROLE_ADMIN and target_admin.role == ROLE_AGENT:
        return True
    return False


def can_view_log(admin, log) -> bool:
    """
    检查管理员是否有权查看操作日志。
    super_admin: 全部
    admin: 全部
    agent: 只看自己做操作人的
    """
    if admin.role in (ROLE_SUPER_ADMIN, ROLE_ADMIN):
        return True
    if admin.role == ROLE_AGENT:
        return log.admin_id == admin.id
    return False


# ============================================================
# 智能搜索工具
# ============================================================

def smart_search(field, query):
    """大小写不敏感 + 多词搜索（空格分隔，AND 逻辑）。
    
    使用 ilike 替代 contains，解决 PostgreSQL 区分大小写问题。
    多词场景下每个词都必须匹配（如 "zhang 三" 要求同时含 zhang 和 三）。
    """
    from sqlalchemy import and_, true
    terms = query.strip().split()
    filters = [field.ilike(f'%{t}%') for t in terms if t]
    return and_(*filters) if filters else true()


def can_modify_coins(admin, target_user, amount: int) -> tuple:
    """
    检查管理员是否有权对目标用户进行金币操作。
    返回 (allowed: bool, error_msg: str | None)
    
    super_admin: +/- 任何人（不消耗自身余额）
    admin: +/- 代理和用户（不消耗自身余额）
    agent: +/- 自己创建的用户（加=代理出，扣=代理收）
    """
    if admin.role == ROLE_SUPER_ADMIN:
        return True, None
    if admin.role == ROLE_ADMIN:
        if not can_manage_user(admin, target_user):
            return False, '无权操作该用户'
        return True, None
    if admin.role == ROLE_AGENT:
        if target_user.created_by_admin_id != admin.id:
            return False, '无权操作该用户'
        if amount > 0:
            # 加金币：代理出
            if admin.coin_balance < amount:
                return False, f'余额不足（当前 {admin.coin_balance}，需要 {amount}）'
        # amount < 0 扣金币：代理收，只需检查用户余额（在 coins.py 里检查）
        return True, None
    return False, '无权操作'


# ============================================================
# 登录失败限流（每个账号 5次/15分钟）
# ============================================================
from collections import defaultdict

_login_attempts = defaultdict(list)  # {username: [attempt_times]}
_MAX_ATTEMPTS = 5
_ATTEMPT_WINDOW = 900  # 15 分钟


def check_login_rate_limit(username: str) -> bool:
    """检查登录频率限制，返回 True 表示允许登录"""
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=_ATTEMPT_WINDOW)
    attempts = [t for t in _login_attempts.get(username, []) if t > window_start]
    _login_attempts[username] = attempts
    if len(attempts) >= _MAX_ATTEMPTS:
        return False
    return True


def record_login_failure(username: str):
    """记录一次登录失败"""
    _login_attempts[username].append(datetime.utcnow())


def clear_login_attempts(username: str):
    """登录成功后清除失败记录"""
    _login_attempts.pop(username, None)


# ============================================================
# 装饰器
# ============================================================

def login_required(f):
    """用户登录验证"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from models import UserAccount

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': '未登录'}), 401
        try:
            token = auth_header[7:]
            payload = decode_token(token)
            if payload.get('is_admin'):
                return jsonify({'error': '请使用用户账号'}), 403

            user = UserAccount.query.get(int(payload['sub']))
            if not user:
                return jsonify({'error': '账号不存在'}), 401
            if user.status != 'active':
                return jsonify({'error': '账号已被封禁'}), 403

            request.current_user_id = int(payload['sub'])
            request.current_user_role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '登录已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的登录凭证'}), 401
        return f(*args, **kwargs)
    return decorated


def _admin_auth(f, allowed_roles: list):
    """
    通用管理员认证装饰器。
    allowed_roles: 允许的角色列表
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        from models import AdminAccount

        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': '未登录'}), 401
        try:
            token = auth_header[7:]
            payload = decode_token(token)
            if is_token_blacklisted(token):
                return jsonify({'error': '登录已失效，请重新登录'}), 401
            if not payload.get('is_admin'):
                return jsonify({'error': '需要管理员权限'}), 403
            if payload.get('role') not in allowed_roles:
                return jsonify({'error': '权限不足'}), 403

            admin = AdminAccount.query.get(int(payload['sub']))
            if not admin:
                return jsonify({'error': '账号不存在'}), 401
            disabled_check = _check_disabled(admin)
            if disabled_check:
                return disabled_check

            request.current_user_id = admin.id
            request.current_user_role = admin.role
            request.current_admin = admin
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '登录已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的登录凭证'}), 401
        return f(*args, **kwargs)
    return decorated


def agent_or_above(f):
    """三级管理员验证（超管、管理、代理均可）"""
    return _admin_auth(f, [ROLE_SUPER_ADMIN, ROLE_ADMIN, ROLE_AGENT])


def admin_or_above(f):
    """二级管理员验证（超管、管理）"""
    return _admin_auth(f, [ROLE_SUPER_ADMIN, ROLE_ADMIN])


def super_admin_required(f):
    """超管验证"""
    return _admin_auth(f, [ROLE_SUPER_ADMIN])


def agent_only(f):
    """代理验证（仅代理可访问，超管/管理不可）"""
    return _admin_auth(f, [ROLE_AGENT])
