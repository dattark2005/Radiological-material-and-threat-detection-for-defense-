from flask_pymongo import PyMongo
from datetime import datetime
import uuid
from bson import ObjectId

mongo = PyMongo()

class User:
    """User model for authentication and authorization."""
    
    @staticmethod
    def create(username, email, password_hash, role='operator'):
        """Create a new user."""
        user_data = {
            '_id': str(uuid.uuid4()),
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'role': role,
            'created_at': datetime.utcnow(),
            'last_login': None,
            'is_active': True
        }
        return mongo.db.users.insert_one(user_data)
    
    @staticmethod
    def find_by_email(email):
        """Find user by email."""
        return mongo.db.users.find_one({'email': email})
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID."""
        return mongo.db.users.find_one({'_id': user_id})
    
    @staticmethod
    def update_last_login(user_id):
        """Update user's last login time."""
        return mongo.db.users.update_one(
            {'_id': user_id},
            {'$set': {'last_login': datetime.utcnow()}}
        )
    
    @staticmethod
    def to_dict(user_doc):
        """Convert user document to dictionary."""
        if not user_doc:
            return None
        return {
            'id': user_doc['_id'],
            'username': user_doc['username'],
            'email': user_doc['email'],
            'role': user_doc['role'],
            'created_at': user_doc['created_at'].isoformat() if user_doc.get('created_at') else None,
            'last_login': user_doc['last_login'].isoformat() if user_doc.get('last_login') else None,
            'is_active': user_doc.get('is_active', True)
        }

class SpectrumUpload:
    """Model for uploaded spectrum data files."""
    
    @staticmethod
    def create(filename, original_filename, file_path, file_size, file_type, user_id, **metadata):
        """Create a new spectrum upload record."""
        upload_data = {
            '_id': str(uuid.uuid4()),
            'filename': filename,
            'original_filename': original_filename,
            'file_path': file_path,
            'file_size': file_size,
            'file_type': file_type,
            'upload_time': datetime.utcnow(),
            'user_id': user_id,
            'energy_range_min': metadata.get('energy_range_min'),
            'energy_range_max': metadata.get('energy_range_max'),
            'total_counts': metadata.get('total_counts'),
            'data_points': metadata.get('data_points')
        }
        return mongo.db.spectrum_uploads.insert_one(upload_data)
    
    @staticmethod
    def find_by_user(user_id, limit=50):
        """Find uploads by user ID."""
        return list(mongo.db.spectrum_uploads.find(
            {'user_id': user_id}
        ).sort('upload_time', -1).limit(limit))
    
    @staticmethod
    def find_by_id(upload_id):
        """Find upload by ID."""
        return mongo.db.spectrum_uploads.find_one({'_id': upload_id})
    
    @staticmethod
    def to_dict(upload_doc):
        """Convert upload document to dictionary."""
        if not upload_doc:
            return None
        return {
            'id': upload_doc['_id'],
            'filename': upload_doc['filename'],
            'original_filename': upload_doc['original_filename'],
            'file_size': upload_doc['file_size'],
            'file_type': upload_doc['file_type'],
            'upload_time': upload_doc['upload_time'].isoformat() if upload_doc.get('upload_time') else None,
            'energy_range_min': upload_doc.get('energy_range_min'),
            'energy_range_max': upload_doc.get('energy_range_max'),
            'total_counts': upload_doc.get('total_counts'),
            'data_points': upload_doc.get('data_points')
        }

class AnalysisSession:
    """Model for analysis sessions and runs."""
    
    @staticmethod
    def create(user_id, session_name=None, spectrum_upload_id=None, analysis_type='both', **params):
        """Create a new analysis session."""
        session_data = {
            '_id': str(uuid.uuid4()),
            'session_name': session_name,
            'start_time': datetime.utcnow(),
            'end_time': None,
            'status': 'pending',
            'user_id': user_id,
            'spectrum_upload_id': spectrum_upload_id,
            'analysis_type': analysis_type,
            'noise_level': params.get('noise_level', 1),
            'synthetic_isotope': params.get('synthetic_isotope')
        }
        return mongo.db.analysis_sessions.insert_one(session_data)
    
    @staticmethod
    def update_status(session_id, status, end_time=None):
        """Update session status."""
        update_data = {'status': status}
        if end_time:
            update_data['end_time'] = end_time
        return mongo.db.analysis_sessions.update_one(
            {'_id': str(session_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def update_by_id(session_id, update_data):
        """Update session by ID with arbitrary data."""
        return mongo.db.analysis_sessions.update_one(
            {'_id': str(session_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def find_by_id(session_id):
        """Find session by ID."""
        return mongo.db.analysis_sessions.find_one({'_id': str(session_id)})
    
    @staticmethod
    def find_by_user(user_id, limit=50):
        """Find sessions by user ID."""
        return list(mongo.db.analysis_sessions.find(
            {'user_id': user_id}
        ).sort('start_time', -1).limit(limit))
    
    @staticmethod
    def to_dict(session_doc):
        """Convert session document to dictionary."""
        if not session_doc:
            return None
        return {
            'id': session_doc['_id'],
            'session_name': session_doc.get('session_name'),
            'start_time': session_doc['start_time'].isoformat() if session_doc.get('start_time') else None,
            'end_time': session_doc['end_time'].isoformat() if session_doc.get('end_time') else None,
            'status': session_doc['status'],
            'analysis_type': session_doc.get('analysis_type'),
            'noise_level': session_doc.get('noise_level'),
            'synthetic_isotope': session_doc.get('synthetic_isotope')
        }

class MLResult:
    """Model for ML analysis results."""
    
    @staticmethod
    def create(analysis_session_id, model_type, results):
        """Create a new ML result."""
        result_data = {
            '_id': str(uuid.uuid4()),
            'analysis_session_id': analysis_session_id,
            'model_type': model_type,
            'threat_probability': results['threat_probability'],
            'classified_isotope': results.get('classified_isotope'),
            'confidence_level': results.get('confidence_level'),
            'material_quantity': results.get('material_quantity'),
            'detected_peaks': results.get('detected_peaks', []),
            'model_confidence': results.get('model_confidence'),
            'processing_time': results.get('processing_time'),
            'created_at': datetime.utcnow()
        }
        return mongo.db.ml_results.insert_one(result_data)
    
    @staticmethod
    def find_by_session(session_id):
        """Find results by session ID."""
        return list(mongo.db.ml_results.find({'analysis_session_id': session_id}))
    
    @staticmethod
    def to_dict(result_doc):
        """Convert result document to dictionary."""
        if not result_doc:
            return None
        return {
            'id': result_doc['_id'],
            'model_type': result_doc['model_type'],
            'threat_probability': result_doc['threat_probability'],
            'classified_isotope': result_doc.get('classified_isotope'),
            'confidence_level': result_doc.get('confidence_level'),
            'material_quantity': result_doc.get('material_quantity'),
            'detected_peaks': result_doc.get('detected_peaks', []),
            'model_confidence': result_doc.get('model_confidence'),
            'processing_time': result_doc.get('processing_time'),
            'created_at': result_doc['created_at'].isoformat() if result_doc.get('created_at') else None
        }

class ThreatAssessment:
    """Model for threat assessment results."""
    
    @staticmethod
    def create(analysis_session_id, assessment_data):
        """Create a new threat assessment."""
        threat_data = {
            '_id': str(uuid.uuid4()),
            'analysis_session_id': analysis_session_id,
            'threat_level': assessment_data['threat_level'],
            'overall_threat_probability': assessment_data['overall_threat_probability'],
            'consensus_isotope': assessment_data.get('consensus_isotope'),
            'contamination_radius': assessment_data.get('contamination_radius'),
            'evacuation_recommended': assessment_data.get('evacuation_recommended', False),
            'emergency_response_level': assessment_data.get('emergency_response_level', 0),
            'assessment_time': datetime.utcnow(),
            'model_agreement': assessment_data.get('model_agreement')
        }
        return mongo.db.threat_assessments.insert_one(threat_data)
    
    @staticmethod
    def find_by_session(session_id):
        """Find threat assessment by session ID."""
        return mongo.db.threat_assessments.find_one({'analysis_session_id': session_id})
    
    @staticmethod
    def get_current_threats(limit=10):
        """Get current threat assessments."""
        return list(mongo.db.threat_assessments.find().sort('assessment_time', -1).limit(limit))
    
    @staticmethod
    def to_dict(threat_doc):
        """Convert threat document to dictionary."""
        if not threat_doc:
            return None
        return {
            'id': threat_doc['_id'],
            'threat_level': threat_doc['threat_level'],
            'overall_threat_probability': threat_doc['overall_threat_probability'],
            'consensus_isotope': threat_doc.get('consensus_isotope'),
            'contamination_radius': threat_doc.get('contamination_radius'),
            'evacuation_recommended': threat_doc.get('evacuation_recommended', False),
            'emergency_response_level': threat_doc.get('emergency_response_level', 0),
            'assessment_time': threat_doc['assessment_time'].isoformat() if threat_doc.get('assessment_time') else None,
            'model_agreement': threat_doc.get('model_agreement')
        }

class SystemLog:
    """Model for system logs and audit trail."""
    
    @staticmethod
    def create(level, message, module=None, user_id=None, session_id=None, ip_address=None):
        """Create a new system log entry."""
        log_data = {
            '_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow(),
            'level': level,
            'message': message,
            'module': module,
            'user_id': user_id,
            'session_id': session_id,
            'ip_address': ip_address
        }
        return mongo.db.system_logs.insert_one(log_data)
    
    @staticmethod
    def find_recent(limit=100, level=None):
        """Find recent log entries."""
        query = {}
        if level:
            query['level'] = level
        return list(mongo.db.system_logs.find(query).sort('timestamp', -1).limit(limit))
    
    @staticmethod
    def to_dict(log_doc):
        """Convert log document to dictionary."""
        if not log_doc:
            return None
        return {
            'id': log_doc['_id'],
            'timestamp': log_doc['timestamp'].isoformat() if log_doc.get('timestamp') else None,
            'level': log_doc['level'],
            'message': log_doc['message'],
            'module': log_doc.get('module'),
            'user_id': log_doc.get('user_id'),
            'session_id': log_doc.get('session_id'),
            'ip_address': log_doc.get('ip_address')
        }

class IsotopeReference:
    """Model for isotope reference database."""
    
    @staticmethod
    def create(isotope_data):
        """Create a new isotope reference."""
        isotope_doc = {
            '_id': str(uuid.uuid4()),
            'symbol': isotope_data['symbol'],
            'name': isotope_data['name'],
            'atomic_number': isotope_data.get('atomic_number'),
            'mass_number': isotope_data.get('mass_number'),
            'half_life': isotope_data.get('half_life'),
            'decay_mode': isotope_data.get('decay_mode'),
            'gamma_peaks': isotope_data.get('gamma_peaks', []),
            'peak_intensities': isotope_data.get('peak_intensities', []),
            'isotope_type': isotope_data.get('isotope_type'),
            'threat_level': isotope_data.get('threat_level'),
            'description': isotope_data.get('description'),
            'common_uses': isotope_data.get('common_uses'),
            'safety_notes': isotope_data.get('safety_notes'),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        return mongo.db.isotope_references.insert_one(isotope_doc)
    
    @staticmethod
    def find_all():
        """Find all isotope references."""
        return list(mongo.db.isotope_references.find().sort('symbol', 1))
    
    @staticmethod
    def find_by_symbol(symbol):
        """Find isotope by symbol."""
        return mongo.db.isotope_references.find_one({'symbol': symbol})
    
    @staticmethod
    def search(query):
        """Search isotopes by name or symbol."""
        return list(mongo.db.isotope_references.find({
            '$or': [
                {'symbol': {'$regex': query, '$options': 'i'}},
                {'name': {'$regex': query, '$options': 'i'}}
            ]
        }))
    
    @staticmethod
    def to_dict(isotope_doc):
        """Convert isotope document to dictionary."""
        if not isotope_doc:
            return None
        return {
            'id': isotope_doc['_id'],
            'symbol': isotope_doc['symbol'],
            'name': isotope_doc['name'],
            'atomic_number': isotope_doc.get('atomic_number'),
            'mass_number': isotope_doc.get('mass_number'),
            'half_life': isotope_doc.get('half_life'),
            'decay_mode': isotope_doc.get('decay_mode'),
            'gamma_peaks': isotope_doc.get('gamma_peaks', []),
            'peak_intensities': isotope_doc.get('peak_intensities', []),
            'isotope_type': isotope_doc.get('isotope_type'),
            'threat_level': isotope_doc.get('threat_level'),
            'description': isotope_doc.get('description')
        }

def init_isotope_database():
    """Initialize the isotope reference database with common isotopes."""
    try:
        # Check if MongoDB is connected
        if mongo.db is None:
            print("⚠️  MongoDB not connected, skipping isotope database initialization")
            return 0
            
        isotopes = [
            {
                'symbol': 'K-40',
                'name': 'Potassium-40',
                'atomic_number': 19,
                'mass_number': 40,
                'half_life': '1.25 billion years',
                'decay_type': 'Beta decay, Electron capture',
                'energy_peaks': [1460.8],  # keV
                'threat_level': 'background',
                'description': 'Natural background radiation isotope',
                'common_uses': 'Natural occurrence in environment',
                'safety_notes': 'Natural background, minimal risk'
            },
            {
                'symbol': 'Cs-137',
                'name': 'Cesium-137',
                'atomic_number': 55,
                'mass_number': 137,
                'half_life': '30.17 years',
                'decay_type': 'Beta decay',
                'energy_peaks': [661.7],  # keV
                'threat_level': 'medium',
                'description': 'Common medical and industrial isotope',
                'common_uses': 'Medical radiotherapy, industrial gauging',
                'safety_notes': 'Moderate radiation risk, requires proper handling'
            },
            {
                'symbol': 'Co-60',
                'name': 'Cobalt-60',
                'atomic_number': 27,
                'mass_number': 60,
                'half_life': '5.27 years',
                'decay_type': 'Beta decay',
                'energy_peaks': [1173.2, 1332.5],  # keV
                'threat_level': 'high',
                'description': 'Industrial and medical isotope',
                'common_uses': 'Sterilization, radiotherapy, industrial radiography',
                'safety_notes': 'High radiation risk, strict security required'
            },
            {
                'symbol': 'U-238',
                'name': 'Uranium-238',
                'atomic_number': 92,
                'mass_number': 238,
                'half_life': '4.47 billion years',
                'decay_type': 'Alpha decay',
                'energy_peaks': [1001.0, 766.4],  # keV
                'threat_level': 'very_high',
                'description': 'Most common isotope of uranium, fissile material',
                'common_uses': 'Nuclear fuel, depleted uranium applications',
                'safety_notes': 'Extremely high security risk, nuclear material'
            }
        ]
        
        # Check if isotopes already exist
        existing_count = mongo.db.isotope_references.count_documents({})
        if existing_count == 0:
            for isotope in isotopes:
                IsotopeReference.create(isotope)
            return len(isotopes)
        return 0
    except Exception as e:
        print(f"⚠️  Error initializing isotope database: {e}")
        print("📝 Application will continue without isotope database")
        return 0
