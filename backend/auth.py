# bet365cn Backend — JWT 双认证体系
import jwt
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def check_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def create_token(user_id: int, role: str, is_admin: bool = False) -> dict:
    """生成 JWT token"""
    exp = datetime.utcnow() + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
    payload = {
        'sub': user_id,
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


# ============================================================
# 装饰器
# ============================================================

def login_required(f):
    """用户登录验证"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': '未登录'}), 401
        try:
            token = auth_header[7:]
            payload = decode_token(token)
            if payload.get('is_admin'):
                return jsonify({'error': '请使用用户账号'}), 403
            request.current_user_id = payload['sub']
            request.current_user_role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '登录已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的登录凭证'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """管理员登录验证（超管 + 普管）"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': '未登录'}), 401
        try:
            token = auth_header[7:]
            payload = decode_token(token)
            if not payload.get('is_admin'):
                return jsonify({'error': '需要管理员权限'}), 403
            request.current_user_id = payload['sub']
            request.current_user_role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '登录已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的登录凭证'}), 401
        return f(*args, **kwargs)
    return decorated


def super_admin_required(f):
    """超管验证"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': '未登录'}), 401
        try:
            token = auth_header[7:]
            payload = decode_token(token)
            if not payload.get('is_admin') or payload.get('role') != 'super_admin':
                return jsonify({'error': '需要超级管理员权限'}), 403
            request.current_user_id = payload['sub']
            request.current_user_role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '登录已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的登录凭证'}), 401
        return f(*args, **kwargs)
    return decorated
