const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');

// Get RFID reader status
router.get('/status', (req, res) => {
  try {
    const rfidService = req.app.locals.services.rfid;
    
    if (!rfidService) {
      return res.status(503).json({
        success: false,
        error: 'RFID service not available'
      });
    }

    const status = rfidService.getReaderInfo();
    
    res.json({
      success: true,
      data: status
    });
  } catch (error) {
    logger.error('Get RFID status error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to get RFID status'
    });
  }
});

// Get scan history
router.get('/history', (req, res) => {
  try {
    const rfidService = req.app.locals.services.rfid;
    
    if (!rfidService) {
      return res.status(503).json({
        success: false,
        error: 'RFID service not available'
      });
    }

    const history = rfidService.getScanHistory();
    
    res.json({
      success: true,
      data: history
    });
  } catch (error) {
    logger.error('Get scan history error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to get scan history'
    });
  }
});

// Manual scan (for testing)
router.post('/manual-scan', async (req, res) => {
  try {
    const { uid } = req.body;
    
    if (!uid) {
      return res.status(400).json({
        success: false,
        error: 'UID is required'
      });
    }

    const rfidService = req.app.locals.services.rfid;
    
    if (!rfidService) {
      return res.status(503).json({
        success: false,
        error: 'RFID service not available'
      });
    }

    if (!rfidService.mockMode) {
      return res.status(400).json({
        success: false,
        error: 'Manual scan only available in mock mode'
      });
    }

    await rfidService.simulateScan(uid);
    
    logger.logRfidEvent('Manual Scan Triggered', { uid });
    
    res.json({
      success: true,
      message: 'Manual scan triggered successfully',
      data: { uid }
    });
  } catch (error) {
    logger.error('Manual scan error:', error);
    
    res.status(500).json({
      success: false,
      error: error.message || 'Manual scan failed'
    });
  }
});

// Reconnect RFID reader
router.post('/reconnect', async (req, res) => {
  try {
    const rfidService = req.app.locals.services.rfid;
    
    if (!rfidService) {
      return res.status(503).json({
        success: false,
        error: 'RFID service not available'
      });
    }

    await rfidService.reconnect();
    
    logger.logSystemEvent('RFID Reader Reconnect Triggered');
    
    res.json({
      success: true,
      message: 'RFID reader reconnection initiated'
    });
  } catch (error) {
    logger.error('RFID reconnect error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to reconnect RFID reader'
    });
  }
});

module.exports = router;