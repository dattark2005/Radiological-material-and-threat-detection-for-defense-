from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from models.database import SystemLog, User, mongo
from utils.logger import log_system_event

logs_bp = Blueprint('logs', __name__)

@logs_bp.route('/system', methods=['GET'])
@jwt_required()
def get_system_logs():
    """Get system logs with filtering and pagination."""
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        level = request.args.get('level')
        module = request.args.get('module')
        hours = request.args.get('hours', 24, type=int)
        
        # Limit per_page
        per_page = min(per_page, 200)
        
        # Build query
        query = SystemLog.query
        
        # Filter by time
        if hours > 0:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(SystemLog.timestamp >= cutoff_time)
        
        # Filter by log level
        if level:
            query = query.filter_by(level=level.upper())
        
        # Filter by module
        if module:
            query = query.filter_by(module=module)
        
        # Execute query with pagination
        logs = query.order_by(desc(SystemLog.timestamp)).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'logs': [log.to_dict() for log in logs.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': logs.total,
                'pages': logs.pages,
                'has_next': logs.has_next,
                'has_prev': logs.has_prev
            }
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'System logs retrieval error: {str(e)}', 'logs')
        return jsonify({'message': 'Failed to retrieve system logs'}), 500

@logs_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_log_statistics():
    """Get log statistics and trends."""
    try:
        hours = request.args.get('hours', 24, type=int)
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        from sqlalchemy import func
        
        # Get log level distribution
        level_distribution = db.session.query(
            SystemLog.level,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.timestamp >= cutoff_time
        ).group_by(SystemLog.level).all()
        
        # Get module distribution
        module_distribution = db.session.query(
            SystemLog.module,
            func.count(SystemLog.id).label('count')
        ).filter(
            SystemLog.timestamp >= cutoff_time,
            SystemLog.module.isnot(None)
        ).group_by(SystemLog.module).all()
        
        # Get hourly trends
        hourly_trends = db.session.query(
            func.date_trunc('hour', SystemLog.timestamp).label('hour'),
            func.count(SystemLog.id).label('count'),
            func.sum(func.case([(SystemLog.level == 'ERROR', 1)], else_=0)).label('errors')
        ).filter(
            SystemLog.timestamp >= cutoff_time
        ).group_by(
            func.date_trunc('hour', SystemLog.timestamp)
        ).order_by('hour').all()
        
        trends = []
        for hour, count, errors in hourly_trends:
            trends.append({
                'hour': hour.isoformat(),
                'total_logs': count,
                'error_count': errors or 0
            })
        
        return jsonify({
            'period_hours': hours,
            'level_distribution': {level: count for level, count in level_distribution},
            'module_distribution': {module: count for module, count in module_distribution},
            'hourly_trends': trends,
            'summary': {
                'total_logs': sum(count for _, count in level_distribution),
                'error_count': dict(level_distribution).get('ERROR', 0),
                'warning_count': dict(level_distribution).get('WARNING', 0)
            }
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Log statistics error: {str(e)}', 'logs')
        return jsonify({'message': 'Failed to get log statistics'}), 500

@logs_bp.route('/export', methods=['POST'])
@jwt_required()
def export_logs():
    """Export logs to file."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Get export parameters
        hours = data.get('hours', 24)
        level = data.get('level')
        module = data.get('module')
        format_type = data.get('format', 'json')  # json, csv
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Build query
        query = SystemLog.query.filter(SystemLog.timestamp >= cutoff_time)
        
        if level:
            query = query.filter_by(level=level.upper())
        
        if module:
            query = query.filter_by(module=module)
        
        logs = query.order_by(desc(SystemLog.timestamp)).limit(10000).all()  # Limit for performance
        
        if format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['Timestamp', 'Level', 'Message', 'Module', 'User ID', 'IP Address'])
            
            # Write data
            for log in logs:
                writer.writerow([
                    log.timestamp.isoformat() if log.timestamp else '',
                    log.level,
                    log.message,
                    log.module or '',
                    log.user_id or '',
                    log.ip_address or ''
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            log_system_event('INFO', f'Logs exported to CSV: {len(logs)} entries', 'logs', user_id)
            
            return jsonify({
                'format': 'csv',
                'content': csv_content,
                'count': len(logs)
            }), 200
        
        else:  # JSON format
            log_data = [log.to_dict() for log in logs]
            
            log_system_event('INFO', f'Logs exported to JSON: {len(logs)} entries', 'logs', user_id)
            
            return jsonify({
                'format': 'json',
                'logs': log_data,
                'count': len(logs)
            }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Log export error: {str(e)}', 'logs')
        return jsonify({'message': 'Failed to export logs'}), 500

@logs_bp.route('/clear', methods=['POST'])
@jwt_required()
def clear_logs():
    """Clear old logs (admin only)."""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        data = request.get_json()
        days = data.get('days', 30)  # Clear logs older than X days
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count logs to be deleted
        count = SystemLog.query.filter(SystemLog.timestamp < cutoff_date).count()
        
        # Delete old logs
        SystemLog.query.filter(SystemLog.timestamp < cutoff_date).delete()
        db.session.commit()
        
        log_system_event('INFO', f'Cleared {count} old log entries (older than {days} days)', 'logs', user_id)
        
        return jsonify({
            'message': f'Cleared {count} log entries',
            'cleared_count': count,
            'cutoff_date': cutoff_date.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        log_system_event('ERROR', f'Log clearing error: {str(e)}', 'logs')
        return jsonify({'message': 'Failed to clear logs'}), 500
