from flask import Blueprint, request, jsonify, current_app
import structlog

logger = structlog.get_logger()
reservations_bp = Blueprint('reservations', __name__)

@reservations_bp.route('/user/<user_id>/today', methods=['GET'])
def get_today_reservations(user_id):
    try:
        reservation_service = current_app.reservation_service
        
        if not reservation_service:
            return jsonify({
                'success': False,
                'error': 'Reservation service not available'
            }), 503
        
        reservations = reservation_service.get_today_reservations(user_id)
        
        return jsonify({
            'success': True,
            'data': reservations
        })
    except Exception as e:
        logger.error("Get today reservations error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': 'Failed to get reservations'
        }), 500

@reservations_bp.route('/<reservation_id>/confirm', methods=['POST'])
def confirm_reservation(reservation_id):
    try:
        reservation_service = current_app.reservation_service
        purchase_service = current_app.purchase_service
        
        if not reservation_service:
            return jsonify({
                'success': False,
                'error': 'Reservation service not available'
            }), 503
        
        result = reservation_service.confirm_reservation(reservation_id, purchase_service)
        
        logger.info("Reservation Confirmed via RFID", 
                   student_id=result['reservation']['student_id'],
                   reservation_id=reservation_id,
                   cafeteria=current_app.config.get('CAFETERIA_NAME'))
        
        return jsonify(result)
    except Exception as e:
        logger.error("Confirm reservation error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': str(e) or 'Failed to confirm reservation'
        }), 400

@reservations_bp.route('/<reservation_id>', methods=['GET'])
def get_reservation(reservation_id):
    try:
        reservation_service = current_app.reservation_service
        
        if not reservation_service:
            return jsonify({
                'success': False,
                'error': 'Reservation service not available'
            }), 503
        
        reservation = reservation_service.get_reservation_by_id(reservation_id)
        
        if not reservation:
            return jsonify({
                'success': False,
                'error': 'Reservation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': reservation
        })
    except Exception as e:
        logger.error("Get reservation error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': 'Failed to get reservation'
        }), 500