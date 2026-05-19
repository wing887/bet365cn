# bet365cn — 操作日志 + 统计 API（仅超管）
from flask import Blueprint, request, jsonify
from models import db, OperationLog, CoinTransaction
from auth import super_admin_required
from datetime import datetime
from sqlalchemy import func

logs_bp = Blueprint('admin_logs', __name__)


@logs_bp.route('/api/admin/logs', methods=['GET'])
@super_admin_required
def list_logs():
    """操作日志列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)

    query = OperationLog.query.order_by(OperationLog.created_at.desc())
    total = query.count()
    logs = query.offset((page - 1) * per_page).limit(per_page).all()

    from models import AdminAccount
    admin_map = {}
    
    result = []
    for l in logs:
        if l.admin_id not in admin_map:
            a = AdminAccount.query.get(l.admin_id)
            admin_map[l.admin_id] = a.username if a else '?'
        
        result.append({
            'id': l.id,
            'admin_name': admin_map[l.admin_id],
            'action': l.action,
            'target_type': l.target_type,
            'target_id': l.target_id,
            'detail': l.detail,
            'created_at': l.created_at.isoformat() if l.created_at else None,
        })

    return jsonify({'logs': result, 'total': total, 'page': page})


@logs_bp.route('/api/admin/stats', methods=['GET'])
@super_admin_required
def stats():
    """金币统计（按日期范围）"""
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    query = CoinTransaction.query.filter(
        CoinTransaction.type.in_(['admin_add', 'admin_deduct'])
    )

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
    from models import AdminAccount
    by_admin = {}
    for t in txs:
        if t.operator_id not in by_admin:
            admin = AdminAccount.query.get(t.operator_id)
            by_admin[t.operator_id] = {'admin_name': admin.username if admin else '?', 'add': 0, 'deduct': 0}
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
