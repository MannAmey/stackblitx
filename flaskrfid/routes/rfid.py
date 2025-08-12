from flask import Blueprint, request, jsonify, current_app
import structlog

logger = structlog.get_logger()
rfid_bp = Blueprint('rfid', __name__)

@rfid_bp.route('/status', methods=['GET'])
def get_status():
    try:
        rfid_service = current_app.rfid_service
        
        if not rfid_service:
            return jsonify({
                'success': False,
                'error': 'RFID service not available'
            }), 503
        
        status = rfid_service.get_reader_info()
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error("Get RFID status error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': 'Failed to get RFID status'
        }), 500

@rfid_bp.route('/history', methods=['GET'])
def get_history():
    try:
        rfid_service = current_app.rfid_service
        
        if not rfid_service:
            return jsonify({
                'success': False,
                'error': 'RFID service not available'
            }), 503
        
        history = rfid_service.get_scan_history()
        
        return jsonify({
            'success': True,
            'data': history
        })
    except Exception as e:
        logger.error("Get scan history error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': 'Failed to get scan history'
        }), 500

@rfid_bp.route('/manual-scan', methods=['POST'])
def manual_scan():
    try:
        data = request.get_json()
        
        if not data or not data.get('uid'):
            return jsonify({
                'success': False,
                'error': 'UID is required'
            }), 400
        
        rfid_service = current_app.rfid_service
        
        if not rfid_service:
            return jsonify({
                'success': False,
                'error': 'RFID service not available'
            }), 503
        
        if not rfid_service.mock_mode:
            return jsonify({
                'success': False,
                'error': 'Manual scan only available in mock mode'
            }), 400
        
        rfid_service.simulate_scan(data['uid'])
        
        logger.info("Manual Scan Triggered", uid=data['uid'])
        
        return jsonify({
            'success': True,
            'message': 'Manual scan triggered successfully',
            'data': {'uid': data['uid']}
        })
    except Exception as e:
        logger.error("Manual scan error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': str(e) or 'Manual scan failed'
        }), 500

@rfid_bp.route('/reconnect', methods=['POST'])
def reconnect():
    try:
        rfid_service = current_app.rfid_service
        
        if not rfid_service:
            return jsonify({
                'success': False,
                'error': 'RFID service not available'
            }), 503
        
        rfid_service.reconnect()
        
        logger.info("RFID Reader Reconnect Triggered")
        
        return jsonify({
            'success': True,
            'message': 'RFID reader reconnection initiated'
        })
    except Exception as e:
        logger.error("RFID reconnect error", error=str(e))
        
        return jsonify({
            'success': False,
            'error': 'Failed to reconnect RFID reader'
        }), 500