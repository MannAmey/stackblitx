const Purchase = require('../models/Purchase');
const Food = require('../models/Food');
const User = require('../models/User');
const logger = require('../utils/logger');

class PurchaseService {
  constructor() {
    // Direct database access
  }

  /**
   * Get available foods for purchase
   */
  async getAvailableFoods() {
    try {
      logger.info('🍽️ Fetching available foods...');

      // Direct database query
      const foods = await Food.find({ 
        isActive: true, 
        isAvailable: true 
      }).sort({ category: 1, name: 1 });

      // Group by category
      const groupedFoods = foods.reduce((acc, food) => {
        if (!acc[food.category]) {
          acc[food.category] = [];
        }
        acc[food.category].push(food);
        return acc;
      }, {});

      logger.info('✅ Available foods fetched:', { 
        categories: Object.keys(groupedFoods).length,
        totalFoods: foods.length
      });
      
      return groupedFoods;
    } catch (error) {
      logger.error('Get available foods error:', error);
      return {};
    }
  }

  /**
   * Complete a purchase transaction
   */
  async completePurchase(purchaseData) {
    try {
      logger.info('💳 Processing purchase:', { 
        userId: purchaseData.userId,
        itemCount: purchaseData.items.length,
        totalAmount: purchaseData.totalAmount,
        paymentMethod: purchaseData.paymentMethod
      });

      // Validate purchase data
      if (!purchaseData.userId || !purchaseData.items || purchaseData.items.length === 0) {
        throw new Error('Invalid purchase data');
      }

      // Ensure userCategory is provided with fallback
      const userCategory = purchaseData.userCategory || 'student';

      // Determine payment status based on payment method
      let paymentStatus = 'pending';
      let paidAt = null;
      let notes = purchaseData.notes || '';
      let cashAmount = null;
      let change = null;
      
      if (purchaseData.paymentMethod === 'cash') {
        paymentStatus = 'paid';
        paidAt = new Date();
        cashAmount = purchaseData.paidAmount;
        notes += ` | Cash payment: €${purchaseData.paidAmount.toFixed(2)}`;
        if (purchaseData.paidAmount > purchaseData.totalAmount) {
          change = purchaseData.paidAmount - purchaseData.totalAmount;
          notes += ` | Change: €${change.toFixed(2)}`;
        }
      } else if (purchaseData.paymentMethod === 'monthly_billing') {
        paymentStatus = 'pending';
        notes += ' | Added to monthly bill - parent will be charged';
      }

      // Create purchase record
      const purchase = new Purchase({
        userId: purchaseData.userId,
        uid: purchaseData.uid,
        userName: purchaseData.userName,
        userCategory: userCategory,
        items: purchaseData.items,
        totalAmount: purchaseData.totalAmount,
        cafeteriaStation: purchaseData.cafeteriaStation || process.env.STATION_ID || 'STATION_001',
        purchasedAt: new Date(),
        paymentStatus: paymentStatus,
        paidAt: paidAt,
        paymentMethod: purchaseData.paymentMethod,
        cashAmount: cashAmount,
        change: change,
        notes: notes,
        processedBy: purchaseData.processedBy || 'rfid_system'
      });

      await purchase.save();

      // Update user's last scan time
      await User.findByIdAndUpdate(purchaseData.userId, {
        lastScanAt: new Date(),
        $inc: { scanCount: 1 }
      });
      
      logger.info('✅ Purchase completed successfully:', { 
        purchaseId: purchase._id,
        userId: purchase.userId,
        totalAmount: purchase.totalAmount,
        paymentMethod: purchaseData.paymentMethod,
        paymentStatus: paymentStatus,
        source: purchaseData.processedBy || 'rfid_system'
      });

      return {
        success: true,
        purchase: purchase,
        message: purchaseData.paymentMethod === 'cash' 
          ? 'Cash payment completed successfully'
          : 'Purchase added to monthly bill',
        paymentMethod: purchaseData.paymentMethod,
        change: purchaseData.paymentMethod === 'cash' && purchaseData.paidAmount > purchaseData.totalAmount
          ? purchaseData.paidAmount - purchaseData.totalAmount
          : 0
      };
    } catch (error) {
      logger.error('Purchase completion error:', error);
      
      if (error.name === 'ValidationError') {
        const messages = Object.values(error.errors).map(err => err.message);
        throw new Error(messages.join(', '));
      }
      
      throw new Error(error.message || 'Purchase failed');
    }
  }

  /**
   * Validate purchase items against available foods
   */
  async validatePurchaseItems(items) {
    try {
      for (const item of items) {
        const food = await Food.findById(item.foodId);
        
        if (!food) {
          throw new Error(`Food item not found: ${item.name}`);
        }
        
        if (!food.isAvailable || !food.isActive) {
          throw new Error(`Food item not available: ${food.name}`);
        }
        
        if (Math.abs(item.price - food.price) > 0.01) {
          throw new Error(`Price mismatch for ${food.name}. Expected: $${food.price}, Got: $${item.price}`);
        }
      }
      
      return true;
    } catch (error) {
      logger.error('Purchase validation error:', error);
      throw error;
    }
  }

  /**
   * Calculate purchase total
   */
  calculateTotal(items) {
    return items.reduce((total, item) => {
      return total + (item.price * item.quantity);
    }, 0);
  }

  /**
   * Get purchase history for a user
   */
  async getUserPurchases(userId, limit = 10) {
    try {
      const purchases = await Purchase.find({ userId })
        .populate('items.foodId', 'name category')
        .sort({ purchasedAt: -1 })
        .limit(limit);

      return purchases;
    } catch (error) {
      logger.error('Get user purchases error:', error);
      return [];
    }
  }

  /**
   * Get purchase statistics
   */
  async getPurchaseStats() {
    try {
      const totalPurchases = await Purchase.countDocuments();
      const totalRevenue = await Purchase.aggregate([
        { $group: { _id: null, total: { $sum: '$totalAmount' } } }
      ]);
      
      const todayStart = new Date();
      todayStart.setHours(0, 0, 0, 0);
      const todayPurchases = await Purchase.countDocuments({
        purchasedAt: { $gte: todayStart }
      });
      
      const todayRevenue = await Purchase.aggregate([
        { $match: { purchasedAt: { $gte: todayStart } } },
        { $group: { _id: null, total: { $sum: '$totalAmount' } } }
      ]);

      return {
        totalPurchases,
        totalRevenue: totalRevenue[0]?.total || 0,
        todayPurchases,
        todayRevenue: todayRevenue[0]?.total || 0
      };
    } catch (error) {
      logger.error('Get purchase stats error:', error);
      return {
        totalPurchases: 0,
        totalRevenue: 0,
        todayPurchases: 0,
        todayRevenue: 0
      };
    }
  }

  /**
   * Get food by ID with full details
   */
  async getFoodById(foodId) {
    try {
      const food = await Food.findById(foodId);
      return food;
    } catch (error) {
      logger.error('Get food by ID error:', error);
      return null;
    }
  }
}

module.exports = PurchaseService;