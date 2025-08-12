const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');

// Get today's reservations for a user
router.get('/user/:userId/today', async (req, res) => {
  try {
    const { userId } = req.params;
    const reservationService = req.app.locals.services.reservation;
    
    if (!reservationService) {
      return res.status(503).json({
        success: false,
        error: 'Reservation service not available'
      });
    }

    const reservations = await reservationService.getTodayReservations(userId);
    
    res.json({
      success: true,
      data: reservations
    });
  } catch (error) {
    logger.error('Get today reservations error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to get reservations'
    });
  }
});

// Confirm reservation (mark as served)
router.post('/:id/confirm', async (req, res) => {
  try {
    const { id } = req.params;
    const reservationService = req.app.locals.services.reservation;
    const purchaseService = req.app.locals.services.purchase;
    
    if (!reservationService) {
      return res.status(503).json({
        success: false,
        error: 'Reservation service not available'
      });
    }

    const result = await reservationService.confirmReservation(id, purchaseService);
    
    logger.logUserAction('Reservation Confirmed via RFID', result.reservation.studentId, {
      reservationId: id,
      cafeteria: process.env.CAFETERIA_NAME
    });

    res.json(result);
  } catch (error) {
    logger.error('Confirm reservation error:', error);
    
    res.status(400).json({
      success: false,
      error: error.message || 'Failed to confirm reservation'
    });
  }
});

// Get reservation details
router.get('/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const reservationService = req.app.locals.services.reservation;
    
    if (!reservationService) {
      return res.status(503).json({
        success: false,
        error: 'Reservation service not available'
      });
    }

    const reservation = await reservationService.getReservationById(id);
    
    if (!reservation) {
      return res.status(404).json({
        success: false,
        error: 'Reservation not found'
      });
    }

    res.json({
      success: true,
      data: reservation
    });
  } catch (error) {
    logger.error('Get reservation error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to get reservation'
    });
  }
});

module.exports = router;