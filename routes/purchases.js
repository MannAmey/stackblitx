const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');

// Get available foods for purchase
router.get('/foods', async (req, res) => {
  try {
    const language = req.language || 'en';
    const purchaseService = req.app.locals.services.purchase;
    
    if (!purchaseService) {
      return res.status(503).json({
        success: false,
        error: req.t('systemError')
      });
    }

    const foods = await purchaseService.getAvailableFoods();
    
    res.json({
      success: true,
      data: foods
    });
  } catch (error) {
    logger.error('Get available foods error:', error);
    
    res.status(500).json({
      success: false,
      error: req.t('systemError')
    });
  }
});

// Complete purchase
router.post('/complete', async (req, res) => {
  try {
    const purchaseService = req.app.locals.services.purchase;
    
    if (!purchaseService) {
      return res.status(503).json({
        success: false,
        error: 'Purchase service not available'
      });
    }

    // Validate purchase data
    const { userId, items, totalAmount, paymentMethod, paidAmount } = req.body;
    
    if (!userId || !items || !Array.isArray(items) || items.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'Invalid purchase data'
      });
    }

    // Validate payment method
    if (!['cash', 'monthly_billing'].includes(paymentMethod)) {
      return res.status(400).json({
        success: false,
        error: 'Invalid payment method'
      });
    }

    // Validate items
    await purchaseService.validatePurchaseItems(items);

    // Calculate and verify total
    const calculatedTotal = purchaseService.calculateTotal(items);
    if (Math.abs(calculatedTotal - totalAmount) > 0.01) {
      return res.status(400).json({
        success: false,
        error: 'Total amount mismatch'
      });
    }

    // For cash payments, validate paid amount
    if (paymentMethod === 'cash') {
      if (!paidAmount || paidAmount < totalAmount) {
        return res.status(400).json({
          success: false,
          error: 'Insufficient cash amount'
        });
      }
    }

    const result = await purchaseService.completePurchase(req.body);
    
    logger.logPurchaseEvent('Purchase Completed', result.purchase, {
      cafeteria: process.env.CAFETERIA_NAME,
      station: process.env.STATION_ID,
      paymentMethod: paymentMethod
    });

    res.json(result);
  } catch (error) {
    logger.error('Complete purchase error:', error);
    
    res.status(400).json({
      success: false,
      error: error.message || 'Failed to complete purchase'
    });
  }
});

// Get user purchase history
router.get('/user/:userId', async (req, res) => {
  try {
    const { userId } = req.params;
    const { limit = 10 } = req.query;
    
    const purchaseService = req.app.locals.services.purchase;
    
    if (!purchaseService) {
      return res.status(503).json({
        success: false,
        error: 'Purchase service not available'
      });
    }

    const purchases = await purchaseService.getUserPurchases(userId, parseInt(limit));
    
    res.json({
      success: true,
      data: purchases
    });
  } catch (error) {
    logger.error('Get user purchases error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to get user purchases'
    });
  }
});

module.exports = router;