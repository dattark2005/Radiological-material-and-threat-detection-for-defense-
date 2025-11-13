from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import threading
import time

from models.database import AnalysisSession, MLResult, ThreatAssessment, SpectrumUpload, mongo
from services.ml_service import ClassicalMLService
from services.real_quantum_service import RealQuantumMLService
from services.threat_service import ThreatAssessmentService
from utils.logger import log_system_event

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/run', methods=['POST'])
@jwt_required()
def run_analysis():
    """Start analysis on spectrum data."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Validate input
        if 'spectrum_data' not in data:
            return jsonify({'message': 'Spectrum data is required'}), 400
        
        spectrum_data = data['spectrum_data']
        analysis_type = data.get('analysis_type', 'both')  # classical, quantum, both
        session_name = data.get('session_name', f'Analysis_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}')
        
        # Prepare session parameters
        spectrum_upload_id = None
        if 'upload_id' in data:
            from bson import ObjectId
            try:
                upload = SpectrumUpload.find_by_id(ObjectId(data['upload_id']))
                if upload and upload.get('user_id') == user_id:
                    spectrum_upload_id = data['upload_id']
            except:
                pass
        
        # Create analysis session using the correct method signature
        result = AnalysisSession.create(
            user_id=user_id,
            session_name=session_name,
            spectrum_upload_id=spectrum_upload_id,
            analysis_type=analysis_type,
            synthetic_isotope=data.get('synthetic_isotope'),
            noise_level=data.get('noise_level', 1)
        )
        session_id = result.inserted_id
        
        # Start analysis in background thread
        analysis_thread = threading.Thread(
            target=perform_analysis_async,
            args=(str(session_id), spectrum_data, analysis_type)
        )
        analysis_thread.daemon = True
        analysis_thread.start()
        
        log_system_event('INFO', f'Analysis started: {str(session_id)}', 'analysis', user_id)
        
        return jsonify({
            'message': 'Analysis started',
            'session_id': str(session_id),
            'status': 'pending'
        }), 202
        
    except Exception as e:
        log_system_event('ERROR', f'Analysis start error: {str(e)}', 'analysis')
        return jsonify({'message': 'Failed to start analysis'}), 500

def perform_analysis_async(session_id, spectrum_data, analysis_type):
    """Perform analysis asynchronously."""
    print(f"[DEBUG] Starting analysis for session {session_id}, type: {analysis_type}")
    print(f"[DEBUG] Spectrum data keys: {spectrum_data.keys() if isinstance(spectrum_data, dict) else 'Not a dict'}")
    
    from app import create_app
    
    app = create_app()
    with app.app_context():
        try:
            # Update session status
            AnalysisSession.update_by_id(session_id, {
                'status': 'running',
                'start_time': datetime.utcnow()
            })
            
            # Initialize services
            classical_service = ClassicalMLService()
            quantum_service = RealQuantumMLService()
            threat_service = ThreatAssessmentService()
            
            results = []
            
            # Run classical analysis
            if analysis_type in ['classical', 'both']:
                classical_result = classical_service.analyze(spectrum_data)
                
                MLResult.create(session_id, 'classical', classical_result)
                results.append(classical_result)
            
            # Run quantum analysis
            if analysis_type in ['quantum', 'both']:
                quantum_result = quantum_service.analyze(spectrum_data)
                
                MLResult.create(session_id, 'quantum', quantum_result)
                results.append(quantum_result)
            
            # Perform threat assessment
            threat_assessment = threat_service.assess_threat(results)
            
            ThreatAssessment.create(session_id, threat_assessment)
            
            # Update session
            AnalysisSession.update_by_id(session_id, {
                'status': 'completed',
                'end_time': datetime.utcnow()
            })
            
            # Emit WebSocket event
            from services.websocket_service import emit_analysis_complete
            emit_analysis_complete(session_id, threat_assessment)
            
            log_system_event('INFO', f'Analysis completed: {session_id}', 'analysis')
            
        except Exception as e:
            print(f"[ERROR] Analysis failed for session {session_id}: {str(e)}")
            print(f"[ERROR] Exception type: {type(e).__name__}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            
            # Mark session as failed
            AnalysisSession.update_by_id(session_id, {
                'status': 'failed',
                'end_time': datetime.utcnow(),
                'error_message': str(e)
            })
            
            log_system_event('ERROR', f'Analysis failed: {session_id} - {str(e)}', 'analysis')

@analysis_bp.route('/status/<session_id>', methods=['GET'])
@jwt_required()
def get_analysis_status(session_id):
    """Get analysis session status."""
    try:
        user_id = get_jwt_identity()
        print(f"[DEBUG] Status check - User ID: {user_id}, Session ID: {session_id}")
        
        try:
            session = AnalysisSession.find_by_id(session_id)
        except Exception as e:
            print(f"[DEBUG] Error finding session: {e}")
            return jsonify({'message': 'Invalid session ID'}), 400
            
        if not session:
            print(f"[DEBUG] Session not found: {session_id}")
            return jsonify({'message': 'Analysis session not found'}), 404
        
        print(f"[DEBUG] Session found - Session user_id: {session.get('user_id')}, Current user_id: {user_id}")
        
        # Check ownership
        if session.get('user_id') != user_id:
            print(f"[DEBUG] Access denied - Session owner: {session.get('user_id')}, Current user: {user_id}")
            return jsonify({'message': 'Access denied'}), 403
        
        # Convert ObjectId to string for JSON serialization
        session['_id'] = str(session['_id'])
        
        return jsonify({
            'session': session,
            'status': session.get('status')
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Status check error: {str(e)}', 'analysis')
        return jsonify({'message': 'Failed to get analysis status'}), 500

@analysis_bp.route('/results/<session_id>', methods=['GET'])
@jwt_required()
def get_analysis_results(session_id):
    """Get analysis results."""
    try:
        user_id = get_jwt_identity()
        
        try:
            session = AnalysisSession.find_by_id(session_id)
        except:
            return jsonify({'message': 'Invalid session ID'}), 400
            
        if not session:
            return jsonify({'message': 'Analysis session not found'}), 404
        
        # Check ownership
        if session.get('user_id') != user_id:
            return jsonify({'message': 'Access denied'}), 403
        
        # Get ML results
        ml_results = list(mongo.db.ml_results.find({'analysis_session_id': session_id}))
        
        # Get threat assessment
        threat_assessment = mongo.db.threat_assessments.find_one({'analysis_session_id': session_id})
        
        # Convert ObjectId to string for JSON serialization
        session['_id'] = str(session['_id'])
        for result in ml_results:
            result['_id'] = str(result['_id'])
        if threat_assessment:
            threat_assessment['_id'] = str(threat_assessment['_id'])
        
        return jsonify({
            'session': session,
            'ml_results': ml_results,
            'threat_assessment': threat_assessment
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Results retrieval error: {str(e)}', 'analysis')
        return jsonify({'message': 'Failed to get analysis results'}), 500

@analysis_bp.route('/history', methods=['GET'])
@jwt_required()
def get_analysis_history():
    """Get user's analysis history."""
    try:
        user_id = get_jwt_identity()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        # Limit per_page
        per_page = min(per_page, 100)
        
        # Build MongoDB query
        query_filter = {'user_id': user_id}
        
        if status_filter:
            query_filter['status'] = status_filter
        
        # Get paginated sessions
        skip = (page - 1) * per_page
        sessions = list(mongo.db.analysis_sessions.find(
            query_filter
        ).sort('start_time', -1).skip(skip).limit(per_page))
        
        # Get total count for pagination
        total = mongo.db.analysis_sessions.count_documents(query_filter)
        pages = (total + per_page - 1) // per_page
        
        # Convert ObjectId to string for JSON serialization
        for session in sessions:
            session['_id'] = str(session['_id'])
        
        return jsonify({
            'sessions': sessions,
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
        log_system_event('ERROR', f'Analysis history error: {str(e)}', 'analysis')
        return jsonify({'message': 'Failed to fetch analysis history'}), 500

@analysis_bp.route('/cancel/<session_id>', methods=['POST'])
@jwt_required()
def cancel_analysis(session_id):
    """Cancel running analysis."""
    try:
        user_id = get_jwt_identity()
        
        try:
            session = AnalysisSession.find_by_id(session_id)
        except:
            return jsonify({'message': 'Invalid session ID'}), 400
        if not session:
            return jsonify({'message': 'Analysis session not found'}), 404
        
        # Check ownership
        if session.get('user_id') != user_id:
            return jsonify({'message': 'Access denied'}), 403
        
        # Can only cancel pending or running analyses
        if session.get('status') not in ['pending', 'running']:
            return jsonify({'message': 'Cannot cancel completed analysis'}), 400
        
        # Update status
        AnalysisSession.update_by_id(session_id, {
            'status': 'cancelled',
            'end_time': datetime.utcnow()
        })
        
        log_system_event('INFO', f'Analysis cancelled: {session_id}', 'analysis', user_id)
        
        return jsonify({'message': 'Analysis cancelled successfully'}), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Analysis cancellation error: {str(e)}', 'analysis')
        return jsonify({'message': 'Failed to cancel analysis'}), 500
