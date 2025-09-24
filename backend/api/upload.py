from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from models.database import SpectrumUpload, mongo
from utils.file_utils import save_uploaded_file, parse_spectrum_file, generate_synthetic_spectrum, validate_spectrum_data
from utils.logger import log_system_event

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/spectrum', methods=['POST'])
@jwt_required()
def upload_spectrum():
    """Upload spectrum data file."""
    try:
        user_id = get_jwt_identity()
        
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'message': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'No file selected'}), 400
        
        # Save uploaded file
        file_info = save_uploaded_file(file)
        if not file_info:
            return jsonify({'message': 'Invalid file type or upload failed'}), 400
        
        # Parse spectrum data
        try:
            spectrum_data = parse_spectrum_file(file_info['file_path'], file_info['file_type'])
            validate_spectrum_data(spectrum_data)
        except ValueError as e:
            return jsonify({'message': str(e)}), 400
        
        # Create database record
        spectrum_data_doc = {
            'filename': file_info['filename'],
            'original_filename': file_info['original_filename'],
            'file_path': file_info['file_path'],
            'file_size': file_info['file_size'],
            'file_type': file_info['file_type'],
            'user_id': user_id,
            'energy_range_min': spectrum_data['energy_range_min'],
            'energy_range_max': spectrum_data['energy_range_max'],
            'total_counts': spectrum_data['total_counts'],
            'data_points': spectrum_data['data_points']
        }
        
        result = SpectrumUpload.create(spectrum_data_doc)
        upload_id = result.inserted_id
        
        log_system_event('INFO', f'Spectrum file uploaded: {file_info["original_filename"]}', 'upload', user_id)
        
        return jsonify({
            'message': 'File uploaded successfully',
            'upload_id': str(upload_id),
            'spectrum_data': spectrum_data,
            'file_info': spectrum_data_doc
        }), 201
        
    except Exception as e:
        log_system_event('ERROR', f'Upload error: {str(e)}', 'upload')
        return jsonify({'message': 'Upload failed'}), 500

@upload_bp.route('/synthetic', methods=['POST'])
@jwt_required()
def generate_synthetic():
    """Generate synthetic spectrum data."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Debug logging
        print(f"[DEBUG] Received synthetic request data: {data}")
        
        # Validate input
        if not data:
            return jsonify({'message': 'No JSON data received'}), 400
            
        if 'isotope' not in data:
            return jsonify({'message': 'Isotope type is required'}), 400
        
        isotope = data['isotope']
        noise_level = data.get('noise_level', 1)
        
        # Validate parameters
        valid_isotopes = ['K-40', 'Cs-137', 'Co-60', 'U-238', 'mixed']
        if isotope not in valid_isotopes:
            return jsonify({'message': f'Invalid isotope. Must be one of: {valid_isotopes}'}), 400
        
        if not isinstance(noise_level, int) or noise_level < 1 or noise_level > 3:
            return jsonify({'message': 'Noise level must be 1, 2, or 3'}), 400
        
        # Generate synthetic spectrum
        spectrum_data = generate_synthetic_spectrum(isotope, noise_level)
        
        log_system_event('INFO', f'Synthetic spectrum generated: {isotope} (noise: {noise_level})', 'upload', user_id)
        
        return jsonify({
            'message': 'Synthetic spectrum generated successfully',
            'spectrum_data': spectrum_data
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Synthetic generation error: {str(e)}', 'upload')
        return jsonify({'message': 'Failed to generate synthetic spectrum'}), 500

@upload_bp.route('/spectrum/<upload_id>', methods=['GET'])
@jwt_required()
def get_spectrum(upload_id):
    """Get spectrum data by upload ID."""
    try:
        user_id = get_jwt_identity()
        
        # Find spectrum upload
        from bson import ObjectId
        try:
            spectrum_upload = SpectrumUpload.find_by_id(ObjectId(upload_id))
        except:
            return jsonify({'message': 'Invalid upload ID'}), 400
            
        if not spectrum_upload:
            return jsonify({'message': 'Spectrum not found'}), 404
        
        # Check ownership (users can only access their own uploads)
        if spectrum_upload.get('user_id') != user_id:
            return jsonify({'message': 'Access denied'}), 403
        
        # Parse spectrum data from file
        try:
            spectrum_data = parse_spectrum_file(spectrum_upload['file_path'], spectrum_upload['file_type'])
        except Exception as e:
            return jsonify({'message': f'Failed to read spectrum data: {str(e)}'}), 500
        
        # Convert ObjectId to string for JSON serialization
        spectrum_upload['_id'] = str(spectrum_upload['_id'])
        
        return jsonify({
            'upload_info': spectrum_upload,
            'spectrum_data': spectrum_data
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Spectrum retrieval error: {str(e)}', 'upload')
        return jsonify({'message': 'Failed to retrieve spectrum'}), 500

@upload_bp.route('/history', methods=['GET'])
@jwt_required()
def get_upload_history():
    """Get user's upload history."""
    try:
        user_id = get_jwt_identity()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Limit per_page to prevent abuse
        per_page = min(per_page, 100)
        
        # Query user's uploads with pagination
        skip = (page - 1) * per_page
        uploads = list(mongo.db.spectrum_uploads.find(
            {'user_id': user_id}
        ).sort('upload_time', -1).skip(skip).limit(per_page))
        
        # Get total count for pagination
        total = mongo.db.spectrum_uploads.count_documents({'user_id': user_id})
        pages = (total + per_page - 1) // per_page
        
        # Convert ObjectId to string for JSON serialization
        for upload in uploads:
            upload['_id'] = str(upload['_id'])
        
        return jsonify({
            'uploads': uploads,
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
        log_system_event('ERROR', f'Upload history error: {str(e)}', 'upload')
        return jsonify({'message': 'Failed to fetch upload history'}), 500

@upload_bp.route('/spectrum/<upload_id>', methods=['DELETE'])
@jwt_required()
def delete_spectrum(upload_id):
    """Delete spectrum upload."""
    try:
        user_id = get_jwt_identity()
        
        # Find spectrum upload
        from bson import ObjectId
        try:
            spectrum_upload = SpectrumUpload.find_by_id(ObjectId(upload_id))
        except:
            return jsonify({'message': 'Invalid upload ID'}), 400
            
        if not spectrum_upload:
            return jsonify({'message': 'Spectrum not found'}), 404
        
        # Check ownership
        if spectrum_upload.get('user_id') != user_id:
            return jsonify({'message': 'Access denied'}), 403
        
        # Delete file from filesystem
        import os
        try:
            if os.path.exists(spectrum_upload['file_path']):
                os.remove(spectrum_upload['file_path'])
        except OSError:
            pass  # File might already be deleted
        
        # Delete database record
        SpectrumUpload.delete_by_id(ObjectId(upload_id))
        
        log_system_event('INFO', f'Spectrum deleted: {spectrum_upload["original_filename"]}', 'upload', user_id)
        
        return jsonify({'message': 'Spectrum deleted successfully'}), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Spectrum deletion error: {str(e)}', 'upload')
        return jsonify({'message': 'Failed to delete spectrum'}), 500

@upload_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_spectrum():
    """Validate spectrum data format."""
    try:
        data = request.get_json()
        
        if 'spectrum_data' not in data:
            return jsonify({'message': 'Spectrum data is required'}), 400
        
        spectrum_data = data['spectrum_data']
        
        # Validate spectrum data
        try:
            validate_spectrum_data(spectrum_data)
            is_valid = True
            message = 'Spectrum data is valid'
        except ValueError as e:
            is_valid = False
            message = str(e)
        
        return jsonify({
            'is_valid': is_valid,
            'message': message
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Spectrum validation error: {str(e)}', 'upload')
        return jsonify({'message': 'Validation failed'}), 500
