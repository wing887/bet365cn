# bet365cn — 操作日志 + 统计 API
from flask import Blueprint, request, jsonify
from models import db, OperationLog, CoinTransaction, AdminAccount
from auth import agent_or_above, super_admin_required, get_client_ip, ROLE_AGENT
from datetime import datetime

logs_bp = Blueprint('admin_logs', __name__)


@logs_bp.route('/api/admin/logs', methods=['GET'])
@agent_or_above
def list_logs():
    """操作日志列表（按权限过滤）
    super_admin / admin → 全部
    agent → 只看自己操作的日志
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)
    admin = request.current_admin

    query = OperationLog.query.order_by(OperationLog.created_at.desc())

    # 代理只能看自己的操作
    if admin.role == ROLE_AGENT:
        query = query.filter_by(admin_id=admin.id)

    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()

    # 预加载操作人名称
    admin_ids = set(l.admin_id for l in logs)
    admin_map = {}
    for aid in admin_ids:
        a = AdminAccount.query.get(aid)
        admin_map[aid] = a.username if a else '?'

    result = []
    for l in logs:
        result.append({
            'id': l.id,
            'admin_name': admin_map.get(l.admin_id, '?'),
            'action': l.action,
            'target_type': l.target_type,
            'target_id': l.target_id,
            'detail': l.detail,
            'ip_address': l.ip_address,
            'created_at': l.created_at.isoformat() if l.created_at else None,
        })

    return jsonify({'logs': result, 'total': total, 'page': page})


@logs_bp.route('/api/admin/stats', methods=['GET'])
@agent_or_above
def stats():
    """金币统计（按日期范围）
    super_admin / admin → 全部操作
    agent → 只看自己的操作
    """
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    admin = request.current_admin

    query = CoinTransaction.query.filter(
        CoinTransaction.type.in_(['admin_add', 'admin_deduct'])
    )

    # 代理只看自己的操作
    if admin.role == ROLE_AGENT:
        query = query.filter_by(operator_id=admin.id)

    if date_from:
        try:
            d = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(CoinTransaction.created_at >= d)
        except ValueError:
            pass

    if date_to:
        try:
            d = datetime.strptime(date_to, '%Y-%m-%d')
            d = d.replace(hour=23, minute=59, second=59)
            query = query.filter(CoinTransaction.created_at <= d)
        except ValueError:
            pass

    txs = query.all()

    total_add = sum(t.amount for t in txs if t.amount > 0)
    total_deduct = sum(abs(t.amount) for t in txs if t.amount < 0)

    # 按操作人分组
    by_admin = {}
    for t in txs:
        if t.operator_id not in by_admin:
            operator = AdminAccount.query.get(t.operator_id)
            by_admin[t.operator_id] = {
                'admin_name': operator.username if operator else '?',
                'add': 0, 'deduct': 0,
            }
        if t.amount > 0:
            by_admin[t.operator_id]['add'] += t.amount
        else:
            by_admin[t.operator_id]['deduct'] += abs(t.amount)

    return jsonify({
        'total_add': total_add,
        'total_deduct': total_deduct,
        'net': total_add - total_deduct,
        'total_ops': len(txs),
        'by_admin': [{'admin_id': k, **v} for k, v in by_admin.items()],
    })
