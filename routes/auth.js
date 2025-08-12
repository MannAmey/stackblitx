const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');

// Admin login for RFID system
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({
        success: false,
        error: 'Username and password are required'
      });
    }

    const authService = req.app.locals.services.auth;
    
    const result = await authService.authenticateAdmin({ username, password });
    
    logger.logUserAction('RFID Admin Login', result.admin.id, {
      username: result.admin.username,
      cafeteria: process.env.CAFETERIA_NAME,
      station: process.env.STATION_ID
    });

    res.json({
      success: true,
      message: 'Authentication successful',
      data: result
    });
  } catch (error) {
    logger.error('RFID admin login error:', error);
    
    res.status(401).json({
      success: false,
      error: error.message || 'Authentication failed'
    });
  }
});

// Get current admin profile
router.get('/profile', async (req, res) => {
  try {
    const authService = req.app.locals.services.auth;
    const authMiddleware = authService.requireAuth();
    
    // Apply auth middleware
    authMiddleware(req, res, () => {
      res.json({
        success: true,
        data: {
          admin: req.admin,
          cafeteria: {
            name: process.env.CAFETERIA_NAME || 'School Cafeteria',
            location: process.env.CAFETERIA_LOCATION || 'Main Building',
            station: process.env.STATION_ID || 'STATION_001'
          },
          permissions: {
            canScan: true,
            canProcessPurchases: true,
            canViewReservations: true,
            canManageUsers: req.admin.permissions?.includes('users.write') || req.admin.role === 'super_admin'
          }
        }
      });
    });
  } catch (error) {
    logger.error('Get RFID admin profile error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to get profile'
    });
  }
});

// Logout
router.post('/logout', (req, res) => {
  logger.logUserAction('RFID Admin Logout', req.admin?.id || 'unknown');
  
  res.json({
    success: true,
    message: 'Logged out successfully'
  });
});

module.exports = router;