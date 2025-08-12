from flask import Blueprint, request, jsonify, current_app
import structlog

logger = structlog.get_logger()
purchases_bp = Blueprint('purchases', __name__)

@purchases_bp.route('/foods', methods=['GET'])
def get_foods():
    try:
        purchase_service = current_app.purchase_service
        
        if not purchase_service:
            return jsonify({
                'success': False,
                'error': 'Purchase service not available'
            }), 503
        
        foods = purchase_service.get_available_foods()
        
        return jsonify({
            'success': True,
            'data': foods
        })
    except Exception as e:
        logger.error("Get available foods error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': 'Failed to get available foods'
        }), 500

@purchases_bp.route('/complete', methods=['POST'])
def complete_purchase():
    try:
        purchase_service = current_app.purchase_service
        
        if not purchase_service:
            return jsonify({
                'success': False,
                'error': 'Purchase service not available'
            }), 503
        
        data = request.get_json()
        
        # Validate purchase data
        if not data.get('user_id') or not data.get('items') or not isinstance(data.get('items'), list) or len(data.get('items')) == 0:
            return jsonify({
                'success': False,
                'error': 'Invalid purchase data'
            }), 400
        
        # Validate payment method
        if data.get('payment_method') not in ['cash', 'monthly_billing']:
            return jsonify({
                'success': False,
                'error': 'Invalid payment method'
            }), 400
        
        # Validate items
        purchase_service.validate_purchase_items(data['items'])
        
        # Calculate and verify total
        calculated_total = purchase_service.calculate_total(data['items'])
        if abs(calculated_total - data.get('total_amount', 0)) > 0.01:
            return jsonify({
                'success': False,
                'error': 'Total amount mismatch'
            }), 400
        
        # For cash payments, validate paid amount
        if data.get('payment_method') == 'cash':
            if not data.get('paid_amount') or data.get('paid_amount') < data.get('total_amount', 0):
                return jsonify({
                    'success': False,
                    'error': 'Insufficient cash amount'
                }), 400
        
        result = purchase_service.complete_purchase(data)
        
        logger.info("Purchase Completed", 
                   purchase_id=result['purchase']['id'],
                   cafeteria=current_app.config.get('CAFETERIA_NAME'),
                   station=current_app.config.get('STATION_ID'),
                   payment_method=data.get('payment_method'))
        
        return jsonify(result)
    except Exception as e:
        logger.error("Complete purchase error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': str(e) or 'Failed to complete purchase'
        }), 400

@purchases_bp.route('/user/<user_id>', methods=['GET'])
def get_user_purchases(user_id):
    try:
        limit = int(request.args.get('limit', 10))
        
        purchase_service = current_app.purchase_service
        
        if not purchase_service:
            return jsonify({
                'success': False,
                'error': 'Purchase service not available'
            }), 503
        
        purchases = purchase_service.get_user_purchases(user_id, limit)
        
        return jsonify({
            'success': True,
            'data': purchases
        })
    except Exception as e:
        logger.error("Get user purchases error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': 'Failed to get user purchases'
        }), 500