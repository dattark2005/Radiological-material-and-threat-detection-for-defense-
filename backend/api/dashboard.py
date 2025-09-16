from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from models.database import User, AnalysisSession, ThreatAssessment, SystemLog, mongo
from utils.logger import log_system_event

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        user_id = get_jwt_identity()
        
        # Total scans
        total_scans = mongo.db.analysis_sessions.count_documents({'status': 'completed'})
        
        # Threats detected (threat probability > 0.5)
        threats_detected = mongo.db.threat_assessments.count_documents(
            {'overall_threat_probability': {'$gt': 0.5}}
        )
        
        # Recent activity (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_scans = mongo.db.analysis_sessions.count_documents(
            {'start_time': {'$gte': yesterday}}
        )
        
        # System uptime (mock calculation)
        uptime_seconds = 86400  # 24 hours for demo
        
        # Current threat level
        latest_assessment = mongo.db.threat_assessments.find_one(
            {}, sort=[('assessment_time', -1)]
        )
        
        current_threat_level = 'clear'
        current_threat_probability = 0.0
        
        if latest_assessment:
            current_threat_level = latest_assessment.get('threat_level', 'clear')
            current_threat_probability = latest_assessment.get('overall_threat_probability', 0.0)
        
        # Active users
        active_users = mongo.db.users.count_documents({'is_active': True})
        
        # System health metrics
        system_health = {
            'database': 'healthy',
            'ml_models': 'healthy',
            'quantum_simulator': 'healthy',
            'file_storage': 'healthy'
        }
        
        return jsonify({
            'total_scans': total_scans,
            'threats_detected': threats_detected,
            'recent_scans': recent_scans,
            'uptime_seconds': uptime_seconds,
            'current_threat_level': current_threat_level,
            'current_threat_probability': current_threat_probability,
            'active_users': active_users,
            'system_health': system_health,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Dashboard stats error: {str(e)}', 'dashboard')
        return jsonify({'message': 'Failed to fetch dashboard stats'}), 500

@dashboard_bp.route('/recent-activity', methods=['GET'])
@jwt_required()
def get_recent_activity():
    """Get recent system activity."""
    try:
        # Get recent analysis sessions
        recent_sessions = list(mongo.db.analysis_sessions.find(
            {}, sort=[('start_time', -1)], limit=10
        ))
        
        # Get recent threat assessments
        recent_threats = list(mongo.db.threat_assessments.find(
            {}, sort=[('assessment_time', -1)], limit=5
        ))
        
        # Get recent system logs
        recent_logs = list(mongo.db.system_logs.find(
            {}, sort=[('timestamp', -1)], limit=20
        ))
        
        # Convert ObjectId to string for JSON serialization
        for session in recent_sessions:
            session['_id'] = str(session['_id'])
        for threat in recent_threats:
            threat['_id'] = str(threat['_id'])
        for log in recent_logs:
            log['_id'] = str(log['_id'])
        
        return jsonify({
            'recent_sessions': recent_sessions,
            'recent_threats': recent_threats,
            'recent_logs': recent_logs
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Recent activity error: {str(e)}', 'dashboard')
        return jsonify({'message': 'Failed to fetch recent activity'}), 500

@dashboard_bp.route('/threat-summary', methods=['GET'])
@jwt_required()
def get_threat_summary():
    """Get threat level summary and statistics."""
    try:
        # Threat level distribution using MongoDB aggregation
        threat_pipeline = [
            {'$group': {'_id': '$threat_level', 'count': {'$sum': 1}}}
        ]
        threat_distribution = list(mongo.db.threat_assessments.aggregate(threat_pipeline))
        
        # Convert to dictionary
        distribution = {item['_id']: item['count'] for item in threat_distribution if item['_id']}
        
        # Isotope detection frequency using MongoDB aggregation
        isotope_pipeline = [
            {'$match': {'consensus_isotope': {'$ne': None, '$exists': True}}},
            {'$group': {'_id': '$consensus_isotope', 'count': {'$sum': 1}}}
        ]
        isotope_frequency = list(mongo.db.threat_assessments.aggregate(isotope_pipeline))
        
        isotopes = {item['_id']: item['count'] for item in isotope_frequency if item['_id']}
        
        # Threat trends (last 7 days) using MongoDB aggregation
        week_ago = datetime.utcnow() - timedelta(days=7)
        trends_pipeline = [
            {'$match': {'assessment_time': {'$gte': week_ago}}},
            {'$group': {
                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$assessment_time'}},
                'count': {'$sum': 1},
                'avg_probability': {'$avg': '$overall_threat_probability'}
            }},
            {'$sort': {'_id': 1}}
        ]
        daily_threats = list(mongo.db.threat_assessments.aggregate(trends_pipeline))
        
        trends = []
        for item in daily_threats:
            trends.append({
                'date': item['_id'],
                'count': item['count'],
                'average_probability': float(item['avg_probability']) if item['avg_probability'] else 0.0
            })
        
        return jsonify({
            'threat_distribution': distribution,
            'isotope_frequency': isotopes,
            'threat_trends': trends,
            'summary': {
                'total_assessments': sum(distribution.values()),
                'high_threat_count': distribution.get('danger', 0),
                'medium_threat_count': distribution.get('warning', 0),
                'low_threat_count': distribution.get('clear', 0)
            }
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Threat summary error: {str(e)}', 'dashboard')
        return jsonify({'message': 'Failed to fetch threat summary'}), 500

@dashboard_bp.route('/system-status', methods=['GET'])
@jwt_required()
def get_system_status():
    """Get detailed system status information."""
    try:
        # Database status
        try:
            mongo.db.command('ping')
            db_status = 'healthy'
        except:
            db_status = 'error'
        
        # Check recent errors
        recent_errors = mongo.db.system_logs.count_documents({
            'level': 'ERROR',
            'timestamp': {'$gte': datetime.utcnow() - timedelta(hours=1)}
        })
        
        # Performance metrics (mock data for demo)
        performance_metrics = {
            'average_analysis_time': 2.5,  # seconds
            'queue_length': 0,
            'cpu_usage': 45.2,  # percentage
            'memory_usage': 62.8,  # percentage
            'disk_usage': 34.1  # percentage
        }
        
        # Service status
        services = {
            'api_server': 'running',
            'database': db_status,
            'ml_service': 'running',
            'quantum_service': 'running',
            'file_service': 'running',
            'websocket_service': 'running'
        }
        
        # Overall health score
        healthy_services = sum(1 for status in services.values() if status == 'running' or status == 'healthy')
        health_score = (healthy_services / len(services)) * 100
        
        return jsonify({
            'services': services,
            'performance_metrics': performance_metrics,
            'health_score': health_score,
            'recent_errors': recent_errors,
            'last_updated': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'System status error: {str(e)}', 'dashboard')
        return jsonify({'message': 'Failed to fetch system status'}), 500
