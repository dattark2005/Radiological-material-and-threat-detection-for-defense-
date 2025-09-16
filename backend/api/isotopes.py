from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from models.database import IsotopeReference, mongo
from utils.logger import log_system_event

isotopes_bp = Blueprint('isotopes', __name__)

@isotopes_bp.route('/database', methods=['GET'])
@jwt_required()
def get_isotope_database():
    """Get isotope reference database."""
    try:
        # Get search and filter parameters
        search = request.args.get('search', '').strip()
        threat_level = request.args.get('threat_level')
        isotope_type = request.args.get('type')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Limit per_page
        per_page = min(per_page, 100)
        
        # Build query
        query = IsotopeReference.query
        
        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    IsotopeReference.symbol.ilike(f'%{search}%'),
                    IsotopeReference.name.ilike(f'%{search}%'),
                    IsotopeReference.description.ilike(f'%{search}%')
                )
            )
        
        # Apply threat level filter
        if threat_level:
            query = query.filter_by(threat_level=threat_level)
        
        # Apply isotope type filter
        if isotope_type:
            query = query.filter_by(isotope_type=isotope_type)
        
        # Execute query with pagination
        isotopes = query.order_by(IsotopeReference.symbol).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'isotopes': [isotope.to_dict() for isotope in isotopes.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': isotopes.total,
                'pages': isotopes.pages,
                'has_next': isotopes.has_next,
                'has_prev': isotopes.has_prev
            }
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Isotope database error: {str(e)}', 'isotopes')
        return jsonify({'message': 'Failed to fetch isotope database'}), 500

@isotopes_bp.route('/isotope/<isotope_id>', methods=['GET'])
@jwt_required()
def get_isotope_details(isotope_id):
    """Get detailed information about specific isotope."""
    try:
        isotope = IsotopeReference.query.get(isotope_id)
        if not isotope:
            return jsonify({'message': 'Isotope not found'}), 404
        
        return jsonify({'isotope': isotope.to_dict()}), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Isotope details error: {str(e)}', 'isotopes')
        return jsonify({'message': 'Failed to get isotope details'}), 500

@isotopes_bp.route('/search', methods=['POST'])
@jwt_required()
def search_isotopes():
    """Search isotopes by various criteria."""
    try:
        data = request.get_json()
        
        # Search by gamma peaks
        if 'gamma_peaks' in data:
            peaks = data['gamma_peaks']
            tolerance = data.get('tolerance', 5.0)  # keV tolerance
            
            matching_isotopes = []
            all_isotopes = IsotopeReference.query.all()
            
            for isotope in all_isotopes:
                if isotope.gamma_peaks:
                    matches = 0
                    for search_peak in peaks:
                        for ref_peak in isotope.gamma_peaks:
                            if abs(search_peak - ref_peak) <= tolerance:
                                matches += 1
                                break
                    
                    if matches > 0:
                        match_score = matches / len(peaks)
                        matching_isotopes.append({
                            'isotope': isotope.to_dict(),
                            'match_score': match_score,
                            'matched_peaks': matches
                        })
            
            # Sort by match score
            matching_isotopes.sort(key=lambda x: x['match_score'], reverse=True)
            
            return jsonify({
                'matches': matching_isotopes[:20],  # Top 20 matches
                'search_criteria': {
                    'gamma_peaks': peaks,
                    'tolerance': tolerance
                }
            }), 200
        
        # Text search
        elif 'query' in data:
            query_text = data['query'].strip()
            
            isotopes = IsotopeReference.query.filter(
                or_(
                    IsotopeReference.symbol.ilike(f'%{query_text}%'),
                    IsotopeReference.name.ilike(f'%{query_text}%'),
                    IsotopeReference.description.ilike(f'%{query_text}%'),
                    IsotopeReference.common_uses.ilike(f'%{query_text}%')
                )
            ).limit(20).all()
            
            return jsonify({
                'isotopes': [isotope.to_dict() for isotope in isotopes],
                'search_query': query_text
            }), 200
        
        else:
            return jsonify({'message': 'Search criteria required'}), 400
        
    except Exception as e:
        log_system_event('ERROR', f'Isotope search error: {str(e)}', 'isotopes')
        return jsonify({'message': 'Search failed'}), 500

@isotopes_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_isotope_categories():
    """Get isotope categories and statistics."""
    try:
        from sqlalchemy import func
        
        # Get threat level distribution
        threat_distribution = db.session.query(
            IsotopeReference.threat_level,
            func.count(IsotopeReference.id).label('count')
        ).group_by(IsotopeReference.threat_level).all()
        
        # Get isotope type distribution
        type_distribution = db.session.query(
            IsotopeReference.isotope_type,
            func.count(IsotopeReference.id).label('count')
        ).group_by(IsotopeReference.isotope_type).all()
        
        return jsonify({
            'threat_levels': {level: count for level, count in threat_distribution},
            'isotope_types': {itype: count for itype, count in type_distribution},
            'total_isotopes': IsotopeReference.query.count()
        }), 200
        
    except Exception as e:
        log_system_event('ERROR', f'Isotope categories error: {str(e)}', 'isotopes')
        return jsonify({'message': 'Failed to get categories'}), 500
