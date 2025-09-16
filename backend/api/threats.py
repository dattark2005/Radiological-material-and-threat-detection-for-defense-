from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from models.database import ThreatAssessment, AnalysisSession, mongo
from services.threat_service import ThreatAssessmentService
from utils.logger import log_system_event

threats_bp = Blueprint('threats', __name__)

@threats_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_threat():
    """Get current threat status."""
    try:
        # Get the most recent threat assessment
        latest_assessment = mongo.db.threat_assessments.find_one(
            {}, sort=[('assessment_time', -1)]
        )
        
        if not latest_assessment:
            return jsonify({
                'threat_level': 'clear',
                'overall_threat_probability': 0.0,
                'message': 'No threat assessments available',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        threat_service = ThreatAssessmentService()
        
        return jsonify({
            'assessment': latest_assessment.to_dict(),
            'summary': threat_service.generate_threat_summary(latest_assessment.to_dict()),
            'recommendations': threat_service.get_response_recommendations(latest_assessment.to_dict()),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Current threat retrieval error: {str(e)}', 'threats')
        return jsonify({'message': 'Failed to get current threat status'}), 500

@threats_bp.route('/history', methods=['GET'])
@jwt_required()
def get_threat_history():
    """Get threat assessment history."""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        threat_level = request.args.get('threat_level')
        days = request.args.get('days', 30, type=int)
        
        # Limit per_page
        per_page = min(per_page, 100)
        
        # Build query
        query = ThreatAssessment.query
        
        # Filter by threat level if specified
        if threat_level:
            query = query.filter_by(threat_level=threat_level)
        
        # Filter by date range
        if days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(ThreatAssessment.assessment_time >= cutoff_date)
        
        # Execute query with pagination
        assessments = query.order_by(
            desc(ThreatAssessment.assessment_time)
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'assessments': [assessment.to_dict() for assessment in assessments.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': assessments.total,
                'pages': assessments.pages,
                'has_next': assessments.has_next,
                'has_prev': assessments.has_prev
            }
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Threat history error: {str(e)}', 'threats')
        return jsonify({'message': 'Failed to get threat history'}), 500

@threats_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_threat_statistics():
    """Get threat statistics and trends."""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get threat level distribution
        from sqlalchemy import func
        threat_distribution = db.session.query(
            ThreatAssessment.threat_level,
            func.count(ThreatAssessment.id).label('count')
        ).filter(
            ThreatAssessment.assessment_time >= cutoff_date
        ).group_by(ThreatAssessment.threat_level).all()
        
        distribution = {level: count for level, count in threat_distribution}
        
        # Get isotope frequency
        isotope_frequency = db.session.query(
            ThreatAssessment.consensus_isotope,
            func.count(ThreatAssessment.id).label('count')
        ).filter(
            ThreatAssessment.assessment_time >= cutoff_date,
            ThreatAssessment.consensus_isotope.isnot(None),
            ThreatAssessment.consensus_isotope != 'Unknown'
        ).group_by(ThreatAssessment.consensus_isotope).all()
        
        isotopes = {isotope: count for isotope, count in isotope_frequency}
        
        # Get daily threat trends
        daily_trends = db.session.query(
            func.date(ThreatAssessment.assessment_time).label('date'),
            func.count(ThreatAssessment.id).label('total_assessments'),
            func.sum(func.case([(ThreatAssessment.threat_level == 'danger', 1)], else_=0)).label('high_threats'),
            func.avg(ThreatAssessment.overall_threat_probability).label('avg_probability')
        ).filter(
            ThreatAssessment.assessment_time >= cutoff_date
        ).group_by(
            func.date(ThreatAssessment.assessment_time)
        ).order_by('date').all()
        
        trends = []
        for date, total, high_threats, avg_prob in daily_trends:
            trends.append({
                'date': date.isoformat(),
                'total_assessments': total,
                'high_threats': high_threats or 0,
                'average_probability': float(avg_prob) if avg_prob else 0.0
            })
        
        # Calculate summary statistics
        total_assessments = sum(distribution.values())
        high_threat_rate = (distribution.get('danger', 0) / total_assessments * 100) if total_assessments > 0 else 0
        
        return jsonify({
            'period_days': days,
            'threat_distribution': distribution,
            'isotope_frequency': isotopes,
            'daily_trends': trends,
            'summary': {
                'total_assessments': total_assessments,
                'high_threat_count': distribution.get('danger', 0),
                'medium_threat_count': distribution.get('warning', 0),
                'low_threat_count': distribution.get('clear', 0),
                'high_threat_rate': round(high_threat_rate, 2)
            }
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Threat statistics error: {str(e)}', 'threats')
        return jsonify({'message': 'Failed to get threat statistics'}), 500

@threats_bp.route('/assessment/<assessment_id>', methods=['GET'])
@jwt_required()
def get_threat_assessment(assessment_id):
    """Get specific threat assessment details."""
    try:
        assessment = ThreatAssessment.query.get(assessment_id)
        if not assessment:
            return jsonify({'message': 'Threat assessment not found'}), 404
        
        # Get related analysis session
        session = AnalysisSession.query.get(assessment.analysis_session_id)
        
        threat_service = ThreatAssessmentService()
        
        return jsonify({
            'assessment': assessment.to_dict(),
            'analysis_session': session.to_dict() if session else None,
            'summary': threat_service.generate_threat_summary(assessment.to_dict()),
            'recommendations': threat_service.get_response_recommendations(assessment.to_dict())
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Threat assessment retrieval error: {str(e)}', 'threats')
        return jsonify({'message': 'Failed to get threat assessment'}), 500

@threats_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_active_alerts():
    """Get active threat alerts."""
    try:
        # Get recent high-threat assessments (last 24 hours)
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        active_alerts = ThreatAssessment.query.filter(
            ThreatAssessment.assessment_time >= cutoff_time,
            ThreatAssessment.threat_level.in_(['warning', 'danger'])
        ).order_by(desc(ThreatAssessment.assessment_time)).all()
        
        alerts = []
        for assessment in active_alerts:
            alert = {
                'id': assessment.id,
                'threat_level': assessment.threat_level,
                'probability': assessment.overall_threat_probability,
                'isotope': assessment.consensus_isotope,
                'timestamp': assessment.assessment_time.isoformat(),
                'contamination_radius': assessment.contamination_radius,
                'evacuation_recommended': assessment.evacuation_recommended,
                'emergency_response_level': assessment.emergency_response_level
            }
            alerts.append(alert)
        
        return jsonify({
            'active_alerts': alerts,
            'alert_count': len(alerts),
            'highest_threat_level': max([a['threat_level'] for a in alerts], default='clear'),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Active alerts error: {str(e)}', 'threats')
        return jsonify({'message': 'Failed to get active alerts'}), 500

@threats_bp.route('/simulate-threat', methods=['POST'])
@jwt_required()
def simulate_threat():
    """Simulate a threat scenario for testing (admin only)."""
    try:
        user_id = get_jwt_identity()
        from models.database import User
        user = User.query.get(user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        data = request.get_json()
        threat_level = data.get('threat_level', 'warning')
        isotope = data.get('isotope', 'Cs-137')
        probability = data.get('probability', 0.75)
        
        # Create simulated threat assessment
        assessment = ThreatAssessment(
            analysis_session_id=None,  # No actual analysis session
            threat_level=threat_level,
            overall_threat_probability=probability,
            consensus_isotope=isotope,
            contamination_radius=50.0 * probability,
            evacuation_recommended=threat_level == 'danger' and probability > 0.8,
            emergency_response_level=3 if threat_level == 'danger' else 1,
            model_agreement=0.9
        )
        
        db.session.add(assessment)
        db.session.commit()
        
        # Emit WebSocket event for real-time updates
        from services.websocket_service import emit_threat_detected
        emit_threat_detected(assessment.to_dict())
        
        log_system_event('INFO', f'Simulated threat created: {threat_level}', 'threats', user_id)
        
        return jsonify({
            'message': 'Threat simulation created',
            'assessment': assessment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        log_system_event('ERROR', f'Threat simulation error: {str(e)}', 'threats')
        return jsonify({'message': 'Failed to simulate threat'}), 500
