import os
import threading
import time
from datetime import datetime
from collections import deque
import structlog

logger = structlog.get_logger()

# Try to import RFID libraries
try:
    from smartcard.System import readers
    from smartcard.util import toHexString
    SMARTCARD_AVAILABLE = True
except ImportError:
    SMARTCARD_AVAILABLE = False
    logger.warning("smartcard library not available, using mock mode")

class RFIDService:
    def __init__(self, socketio, services=None):
        self.socketio = socketio
        self.user_service = services.get('user_service') if services else None
        self.purchase_service = services.get('purchase_service') if services else None
        self.reservation_service = services.get('reservation_service') if services else None
        
        self.reader = None
        self.connection = None
        self.connected = False
        self.last_scan_time = None
        self.scan_history = deque(maxlen=100)
        self.mock_mode = os.getenv('MOCK_RFID_READER', 'false').lower() == 'true' or not SMARTCARD_AVAILABLE
        
        # ACR1252 USB Reader Configuration
        self.reader_config = {
            'reader_name': os.getenv('RFID_READER_NAME', 'ACR1252'),
            'scan_timeout': int(os.getenv('RFID_SCAN_TIMEOUT', '5000')),
            'auto_reconnect': os.getenv('RFID_AUTO_RECONNECT', 'true').lower() == 'true',
            'beep_on_scan': os.getenv('RFID_BEEP_ON_SCAN', 'true').lower() == 'true'
        }
        
        self.running = False
        self.scan_thread = None
        
        self.initialize()
    
    def initialize(self):
        """Initialize RFID Service"""
        try:
            logger.info("🔧 Initializing RFID Service", 
                       reader_name=self.reader_config['reader_name'],
                       mock_mode=self.mock_mode,
                       config=self.reader_config)
            
            if self.mock_mode:
                self.initialize_mock_reader()
            else:
                self.initialize_nfc_reader()
            
            logger.info("✅ RFID Service initialized successfully")
        except Exception as e:
            logger.error("❌ RFID Service initialization failed", error=str(e))
            
            # Fall back to mock mode if hardware fails
            if not self.mock_mode:
                logger.warning("🧪 Falling back to mock mode due to hardware failure")
                self.mock_mode = True
                self.initialize_mock_reader()
    
    def initialize_nfc_reader(self):
        """Initialize NFC reader using pyscard"""
        try:
            if not SMARTCARD_AVAILABLE:
                raise Exception("smartcard library not available")
            
            logger.info("🔍 Initializing pyscard for ACR1252...")
            
            # Get available readers
            reader_list = readers()
            
            if not reader_list:
                raise Exception("No card readers found")
            
            # Find ACR1252 or compatible reader
            target_reader = None
            for reader in reader_list:
                reader_name = str(reader).lower()
                if ('acr' in reader_name or '1252' in reader_name or 
                    'nfc' in reader_name or 'contactless' in reader_name):
                    target_reader = reader
                    break
            
            if not target_reader:
                # Use first available reader as fallback
                target_reader = reader_list[0]
                logger.warning("ACR1252 not found, using first available reader", 
                              reader=str(target_reader))
            
            self.reader = target_reader
            self.connection = target_reader.createConnection()
            self.connection.connect()
            self.connected = True
            
            logger.info("✅ NFC reader connected", reader_name=str(target_reader))
            
            # Start scanning thread
            self.start_scanning()
            
            # Emit connection event
            self.socketio.emit('rfidConnected', {
                'reader_type': str(target_reader),
                'connected': True,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error("NFC reader initialization error", error=str(e))
            raise e
    
    def initialize_mock_reader(self):
        """Initialize mock RFID reader for development"""
        logger.info("🧪 Initializing mock RFID reader for development...")
        
        self.connected = True
        self.reader = {'mock': True, 'type': 'Mock ACR1252'}
        
        # Simulate reader connection
        def emit_connected():
            time.sleep(1)
            self.socketio.emit('rfidConnected', {
                'reader_type': 'Mock ACR1252',
                'connected': True,
                'mock_mode': True,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        threading.Thread(target=emit_connected, daemon=True).start()
        logger.info("✅ Mock RFID reader initialized")
    
    def start_scanning(self):
        """Start the card scanning thread"""
        if self.mock_mode:
            return  # Mock mode doesn't need continuous scanning
        
        self.running = True
        self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.scan_thread.start()
        logger.info("🔄 RFID scanning thread started")
    
    def _scan_loop(self):
        """Main scanning loop for detecting cards"""
        while self.running and self.connected:
            try:
                if not self.connection:
                    time.sleep(1)
                    continue
                
                # Send APDU command to detect card presence
                # This is a simplified approach - in production you might want more sophisticated detection
                try:
                    # ATR (Answer To Reset) command to detect card
                    response, sw1, sw2 = self.connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
                    
                    if sw1 == 0x90 and sw2 == 0x00:  # Success
                        # Card detected, get UID
                        uid_response, uid_sw1, uid_sw2 = self.connection.transmit([0xFF, 0xCA, 0x00, 0x00, 0x00])
                        
                        if uid_sw1 == 0x90 and uid_sw2 == 0x00:
                            uid = ''.join([f'{b:02X}' for b in uid_response])
                            threading.Thread(target=self.process_card_scan, args=(uid,), daemon=True).start()
                            
                            # Wait a bit to avoid multiple reads of the same card
                            time.sleep(2)
                    
                except Exception as scan_error:
                    # No card present or other error - this is normal
                    pass
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error("Scanning loop error", error=str(e))
                if self.reader_config['auto_reconnect']:
                    self.reconnect()
                time.sleep(5)
    
    def process_card_scan(self, uid):
        """Process a card scan"""
        try:
            self.last_scan_time = datetime.utcnow()
            
            # Convert UID to string if needed
            uid_string = uid.upper() if isinstance(uid, str) else str(uid).upper()
            
            # Add to scan history
            self.scan_history.appendleft({
                'uid': uid_string,
                'timestamp': self.last_scan_time,
                'processed': False
            })
            
            logger.info("🔍 Processing card scan", uid=uid_string)
            
            # Emit scan event to all connected clients
            self.socketio.emit('cardScanned', {
                'uid': uid_string,
                'timestamp': self.last_scan_time.isoformat(),
                'status': 'processing'
            })
            
            # Look up user data
            if not self.user_service:
                logger.error("User service not available")
                return
            
            user_data = self.user_service.get_user_by_uid(uid_string)
            
            if not user_data:
                logger.warning("👤 User not found for UID", uid=uid_string)
                self.socketio.emit('scanResult', {
                    'uid': uid_string,
                    'success': False,
                    'error': 'User not found',
                    'message': 'This card is not registered in the system',
                    'timestamp': datetime.utcnow().isoformat()
                })
                return
            
            # Check if user can access system
            access_check = self.user_service.validate_user_access(user_data)
            
            if not access_check['can_access']:
                logger.warning("🚫 User access denied", 
                              uid=uid_string, name=user_data.name,
                              reason=access_check['reason'])
                
                self.socketio.emit('scanResult', {
                    'uid': uid_string,
                    'success': False,
                    'error': 'Access denied',
                    'message': access_check['message'],
                    'user': {
                        'name': user_data.name,
                        'uid': user_data.uid,
                        'status': access_check['reason']
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
                return
            
            # Get user reservations for today
            reservations = []
            if self.reservation_service:
                reservations = self.reservation_service.get_today_reservations(str(user_data.id))
            
            # Update scan history
            if self.scan_history and self.scan_history[0]['uid'] == uid_string:
                self.scan_history[0]['processed'] = True
            
            # Emit successful scan result
            self.socketio.emit('scanResult', {
                'uid': uid_string,
                'success': True,
                'user': user_data.to_dict(),
                'reservations': reservations or [],
                'timestamp': datetime.utcnow().isoformat(),
                'cafeteria': {
                    'name': os.getenv('CAFETERIA_NAME', 'School Cafeteria'),
                    'station': os.getenv('STATION_ID', 'STATION_001')
                }
            })
            
            # Update user's last scan time
            if self.user_service:
                self.user_service.update_last_scan(str(user_data.id))
            
            logger.info("✅ Card scan processed successfully", 
                       uid=uid_string, user_name=user_data.name,
                       reservation_count=len(reservations) if reservations else 0)
            
        except Exception as e:
            logger.error("Card scan processing error", error=str(e))
            
            self.socketio.emit('scanResult', {
                'uid': str(uid),
                'success': False,
                'error': 'Processing error',
                'message': 'Failed to process card scan',
                'timestamp': datetime.utcnow().isoformat()
            })
    
    def process_manual_scan(self, uid, socket_id=None):
        """Process manual scan (for testing)"""
        logger.info("🖱️ Processing manual scan", uid=uid, socket_id=socket_id)
        self.process_card_scan(uid)
    
    def reconnect(self):
        """Reconnect to RFID reader"""
        try:
            logger.info("🔄 Attempting to reconnect NFC reader...")
            
            self.disconnect()
            time.sleep(2)
            
            if self.mock_mode:
                self.initialize_mock_reader()
            else:
                self.initialize_nfc_reader()
            
        except Exception as e:
            logger.error("NFC reconnection failed", error=str(e))
            
            # Try again in 10 seconds
            if self.reader_config['auto_reconnect']:
                threading.Timer(10.0, self.reconnect).start()
    
    def disconnect(self):
        """Disconnect from RFID reader"""
        try:
            logger.info("🔌 Disconnecting NFC reader...")
            
            self.running = False
            
            if self.connection:
                self.connection.disconnect()
                self.connection = None
            
            self.connected = False
            self.reader = None
            
            self.socketio.emit('rfidDisconnected', {
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info("✅ NFC reader disconnected")
        except Exception as e:
            logger.error("NFC disconnection error", error=str(e))
    
    def is_connected(self):
        """Check if reader is connected"""
        return self.connected
    
    def get_last_scan_time(self):
        """Get last scan time"""
        return self.last_scan_time.isoformat() if self.last_scan_time else None
    
    def get_scan_history(self):
        """Get scan history"""
        return list(self.scan_history)[:50]  # Return last 50 scans
    
    def get_reader_info(self):
        """Get reader information"""
        return {
            'type': str(self.reader) if self.reader else os.getenv('RFID_READER_TYPE', 'ACR1252'),
            'connected': self.connected,
            'mock_mode': self.mock_mode,
            'last_scan': self.get_last_scan_time(),
            'config': self.reader_config,
            'library': 'pyscard' if not self.mock_mode else 'mock'
        }
    
    def simulate_scan(self, uid):
        """Simulate card scan for development/testing"""
        if not self.mock_mode:
            raise ValueError('Simulate scan only available in mock mode')
        
        logger.info("🧪 Simulating card scan", uid=uid)
        self.process_card_scan(uid)
    
    def get_connected_readers(self):
        """Get list of connected readers"""
        if self.mock_mode:
            return [{
                'name': 'Mock ACR1252',
                'connected': True,
                'type': 'mock'
            }]
        
        if self.reader:
            return [{
                'name': str(self.reader),
                'connected': self.connected,
                'type': 'pyscard'
            }]
        
        return []
    
    def get_reader_capabilities(self):
        """Get reader capabilities"""
        if self.mock_mode:
            return {
                'name': 'Mock ACR1252',
                'capabilities': ['ISO14443A', 'ISO14443B', 'MIFARE', 'NTAG'],
                'mock': True
            }
        
        if not self.reader:
            return None
        
        return {
            'name': str(self.reader),
            'capabilities': ['ISO14443A', 'ISO14443B', 'MIFARE', 'NTAG', 'FeliCa'],
            'library': 'pyscard',
            'connected': self.connected
        }