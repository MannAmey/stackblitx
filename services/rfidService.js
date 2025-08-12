const { NFC } = require('nfc-pcsc');
const logger = require('../utils/logger');

class RFIDService {
  constructor(io, services = {}) {
    this.io = io;
    this.userService = services.userService;
    this.purchaseService = services.purchaseService;
    this.reservationService = services.reservationService;
    
    this.nfc = null;
    this.reader = null;
    this.connected = false;
    this.lastScanTime = null;
    this.scanHistory = [];
    this.mockMode = process.env.MOCK_RFID_READER === 'true';
    
    // ACR1252 USB Reader Configuration
    this.readerConfig = {
      readerName: process.env.RFID_READER_NAME || 'ACR1252',
      scanTimeout: parseInt(process.env.RFID_SCAN_TIMEOUT) || 5000,
      autoReconnect: process.env.RFID_AUTO_RECONNECT === 'true',
      beepOnScan: process.env.RFID_BEEP_ON_SCAN === 'true',
      autoProcessAID: false,
      autoProcessAll: false
    };
    
    this.initialize();
  }

  async initialize() {
    try {
      logger.info('🔧 Initializing RFID Service with nfc-pcsc...', {
        readerName: this.readerConfig.readerName,
        mockMode: this.mockMode,
        config: this.readerConfig
      });

      if (this.mockMode) {
        await this.initializeMockReader();
      } else {
        await this.initializeNFCReader();
      }
      
      logger.info('✅ RFID Service initialized successfully');
    } catch (error) {
      logger.error('❌ RFID Service initialization failed:', error);
      console.error('❌ RFID initialization error:', error);
      
      // Fall back to mock mode if hardware fails
      if (!this.mockMode) {
        logger.warn('🧪 Falling back to mock mode due to hardware failure');
        await this.initializeMockReader();
      }
    }
  }

  async initializeNFCReader() {
    try {
      logger.info('🔍 Initializing NFC-PCSC for ACR1252...');
      
      // Create NFC instance
      this.nfc = new NFC();

      // Handle reader connection
      this.nfc.on('reader', (reader) => {
        logger.info('📡 NFC Reader detected:', {
          name: reader.name,
          type: 'ACR1252 Compatible'
        });

        // Check if this is our target reader (ACR1252 or compatible)
        if (reader.name.toLowerCase().includes('acr') || 
            reader.name.toLowerCase().includes('1252') ||
            reader.name.toLowerCase().includes('nfc')) {
          
          this.reader = reader;
          this.connected = true;

          logger.info('✅ ACR1252 reader connected:', {
            readerName: reader.name
          });

          this.io.emit('rfidConnected', { 
            readerType: reader.name,
            connected: true,
            timestamp: new Date().toISOString()
          });

          // Handle card events
          this.setupCardHandlers(reader);
        }
      });

      // Handle NFC errors
      this.nfc.on('error', (error) => {
        logger.error('NFC-PCSC error:', error);
        this.connected = false;
        this.io.emit('rfidError', { 
          message: 'NFC reader error',
          error: error.message 
        });

        // Auto-reconnect if enabled
        if (this.readerConfig.autoReconnect) {
          setTimeout(() => this.reconnect(), 5000);
        }
      });

      logger.info('✅ NFC-PCSC initialized, waiting for reader...');

    } catch (error) {
      logger.error('NFC-PCSC initialization error:', error);
      throw error;
    }
  }

  setupCardHandlers(reader) {
    // Handle card insertion
    reader.on('card', async (card) => {
      try {
        logger.info('💳 Card detected:', {
          uid: card.uid,
          atr: card.atr.toString('hex'),
          type: card.type
        });

        // Process the card scan
        await this.processCardScan(card.uid);

      } catch (error) {
        logger.error('Card processing error:', error);
        this.io.emit('scanError', {
          message: 'Failed to process card',
          error: error.message
        });
      }
    });

    // Handle card removal
    reader.on('card.off', (card) => {
      logger.info('💳 Card removed:', { uid: card.uid });
    });

    // Handle reader errors
    reader.on('error', (error) => {
      logger.error('Reader error:', error);
      this.connected = false;
      this.io.emit('rfidError', { 
        message: 'Reader error occurred',
        error: error.message 
      });
    });

    // Handle reader disconnection
    reader.on('end', () => {
      logger.warn('📡 Reader disconnected');
      this.connected = false;
      this.reader = null;
      this.io.emit('rfidDisconnected', {
        timestamp: new Date().toISOString()
      });

      // Auto-reconnect if enabled
      if (this.readerConfig.autoReconnect) {
        setTimeout(() => this.reconnect(), 3000);
      }
    });
  }

  async initializeMockReader() {
    logger.info('🧪 Initializing mock RFID reader for development...');
    
    this.connected = true;
    this.reader = {
      mock: true,
      type: 'Mock ACR1252'
    };

    // Simulate reader connection
    setTimeout(() => {
      this.io.emit('rfidConnected', { 
        readerType: 'Mock ACR1252',
        connected: true,
        mockMode: true,
        timestamp: new Date().toISOString()
      });
    }, 1000);

    logger.info('✅ Mock RFID reader initialized');
  }

  async processCardScan(uid) {
    try {
      this.lastScanTime = new Date();
      
      // Convert UID to string if it's a buffer
      const uidString = Buffer.isBuffer(uid) ? uid.toString('hex').toUpperCase() : uid.toString().toUpperCase();
      
      // Add to scan history
      this.scanHistory.unshift({
        uid: uidString,
        timestamp: this.lastScanTime,
        processed: false
      });

      // Keep only last 100 scans
      if (this.scanHistory.length > 100) {
        this.scanHistory = this.scanHistory.slice(0, 100);
      }

      logger.info('🔍 Processing card scan:', { uid: uidString });

      // Emit scan event to all connected clients
      this.io.emit('cardScanned', {
        uid: uidString,
        timestamp: this.lastScanTime.toISOString(),
        status: 'processing'
      });

      // Look up user data directly from database
      const userData = await this.userService.getUserByUID(uidString);
      
      if (!userData) {
        logger.warn('👤 User not found for UID:', { uid: uidString });
        this.io.emit('scanResult', {
          uid: uidString,
          success: false,
          error: 'User not found',
          message: 'This card is not registered in the system',
          timestamp: new Date().toISOString()
        });
        return;
      }

      // Check if user can access system (not blocked)
      const accessCheck = await this.userService.validateUserAccess(userData);
      
      if (!accessCheck.canAccess) {
        logger.warn('🚫 User access denied:', { 
          uid: uidString, 
          name: userData.name,
          reason: accessCheck.reason
        });
        
        this.io.emit('scanResult', {
          uid: uidString,
          success: false,
          error: 'Access denied',
          message: accessCheck.message,
          user: {
            name: userData.name,
            uid: userData.uid,
            status: accessCheck.reason
          },
          timestamp: new Date().toISOString()
        });
        return;
      }

      // Get user reservations for today
      const reservations = await this.reservationService.getTodayReservations(userData._id);

      // Update scan history
      const scanIndex = this.scanHistory.findIndex(scan => scan.uid === uidString);
      if (scanIndex !== -1) {
        this.scanHistory[scanIndex].processed = true;
      }

      // Emit successful scan result
      this.io.emit('scanResult', {
        uid: uidString,
        success: true,
        user: {
          _id: userData._id,
          uid: userData.uid,
          name: userData.name,
          class_or_year: userData.class_or_year,
          user_category: userData.user_category,
          email: userData.email,
          gender: userData.gender,
          scanCount: userData.scanCount || 0,
          lastScanAt: userData.lastScanAt,
          isActive: userData.isActive,
          isBlocked: userData.isBlocked
        },
        reservations: reservations || [],
        timestamp: new Date().toISOString(),
        cafeteria: {
          name: process.env.CAFETERIA_NAME || 'School Cafeteria',
          station: process.env.STATION_ID || 'STATION_001'
        }
      });

      // Update user's last scan time in database
      await this.userService.updateLastScan(userData._id);

      logger.info('✅ Card scan processed successfully:', { 
        uid: uidString, 
        userName: userData.name,
        reservationCount: reservations ? reservations.length : 0
      });

    } catch (error) {
      logger.error('Card scan processing error:', error);
      
      this.io.emit('scanResult', {
        uid: uid.toString(),
        success: false,
        error: 'Processing error',
        message: 'Failed to process card scan',
        timestamp: new Date().toISOString()
      });
    }
  }

  async processManualScan(uid, socketId) {
    logger.info('🖱️ Processing manual scan:', { uid, socketId });
    await this.processCardScan(uid);
  }

  async reconnect() {
    try {
      logger.info('🔄 Attempting to reconnect NFC reader...');
      
      if (this.nfc) {
        this.nfc.close();
      }
      
      this.connected = false;
      this.reader = null;
      
      // Wait before reconnecting
      await this.delay(2000);
      
      if (this.mockMode) {
        await this.initializeMockReader();
      } else {
        await this.initializeNFCReader();
      }
      
    } catch (error) {
      logger.error('NFC reconnection failed:', error);
      
      // Try again in 10 seconds
      if (this.readerConfig.autoReconnect) {
        setTimeout(() => this.reconnect(), 10000);
      }
    }
  }

  disconnect() {
    try {
      logger.info('🔌 Disconnecting NFC reader...');
      
      if (this.nfc) {
        this.nfc.close();
      }
      
      this.connected = false;
      this.reader = null;
      this.nfc = null;
      
      this.io.emit('rfidDisconnected', {
        timestamp: new Date().toISOString()
      });
      
      logger.info('✅ NFC reader disconnected');
    } catch (error) {
      logger.error('NFC disconnection error:', error);
    }
  }

  isConnected() {
    return this.connected;
  }

  getLastScanTime() {
    return this.lastScanTime;
  }

  getScanHistory() {
    return this.scanHistory.slice(0, 50); // Return last 50 scans
  }

  getReaderInfo() {
    return {
      type: this.reader?.name || process.env.RFID_READER_TYPE || 'ACR1252',
      connected: this.connected,
      mockMode: this.mockMode,
      lastScan: this.lastScanTime,
      config: this.readerConfig,
      library: 'nfc-pcsc'
    };
  }

  // Utility method for delays
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Mock scanning for development/testing
  async simulateScan(uid) {
    if (!this.mockMode) {
      throw new Error('Simulate scan only available in mock mode');
    }
    
    logger.info('🧪 Simulating card scan:', { uid });
    await this.processCardScan(uid);
  }

  // Get connected readers list
  getConnectedReaders() {
    if (this.mockMode) {
      return [{
        name: 'Mock ACR1252',
        connected: true,
        type: 'mock'
      }];
    }

    if (this.reader) {
      return [{
        name: this.reader.name,
        connected: this.connected,
        type: 'nfc-pcsc'
      }];
    }

    return [];
  }

  // Send command to reader (for advanced operations)
  async sendCommand(command) {
    if (!this.reader || this.mockMode) {
      throw new Error('Reader not available or in mock mode');
    }

    try {
      const response = await this.reader.transmit(Buffer.from(command, 'hex'), 40);
      return response.toString('hex');
    } catch (error) {
      logger.error('Send command error:', error);
      throw error;
    }
  }

  // Get reader capabilities
  async getReaderCapabilities() {
    if (this.mockMode) {
      return {
        name: 'Mock ACR1252',
        capabilities: ['ISO14443A', 'ISO14443B', 'MIFARE', 'NTAG'],
        mock: true
      };
    }

    if (!this.reader) {
      return null;
    }

    return {
      name: this.reader.name,
      capabilities: ['ISO14443A', 'ISO14443B', 'MIFARE', 'NTAG', 'FeliCa'],
      library: 'nfc-pcsc',
      connected: this.connected
    };
  }
}

module.exports = RFIDService;