from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from utils.auth import require_role
from services.monitoring_service import system_monitor
import logging

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/system/metrics', methods=['GET'])
@jwt_required()
@require_role(['admin', 'operator'])
def get_system_metrics():
    """Get current system performance metrics."""
    try:
        metrics = system_monitor.get_system_metrics()
        return jsonify({
            'success': True,
            'data': metrics
        })
    except Exception as e:
        logging.error(f"Error getting system metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve system metrics'
        }), 500

@monitoring_bp.route('/application/metrics', methods=['GET'])
@jwt_required()
@require_role(['admin', 'operator'])
def get_application_metrics():
    """Get application-specific metrics."""
    try:
        metrics = system_monitor.get_application_metrics()
        return jsonify({
            'success': True,
            'data': metrics
        })
    except Exception as e:
        logging.error(f"Error getting application metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve application metrics'
        }), 500

@monitoring_bp.route('/errors/metrics', methods=['GET'])
@jwt_required()
@require_role(['admin', 'operator'])
def get_error_metrics():
    """Get error and log metrics."""
    try:
        metrics = system_monitor.get_error_metrics()
        return jsonify({
            'success': True,
            'data': metrics
        })
    except Exception as e:
        logging.error(f"Error getting error metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve error metrics'
        }), 500

@monitoring_bp.route('/health', methods=['GET'])
def get_health_status():
    """Get overall system health status - public endpoint for load balancers."""
    try:
        health = system_monitor.get_health_status()
        status_code = 200 if health.get('overall_status') == 'healthy' else 503
        return jsonify(health), status_code
    except Exception as e:
        logging.error(f"Error checking health status: {str(e)}")
        return jsonify({
            'overall_status': 'unhealthy',
            'error': str(e)
        }), 503

@monitoring_bp.route('/health/detailed', methods=['GET'])
@jwt_required()
@require_role(['admin', 'operator'])
def get_detailed_health():
    """Get detailed health status with all metrics."""
    try:
        health = system_monitor.get_health_status()
        system_metrics = system_monitor.get_system_metrics()
        app_metrics = system_monitor.get_application_metrics()
        error_metrics = system_monitor.get_error_metrics()
        
        return jsonify({
            'success': True,
            'data': {
                'health': health,
                'system': system_metrics,
                'application': app_metrics,
                'errors': error_metrics
            }
        })
    except Exception as e:
        logging.error(f"Error getting detailed health: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve detailed health status'
        }), 500

@monitoring_bp.route('/alerts', methods=['GET'])
@jwt_required()
@require_role(['admin', 'operator'])
def get_system_alerts():
    """Get current system alerts and warnings."""
    try:
        health = system_monitor.get_health_status()
        
        alerts = []
        if 'health_checks' in health:
            for check_name, check_result in health['health_checks'].items():
                if not check_result['healthy']:
                    alerts.append({
                        'type': 'error',
                        'component': check_name,
                        'message': check_result['message'],
                        'timestamp': health['timestamp']
                    })
                elif check_result.get('warning'):
                    alerts.append({
                        'type': 'warning',
                        'component': check_name,
                        'message': check_result['message'],
                        'timestamp': health['timestamp']
                    })
        
        return jsonify({
            'success': True,
            'data': {
                'alerts': alerts,
                'total_alerts': len(alerts),
                'critical_alerts': len([a for a in alerts if a['type'] == 'error'])
            }
        })
    except Exception as e:
        logging.error(f"Error getting system alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve system alerts'
        }), 500
