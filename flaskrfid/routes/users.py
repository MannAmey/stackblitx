from flask import Blueprint, request, jsonify, current_app
import structlog

logger = structlog.get_logger()
users_bp = Blueprint('users', __name__)

@users_bp.route('/uid/<uid>', methods=['GET'])
def get_user_by_uid(uid):
    try:
        user_service = current_app.user_service
        
        if not user_service:
            return jsonify({
                'success': False,
                'error': 'User service not available'
            }), 503
        
        user_data = user_service.get_user_for_rfid_display(uid)
        
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user_data['user'].to_dict(),
            'access_check': user_data['access_check'],
            'display_data': user_data['display_data']
        })
    except Exception as e:
        logger.error("Get user by UID error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': str(e) or 'Failed to get user'
        }), 500

@users_bp.route('/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    try:
        user_service = current_app.user_service
        
        if not user_service:
            return jsonify({
                'success': False,
                'error': 'User service not available'
            }), 503
        
        user = user_service.get_user_by_id(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        })
    except Exception as e:
        logger.error("Get user by ID error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': str(e) or 'Failed to get user'
        }), 500

@users_bp.route('/search', methods=['GET'])
def search_users():
    try:
        query = request.args.get('q')
        
        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'Search query must be at least 2 characters'
            }), 400
        
        user_service = current_app.user_service
        
        if not user_service:
            return jsonify({
                'success': False,
                'error': 'User service not available'
            }), 503
        
        users = user_service.search_users(query)
        
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users]
        })
    except Exception as e:
        logger.error("Search users error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': 'Failed to search users'
        }), 500

@users_bp.route('/register', methods=['POST'])
def register_user():
    try:
        user_service = current_app.user_service
        
        if not user_service:
            return jsonify({
                'success': False,
                'error': 'User service not available'
            }), 503
        
        data = request.get_json()
        user = user_service.create_user(data)
        
        logger.info("User Created via RFID", 
                   user_id=str(user.id), name=user.name, uid=user.uid,
                   cafeteria=current_app.config.get('CAFETERIA_NAME'))
        
        return jsonify({
            'success': True,
            'message': 'User created successfully',
            'data': user.to_dict()
        }), 201
    except Exception as e:
        logger.error("Create user error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': str(e) or 'Failed to create user'
        }), 400