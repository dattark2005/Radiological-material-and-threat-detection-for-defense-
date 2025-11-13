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
        
        # Convert ObjectId to string for JSON serialization
        latest_assessment['_id'] = str(latest_assessment['_id'])
        
        assessment_dict = ThreatAssessment.to_dict(latest_assessment)
        
        return jsonify({
            'assessment': assessment_dict,
            'summary': threat_service.generate_threat_summary(assessment_dict),
            'recommendations': threat_service.get_response_recommendations(assessment_dict),
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
        
        # Build MongoDB query
        query_filter = {}
        
        # Filter by threat level if specified
        if threat_level:
            query_filter['threat_level'] = threat_level
        
        # Filter by date range
        if days > 0:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query_filter['assessment_time'] = {'$gte': cutoff_date}
        
        # Get paginated assessments
        skip = (page - 1) * per_page
        assessments = list(mongo.db.threat_assessments.find(
            query_filter
        ).sort('assessment_time', -1).skip(skip).limit(per_page))
        
        # Get total count for pagination
        total = mongo.db.threat_assessments.count_documents(query_filter)
        pages = (total + per_page - 1) // per_page
        
        # Convert ObjectId to string for JSON serialization
        for assessment in assessments:
            assessment['_id'] = str(assessment['_id'])
        
        return jsonify({
            'assessments': [ThreatAssessment.to_dict(assessment) for assessment in assessments],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': pages,
                'has_next': page < pages,
                'has_prev': page > 1
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
        
        # Get threat level distribution using MongoDB aggregation
        threat_distribution_pipeline = [
            {'$match': {'assessment_time': {'$gte': cutoff_date}}},
            {'$group': {'_id': '$threat_level', 'count': {'$sum': 1}}}
        ]
        threat_dist_result = list(mongo.db.threat_assessments.aggregate(threat_distribution_pipeline))
        distribution = {item['_id']: item['count'] for item in threat_dist_result}
        
        # Get isotope frequency using MongoDB aggregation
        isotope_frequency_pipeline = [
            {'$match': {
                'assessment_time': {'$gte': cutoff_date},
                'consensus_isotope': {'$ne': None, '$ne': 'Unknown'}
            }},
            {'$group': {'_id': '$consensus_isotope', 'count': {'$sum': 1}}}
        ]
        isotope_freq_result = list(mongo.db.threat_assessments.aggregate(isotope_frequency_pipeline))
        isotopes = {item['_id']: item['count'] for item in isotope_freq_result}
        
        # Get daily threat trends using MongoDB aggregation
        daily_trends_pipeline = [
            {'$match': {'assessment_time': {'$gte': cutoff_date}}},
            {'$group': {
                '_id': {'$dateToString': {'format': '%Y-%m-%d', 'date': '$assessment_time'}},
                'total_assessments': {'$sum': 1},
                'high_threats': {'$sum': {'$cond': [{'$eq': ['$threat_level', 'danger']}, 1, 0]}},
                'avg_probability': {'$avg': '$overall_threat_probability'}
            }},
            {'$sort': {'_id': 1}}
        ]
        daily_trends_result = list(mongo.db.threat_assessments.aggregate(daily_trends_pipeline))
        
        trends = []
        for item in daily_trends_result:
            trends.append({
                'date': item['_id'],
                'total_assessments': item['total_assessments'],
                'high_threats': item['high_threats'],
                'average_probability': float(item['avg_probability']) if item['avg_probability'] else 0.0
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
        assessment = mongo.db.threat_assessments.find_one({'_id': assessment_id})
        if not assessment:
            return jsonify({'message': 'Threat assessment not found'}), 404
        
        # Get related analysis session
        session = mongo.db.analysis_sessions.find_one({'_id': assessment.get('analysis_session_id')})
        
        # Convert ObjectId to string for JSON serialization
        assessment['_id'] = str(assessment['_id'])
        if session:
            session['_id'] = str(session['_id'])
        
        threat_service = ThreatAssessmentService()
        assessment_dict = ThreatAssessment.to_dict(assessment)
        
        return jsonify({
            'assessment': assessment_dict,
            'analysis_session': AnalysisSession.to_dict(session) if session else None,
            'summary': threat_service.generate_threat_summary(assessment_dict),
            'recommendations': threat_service.get_response_recommendations(assessment_dict)
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
        
        active_alerts = list(mongo.db.threat_assessments.find({
            'assessment_time': {'$gte': cutoff_time},
            'threat_level': {'$in': ['warning', 'danger']}
        }).sort('assessment_time', -1))
        
        alerts = []
        for assessment in active_alerts:
            alert = {
                'id': str(assessment['_id']),
                'threat_level': assessment['threat_level'],
                'probability': assessment['overall_threat_probability'],
                'isotope': assessment.get('consensus_isotope'),
                'timestamp': assessment['assessment_time'].isoformat(),
                'contamination_radius': assessment.get('contamination_radius'),
                'evacuation_recommended': assessment.get('evacuation_recommended', False),
                'emergency_response_level': assessment.get('emergency_response_level', 0)
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
        user = User.find_by_id(user_id)
        
        if not user or user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        
        data = request.get_json()
        threat_level = data.get('threat_level', 'warning')
        isotope = data.get('isotope', 'Cs-137')
        probability = data.get('probability', 0.75)
        
        # Create simulated threat assessment data
        assessment_data = {
            'threat_level': threat_level,
            'overall_threat_probability': probability,
            'consensus_isotope': isotope,
            'contamination_radius': 50.0 * probability,
            'evacuation_recommended': threat_level == 'danger' and probability > 0.8,
            'emergency_response_level': 3 if threat_level == 'danger' else 1,
            'model_agreement': 0.9
        }
        
        # Create the assessment using the model
        result = ThreatAssessment.create(None, assessment_data)  # No actual analysis session
        assessment_id = str(result.inserted_id)
        
        # Get the created assessment for response
        created_assessment = mongo.db.threat_assessments.find_one({'_id': assessment_id})
        created_assessment['_id'] = str(created_assessment['_id'])
        
        # Emit WebSocket event for real-time updates
        from services.websocket_service import emit_threat_detected
        emit_threat_detected(ThreatAssessment.to_dict(created_assessment))
        
        log_system_event('INFO', f'Simulated threat created: {threat_level}', 'threats', user_id)
        
        return jsonify({
            'message': 'Threat simulation created',
            'assessment': ThreatAssessment.to_dict(created_assessment)
        }), 201
        
    except Exception as e:
        log_system_event('ERROR', f'Threat simulation error: {str(e)}', 'threats')
        return jsonify({'message': 'Failed to simulate threat'}), 500
