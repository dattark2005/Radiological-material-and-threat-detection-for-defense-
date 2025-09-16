from flask_socketio import emit, join_room, leave_room
from flask import request
import logging
from datetime import datetime

# Global SocketIO instance will be set by the main app
socketio = None

def register_socketio_events(socketio_instance):
    """Register WebSocket event handlers."""
    global socketio
    socketio = socketio_instance
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        logging.info(f"Client connected: {request.sid}")
        emit('connection_status', {'status': 'connected', 'timestamp': datetime.utcnow().isoformat()})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        logging.info(f"Client disconnected: {request.sid}")
    
    @socketio.on('join_live_mode')
    def handle_join_live_mode(data):
        """Handle client joining live mode."""
        user_id = data.get('user_id')
        if user_id:
            join_room(f"live_mode_{user_id}")
            emit('live_mode_status', {'status': 'joined', 'timestamp': datetime.utcnow().isoformat()})
            logging.info(f"User {user_id} joined live mode")
    
    @socketio.on('leave_live_mode')
    def handle_leave_live_mode(data):
        """Handle client leaving live mode."""
        user_id = data.get('user_id')
        if user_id:
            leave_room(f"live_mode_{user_id}")
            emit('live_mode_status', {'status': 'left', 'timestamp': datetime.utcnow().isoformat()})
            logging.info(f"User {user_id} left live mode")
    
    @socketio.on('request_system_status')
    def handle_system_status_request():
        """Handle system status request."""
        status = get_system_status()
        emit('system_status_update', status)

def emit_analysis_complete(session_id, threat_assessment):
    """Emit analysis completion event."""
    if socketio:
        socketio.emit('analysis_complete', {
            'session_id': session_id,
            'threat_assessment': threat_assessment,
            'timestamp': datetime.utcnow().isoformat()
        })

def emit_threat_detected(threat_data):
    """Emit threat detection event."""
    if socketio:
        socketio.emit('threat_detected', {
            'threat_data': threat_data,
            'timestamp': datetime.utcnow().isoformat()
        })

def emit_live_scan_result(user_id, scan_result):
    """Emit live scan result to specific user."""
    if socketio:
        socketio.emit('live_scan_result', {
            'scan_result': scan_result,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"live_mode_{user_id}")

def emit_system_alert(alert_data):
    """Emit system-wide alert."""
    if socketio:
        socketio.emit('system_alert', {
            'alert': alert_data,
            'timestamp': datetime.utcnow().isoformat()
        })

def get_system_status():
    """Get current system status."""
    return {
        'status': 'operational',
        'services': {
            'api': 'running',
            'database': 'running',
            'ml_service': 'running',
            'quantum_service': 'running'
        },
        'timestamp': datetime.utcnow().isoformat()
    }
