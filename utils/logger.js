const winston = require('winston');
const path = require('path');
const fs = require('fs');

// Create logs directory if it doesn't exist
const logDir = path.join(__dirname, '../logs');
if (!fs.existsSync(logDir)) {
  fs.mkdirSync(logDir, { recursive: true });
}

// Define log levels
const levels = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  debug: 4,
};

// Define colors for each level
const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'white',
};

// Tell winston that you want to link the colors
winston.addColors(colors);

// Define which level to log based on environment
const level = () => {
  const env = process.env.NODE_ENV || 'development';
  const isDevelopment = env === 'development';
  return isDevelopment ? 'debug' : 'warn';
};

// Define format for logs
const logFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

// Define format for console logs
const consoleFormat = winston.format.combine(
  winston.format.colorize({ all: true }),
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  winston.format.errors({ stack: true }),
  winston.format.printf(
    (info) => `${info.timestamp} ${info.level}: ${info.message}${info.stack ? '\n' + info.stack : ''}`
  )
);

// Define transports
const transports = [
  // Console transport
  new winston.transports.Console({
    level: level(),
    format: consoleFormat,
  }),

  // File transport for all logs
  new winston.transports.File({
    filename: path.join(logDir, 'rfid-server.log'),
    level: 'info',
    format: logFormat,
    maxsize: 5242880, // 5MB
    maxFiles: 5,
  }),

  // Error log file
  new winston.transports.File({
    filename: path.join(logDir, 'error.log'),
    level: 'error',
    format: logFormat,
    maxsize: 5242880, // 5MB
    maxFiles: 3,
  }),
];

// Create the logger
const logger = winston.createLogger({
  level: level(),
  levels,
  format: logFormat,
  transports,
  exitOnError: false,
});

// Add custom methods for specific logging scenarios
logger.logRfidEvent = (event, details = {}) => {
  logger.info('RFID Event', {
    event,
    details,
    timestamp: new Date().toISOString(),
    type: 'RFID_EVENT'
  });
};

logger.logUserAction = (action, userId, details = {}) => {
  logger.info('User Action', {
    action,
    userId,
    details,
    timestamp: new Date().toISOString(),
    type: 'USER_ACTION'
  });
};

logger.logSystemEvent = (event, details = {}) => {
  logger.info('System Event', {
    event,
    details,
    timestamp: new Date().toISOString(),
    type: 'SYSTEM_EVENT'
  });
};

logger.logPurchaseEvent = (event, purchaseData, details = {}) => {
  logger.info('Purchase Event', {
    event,
    purchaseData,
    details,
    timestamp: new Date().toISOString(),
    type: 'PURCHASE_EVENT'
  });
};

module.exports = logger;