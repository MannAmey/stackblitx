from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
import structlog

logger = structlog.get_logger()
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        auth_service = current_app.auth_service
        result = auth_service.authenticate_admin(data)
        
        logger.info("RFID Admin Login", 
                   admin_id=result['admin']['id'],
                   username=result['admin']['username'],
                   cafeteria=current_app.config.get('CAFETERIA_NAME'),
                   station=current_app.config.get('STATION_ID'))
        
        return jsonify({
            'success': True,
            'message': 'Authentication successful',
            'data': result
        })
    except Exception as e:
        logger.error("RFID admin login error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': str(e) or 'Authentication failed'
        }), 401

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        current_user = get_jwt_identity()
        claims = get_jwt()
        
        return jsonify({
            'success': True,
            'data': {
                'admin': {
                    'id': current_user,
                    'username': claims.get('username'),
                    'name': claims.get('username', '').title(),
                    'role': claims.get('role'),
                    'permissions': claims.get('permissions', [])
                },
                'cafeteria': {
                    'name': claims.get('cafeteria', 'School Cafeteria'),
                    'location': current_app.config.get('CAFETERIA_LOCATION', 'Main Building'),
                    'station': claims.get('station', 'STATION_001')
                },
                'permissions': {
                    'can_scan': True,
                    'can_process_purchases': True,
                    'can_view_reservations': True,
                    'can_manage_users': 'users.write' in claims.get('permissions', []) or claims.get('role') == 'super_admin'
                }
            }
        })
    except Exception as e:
        logger.error("Get RFID admin profile error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': 'Failed to get profile'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    current_user = get_jwt_identity()
    logger.info("RFID Admin Logout", admin_id=current_user)
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })