import os
import logging
from datetime import timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_babel import Babel
from dotenv import load_dotenv
import structlog

# Load environment variables
load_dotenv()

# Import services and models
from services.rfid_service import RFIDService
from services.auth_service import AuthService
from services.user_service import UserService
from services.purchase_service import PurchaseService
from services.reservation_service import ReservationService
from database.connection import init_db
from utils.logger import setup_logging
from utils.i18n import init_babel

# Import routes
from routes.auth import auth_bp
from routes.rfid import rfid_bp
from routes.users import users_bp
from routes.purchases import purchases_bp
from routes.reservations import reservations_bp

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'rfid-server-secret-key')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'rfid-jwt-secret')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=8)
    app.config['MONGODB_URI'] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/rfid_system')
    
    # CORS configuration
    allowed_origins = [
        os.getenv('RFID_FRONTEND_URL', 'http://localhost:5175'),
        os.getenv('ADMIN_FRONTEND_URL', 'http://localhost:5173'),
        os.getenv('PARENT_FRONTEND_URL', 'http://localhost:5174'),
        'http://localhost:3000'  # Development fallback
    ]
    
    # Initialize extensions
    CORS(app, origins=allowed_origins, supports_credentials=True)
    jwt = JWTManager(app)
    
    # Rate limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per minute"]
    )
    
    # Socket.IO
    socketio = SocketIO(
        app,
        cors_allowed_origins=allowed_origins,
        async_mode='threading'
    )
    
    # Internationalization
    babel = Babel(app)
    init_babel(app, babel)
    
    # Setup logging
    setup_logging()
    logger = structlog.get_logger()
    
    # Initialize database
    try:
        init_db(app.config['MONGODB_URI'])
        logger.info("✅ Connected to MongoDB", database=app.config['MONGODB_URI'].split('/')[-1])
    except Exception as e:
        logger.error("❌ MongoDB connection error", error=str(e))
        raise
    
    # Initialize services
    try:
        auth_service = AuthService()
        user_service = UserService()
        purchase_service = PurchaseService()
        reservation_service = ReservationService()
        rfid_service = RFIDService(socketio, {
            'user_service': user_service,
            'purchase_service': purchase_service,
            'reservation_service': reservation_service
        })
        
        # Store services in app context
        app.auth_service = auth_service
        app.user_service = user_service
        app.purchase_service = purchase_service
        app.reservation_service = reservation_service
        app.rfid_service = rfid_service
        app.socketio = socketio
        
        logger.info("✅ All services initialized successfully")
    except Exception as e:
        logger.error("❌ Failed to initialize services", error=str(e))
        raise
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(rfid_bp, url_prefix='/api/rfid')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(purchases_bp, url_prefix='/api/purchases')
    app.register_blueprint(reservations_bp, url_prefix='/api/reservations')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'timestamp': structlog.get_logger().info("Health check"),
            'version': '1.0.0',
            'environment': os.getenv('FLASK_ENV', 'development'),
            'mongodb': 'connected',  # We'll enhance this with actual connection check
            'cafeteria': {
                'name': os.getenv('CAFETERIA_NAME', 'School Cafeteria'),
                'location': os.getenv('CAFETERIA_LOCATION', 'Main Building'),
                'station_id': os.getenv('STATION_ID', 'STATION_001')
            },
            'rfid': {
                'reader_type': os.getenv('RFID_READER_TYPE', 'ACR1252'),
                'connected': rfid_service.is_connected() if 'rfid_service' in locals() else False,
                'mock_mode': os.getenv('MOCK_RFID_READER', 'false').lower() == 'true'
            },
            'features': [
                'rfid_scanning',
                'user_lookup',
                'purchase_processing',
                'reservation_display',
                'real_time_updates',
                'admin_authentication',
                'direct_database_access',
                'multilingual_support',
                'payment_processing',
                'cash_payments',
                'monthly_billing'
            ],
            'languages': ['en', 'de'],
            'payment_methods': ['cash', 'monthly_billing']
        })
    
    # Socket.IO event handlers
    @socketio.on('connect')
    def handle_connect():
        logger.info("🔌 RFID Client connected", socket_id=request.sid)
        emit('connected', {
            'message': 'Connected to RFID Server',
            'timestamp': structlog.get_logger().info("Client connected"),
            'cafeteria': {
                'name': os.getenv('CAFETERIA_NAME', 'School Cafeteria'),
                'location': os.getenv('CAFETERIA_LOCATION', 'Main Building')
            },
            'features': ['rfid_scanning', 'purchase_processing', 'reservation_display']
        })
        
        # Send RFID reader status
        if hasattr(app, 'rfid_service'):
            emit('rfidStatus', {
                'connected': app.rfid_service.is_connected(),
                'reader_type': os.getenv('RFID_READER_TYPE', 'ACR1252'),
                'mock_mode': os.getenv('MOCK_RFID_READER', 'false').lower() == 'true'
            })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        logger.info("🔌 RFID Client disconnected", socket_id=request.sid)
    
    @socketio.on('requestRfidStatus')
    def handle_rfid_status_request():
        if hasattr(app, 'rfid_service'):
            emit('rfidStatus', {
                'connected': app.rfid_service.is_connected(),
                'reader_type': os.getenv('RFID_READER_TYPE', 'ACR1252'),
                'mock_mode': os.getenv('MOCK_RFID_READER', 'false').lower() == 'true',
                'last_scan': app.rfid_service.get_last_scan_time()
            })
    
    @socketio.on('manualScan')
    def handle_manual_scan(data):
        try:
            if hasattr(app, 'rfid_service'):
                app.rfid_service.process_manual_scan(data.get('uid'), request.sid)
        except Exception as e:
            logger.error("Manual scan error", error=str(e))
            emit('scanError', {
                'message': 'Failed to process manual scan',
                'error': str(e)
            })
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Route not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error("Internal server error", error=str(error))
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    
    port = int(os.getenv('PORT', 3003))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚀 RFID Server running on port {port}")
    print(f"🏫 Cafeteria: {os.getenv('CAFETERIA_NAME', 'School Cafeteria')}")
    print(f"📡 RFID Reader: {os.getenv('RFID_READER_TYPE', 'ACR1252')}")
    print(f"🌐 Frontend: {os.getenv('RFID_FRONTEND_URL', 'http://localhost:5175')}")
    
    if os.getenv('MOCK_RFID_READER', 'false').lower() == 'true':
        print('🧪 Running in MOCK mode (no physical RFID reader required)')
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)