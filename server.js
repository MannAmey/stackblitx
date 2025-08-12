const express = require('express');
const http = require('http');
const socketIO = require('socket.io');
const mongoose = require('mongoose');
const cors = require('cors');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const path = require('path');
const i18next = require('./utils/i18n');
const middleware = require('i18next-http-middleware');
require('dotenv').config();

// Import models to register schemas
require('./models/User');
require('./models/Food');
require('./models/Purchase');
require('./models/MealReservation');
require('./models/Parent');

// Import services
const RFIDService = require('./services/rfidService');
const AuthService = require('./services/authService');
const UserService = require('./services/userService');
const PurchaseService = require('./services/purchaseService');
const ReservationService = require('./services/reservationService');
const logger = require('./utils/logger');

// Import routes
const authRoutes = require('./routes/auth');
const rfidRoutes = require('./routes/rfid');
const userRoutes = require('./routes/users');
const purchaseRoutes = require('./routes/purchases');
const reservationRoutes = require('./routes/reservations');

const app = express();
const server = http.createServer(app);

// Define allowed origins for CORS
const allowedOrigins = [
  process.env.RFID_FRONTEND_URL || "http://localhost:5175",
  process.env.ADMIN_FRONTEND_URL || "http://localhost:5173",
  process.env.PARENT_FRONTEND_URL || "http://localhost:5174",
  "http://localhost:3000", // Development fallback
];

// Socket.IO configuration
const io = socketIO(server, {
  cors: {
    origin(origin, callback) {
      if (!origin) return callback(null, true) // allow Electron packaged app
      if (allowedOrigins.includes(origin)) return callback(null, true)
      logger.warn(`Socket.IO CORS blocked origin: ${origin}`)
      return callback(new Error('Not allowed by CORS'))
    },
    methods: ["GET", "POST", "PUT", "DELETE", "PATCH"],
    credentials: true
  }
})

// Security middleware
app.use(helmet({
  crossOriginResourcePolicy: { policy: "cross-origin" }
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 60000, // 1 minute
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100,
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});
app.use('/api/', limiter);

// CORS configuration
app.use(cors({
  origin: function (origin, callback) {
    if (!origin) return callback(null, true);
    
    if (allowedOrigins.indexOf(origin) !== -1) {
      callback(null, true);
    } else {
      logger.warn(`CORS blocked origin: ${origin}`);
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

// Body parsing middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// i18n middleware
app.use(middleware.handle(i18next));

// Database connection
const MONGODB_URI = process.env.MONGODB_URI || 'mongodb://localhost:27017/rfid_system';

mongoose.connect(MONGODB_URI, {
  useNewUrlParser: true,
  useUnifiedTopology: true,
})
.then(() => {
  logger.info('✅ Connected to MongoDB', { 
    database: MONGODB_URI.split('/').pop(),
    timestamp: new Date().toISOString()
  });
})
.catch((error) => {
  logger.error('❌ MongoDB connection error', { 
    error: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString()
  });
  process.exit(1);
});

// MongoDB connection event handlers
mongoose.connection.on('disconnected', () => {
  logger.warn('MongoDB disconnected');
});

mongoose.connection.on('reconnected', () => {
  logger.info('MongoDB reconnected');
});

// Initialize services
let rfidService;
let authService;
let userService;
let purchaseService;
let reservationService;

try {
  // Initialize services with dependencies
  authService = new AuthService();
  userService = new UserService();
  purchaseService = new PurchaseService();
  reservationService = new ReservationService();
  
  // Initialize RFID service with socket.io
  rfidService = new RFIDService(io, {
    userService,
    purchaseService,
    reservationService
  });
  
  logger.info('✅ All services initialized successfully');
} catch (error) {
  logger.error('❌ Failed to initialize services:', error);
  console.error('❌ Service initialization failed:', error);
}

// Make services available to routes
app.locals.services = {
  rfid: rfidService,
  auth: authService,
  user: userService,
  purchase: purchaseService,
  reservation: reservationService
};

// Make io available to routes
app.set('io', io);

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/rfid', rfidRoutes);
app.use('/api/users', userRoutes);
app.use('/api/purchases', purchaseRoutes);
app.use('/api/reservations', reservationRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
  const healthData = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development',
    mongodb: mongoose.connection.readyState === 1 ? 'connected' : 'disconnected',
    cafeteria: {
      name: process.env.CAFETERIA_NAME || 'School Cafeteria',
      location: process.env.CAFETERIA_LOCATION || 'Main Building',
      stationId: process.env.STATION_ID || 'STATION_001'
    },
    rfid: {
      readerType: process.env.RFID_READER_TYPE || 'ACR1252',
      connected: rfidService ? rfidService.isConnected() : false,
      mockMode: process.env.MOCK_RFID_READER === 'true'
    },
    features: [
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
    languages: ['en', 'de'],
    paymentMethods: ['cash', 'monthly_billing'],
    operatingHours: {
      start: process.env.OPERATING_START_TIME || '07:00',
      end: process.env.OPERATING_END_TIME || '15:00'
    }
  };

  res.json(healthData);
});

// WebSocket connection handling
io.on('connection', (socket) => {
  logger.info('🔌 RFID Client connected', { 
    socketId: socket.id,
    ip: socket.handshake.address,
    timestamp: new Date().toISOString()
  });

  // Send initial connection data
  socket.emit('connected', {
    message: 'Connected to RFID Server',
    timestamp: new Date().toISOString(),
    cafeteria: {
      name: process.env.CAFETERIA_NAME || 'School Cafeteria',
      location: process.env.CAFETERIA_LOCATION || 'Main Building'
    },
    features: ['rfid_scanning', 'purchase_processing', 'reservation_display']
  });

  // Send RFID reader status
  if (rfidService) {
    socket.emit('rfidStatus', {
      connected: rfidService.isConnected(),
      readerType: process.env.RFID_READER_TYPE || 'ACR1252',
      mockMode: process.env.MOCK_RFID_READER === 'true'
    });
  }

  // Handle client requests
  socket.on('requestRfidStatus', () => {
    if (rfidService) {
      socket.emit('rfidStatus', {
        connected: rfidService.isConnected(),
        readerType: process.env.RFID_READER_TYPE || 'ACR1252',
        mockMode: process.env.MOCK_RFID_READER === 'true',
        lastScan: rfidService.getLastScanTime()
      });
    }
  });

  // Handle manual card scan (for testing)
  socket.on('manualScan', async (data) => {
    try {
      if (rfidService) {
        await rfidService.processManualScan(data.uid, socket.id);
      }
    } catch (error) {
      logger.error('Manual scan error:', error);
      socket.emit('scanError', { 
        message: 'Failed to process manual scan',
        error: error.message 
      });
    }
  });

  // Handle purchase completion
  socket.on('completePurchase', async (data) => {
    try {
      if (purchaseService) {
        const result = await purchaseService.completePurchase(data);
        socket.emit('purchaseCompleted', result);
        
        // Notify other systems
        io.emit('purchaseUpdate', {
          type: 'purchase_completed',
          data: result,
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      logger.error('Purchase completion error:', error);
      socket.emit('purchaseError', { 
        message: 'Failed to complete purchase',
        error: error.message 
      });
    }
  });

  // Handle reservation confirmation
  socket.on('confirmReservation', async (data) => {
    try {
      if (reservationService) {
        const result = await reservationService.confirmReservation(data.reservationId, purchaseService);
        socket.emit('reservationConfirmed', result);
        
        // Notify other systems
        io.emit('reservationUpdate', {
          type: 'reservation_confirmed',
          data: result,
          timestamp: new Date().toISOString()
        });
      }
    } catch (error) {
      logger.error('Reservation confirmation error:', error);
      socket.emit('reservationError', { 
        message: 'Failed to confirm reservation',
        error: error.message 
      });
    }
  });

  socket.on('disconnect', (reason) => {
    logger.info('🔌 RFID Client disconnected', { 
      socketId: socket.id,
      reason,
      timestamp: new Date().toISOString()
    });
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  logger.error('Express error:', {
    error: err.message,
    stack: err.stack,
    url: req.originalUrl,
    method: req.method
  });

  res.status(500).json({
    success: false,
    error: 'Internal server error',
    timestamp: new Date().toISOString()
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({
    success: false,
    error: 'Route not found',
    timestamp: new Date().toISOString()
  });
});

const PORT = process.env.PORT || 3003;

server.listen(PORT, () => {
  logger.info('🚀 RFID Server Started', {
    port: PORT,
    environment: process.env.NODE_ENV || 'development',
    cafeteria: process.env.CAFETERIA_NAME || 'School Cafeteria',
    rfidReader: process.env.RFID_READER_TYPE || 'ACR1252',
    mockMode: process.env.MOCK_RFID_READER === 'true',
    timestamp: new Date().toISOString()
  });
  
  console.log(`🚀 RFID Server running on port ${PORT}`);
  console.log(`🏫 Cafeteria: ${process.env.CAFETERIA_NAME || 'School Cafeteria'}`);
  console.log(`📡 RFID Reader: ${process.env.RFID_READER_TYPE || 'ACR1252'}`);
  console.log(`🌐 Frontend: ${process.env.RFID_FRONTEND_URL || 'http://localhost:5175'}`);
  console.log(`🔗 Main API: ${process.env.MAIN_API_URL || 'http://localhost:3001/api'}`);
  console.log(`🔗 Admin API: ${process.env.ADMIN_API_URL || 'http://localhost:3002/api'}`);
  
  if (process.env.MOCK_RFID_READER === 'true') {
    console.log('🧪 Running in MOCK mode (no physical RFID reader required)');
  }
});

// Graceful shutdown
process.on('SIGINT', () => {
  logger.info('🛑 Shutting down RFID server gracefully...');
  
  if (rfidService) {
    rfidService.disconnect();
  }
  
  mongoose.connection.close();
  server.close(() => {
    logger.info('✅ RFID server closed');
    process.exit(0);
  });
});

module.exports = { app, io };