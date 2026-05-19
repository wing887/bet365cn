# bet365cn — 管理员管理 API（仅超管）
from flask import Blueprint, request, jsonify
from models import db, AdminAccount, OperationLog
from auth import super_admin_required, hash_password

admins_bp = Blueprint('admin_admins', __name__)


@admins_bp.route('/api/admin/admins', methods=['GET'])
@super_admin_required
def list_admins():
    """管理员列表"""
    admins = AdminAccount.query.order_by(AdminAccount.created_at.desc()).all()
    return jsonify({'admins': [{
        'id': a.id, 'username': a.username, 'role': a.role,
        'created_at': a.created_at.isoformat() if a.created_at else None,
    } for a in admins]})


@admins_bp.route('/api/admin/admins', methods=['POST'])
@super_admin_required
def create_admin():
    """创建管理员"""
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': '请填写账号和密码'}), 400

    if AdminAccount.query.filter_by(username=username).first():
        return jsonify({'error': '管理员账号已存在'}), 409

    admin = AdminAccount(
        username=username,
        password_hash=hash_password(password),
        role='admin',
        created_by=request.current_user_id,
    )
    db.session.add(admin)

    log = OperationLog(
        admin_id=request.current_user_id,
        action='创建管理员',
        target_type='admin',
        target_id=admin.id,
        detail={'username': username},
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({'success': True, 'admin': {'id': admin.id, 'username': username}})


@admins_bp.route('/api/admin/admins/<int:admin_id>', methods=['DELETE'])
@super_admin_required
def delete_admin(admin_id):
    """删除管理员（不可删除自己或超管）"""
    admin = AdminAccount.query.get(admin_id)
    if not admin:
        return jsonify({'error': '管理员不存在'}), 404

    if admin.role == 'super_admin':
        return jsonify({'error': '不能删除超级管理员'}), 403

    if admin.id == request.current_user_id:
        return jsonify({'error': '不能删除自己'}), 403

    log = OperationLog(
        admin_id=request.current_user_id,
        action='删除管理员',
        target_type='admin',
        target_id=admin_id,
        detail={'username': admin.username},
    )
    db.session.add(log)
    db.session.delete(admin)
    db.session.commit()

    return jsonify({'success': True})
