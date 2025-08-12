const MealReservation = require('../models/MealReservation');
const Food = require('../models/Food');
const User = require('../models/User');
const logger = require('../utils/logger');

class ReservationService {
  constructor() {
    // Direct database access
  }

  /**
   * Get today's reservations for a user
   */
  async getTodayReservations(userId) {
    try {
      logger.info('📅 Fetching today\'s reservations:', { userId });

      const today = new Date();
      const startOfDay = new Date(today.setHours(0, 0, 0, 0));
      const endOfDay = new Date(today.setHours(23, 59, 59, 999));

      // Direct database query
      const reservations = await MealReservation.find({
        studentId: userId,
        reservationDate: { $gte: startOfDay, $lte: endOfDay },
        status: { $in: ['pending', 'confirmed', 'prepared'] } // Exclude 'served' and 'cancelled'
      })
      .populate('foodId', 'name category price allergens ingredients')
      .populate('parentId', 'name email')
      .populate('studentId', 'name uid class_or_year user_category')
      .sort({ mealType: 1, reservationDate: 1 });

      logger.info('✅ Reservations fetched:', { 
        userId,
        count: reservations.length 
      });

      return reservations;
    } catch (error) {
      logger.error('Get today reservations error:', error);
      return [];
    }
  }

  /**
   * Confirm a reservation (mark as served and create purchase record)
   */
  async confirmReservation(reservationId, purchaseService) {
    try {
      logger.info('✅ Confirming reservation:', { reservationId });

      const reservation = await MealReservation.findById(reservationId)
        .populate('foodId', 'name category price')
        .populate('studentId', 'name uid class_or_year user_category')
        .populate('parentId', 'name email');

      if (!reservation) {
        throw new Error('Reservation not found');
      }

      if (reservation.status === 'served') {
        throw new Error('Reservation has already been served');
      }

      if (reservation.status === 'cancelled') {
        throw new Error('Cannot confirm a cancelled reservation');
      }

      // Mark as served
      await reservation.markServedByRFID(process.env.STATION_ID || 'STATION_001');

      // Create purchase record for the served reservation
      // ALWAYS create purchase record for served reservation
      let purchaseResult = null;
      try {
        const purchaseData = {
          userId: reservation.studentId._id,
          uid: reservation.studentId.uid,
          userName: reservation.studentId.name,
          userCategory: reservation.studentId.user_category || 'student',
          items: [{
            foodId: reservation.foodId._id,
            name: reservation.foodId.name,
            price: reservation.actualCost || reservation.estimatedCost,
            quantity: reservation.quantity,
            subtotal: (reservation.actualCost || reservation.estimatedCost) * reservation.quantity
          }],
          totalAmount: (reservation.actualCost || reservation.estimatedCost) * reservation.quantity,
          cafeteriaStation: process.env.STATION_ID || 'STATION_001',
          processedBy: 'rfid_reservation_system',
          notes: `Reservation fulfilled: ${reservation.mealType} meal on ${new Date().toLocaleDateString()}`,
          paymentStatus: 'pending' // Parent will see this in their purchase history for payment
        };

        if (purchaseService) {
          purchaseResult = await purchaseService.completePurchase(purchaseData);
        } else {
          // Fallback: create purchase directly if service not available
          const Purchase = require('../models/Purchase');
          const purchase = new Purchase(purchaseData);
          await purchase.save();
          purchaseResult = { success: true, purchase };
        }
        
        logger.info('✅ Purchase record created for served reservation:', { 
          reservationId,
          purchaseId: purchaseResult.purchase._id,
          amount: purchaseData.totalAmount,
          studentName: reservation.studentId.name,
          foodName: reservation.foodId.name
        });
      } catch (purchaseError) {
        logger.error('Failed to create purchase record for reservation:', purchaseError);
        // Still mark reservation as served, but log the purchase creation failure
        throw new Error(`Reservation served but failed to create purchase record: ${purchaseError.message}`);
      }
      logger.info('✅ Reservation confirmed successfully:', { reservationId });
      
      return {
        success: true,
        reservation: reservation,
        purchase: purchaseResult ? purchaseResult.purchase : null,
        message: `Reservation served and $${((reservation.actualCost || reservation.estimatedCost) * reservation.quantity).toFixed(2)} purchase recorded for payment`
      };
    } catch (error) {
      logger.error('Confirm reservation error:', error);
      throw new Error(error.message || 'Failed to confirm reservation');
    }
  }

  /**
   * Get reservation details by ID
   */
  async getReservationById(reservationId) {
    try {
      const reservation = await MealReservation.findById(reservationId)
        .populate('foodId', 'name category price allergens')
        .populate('studentId', 'name uid class_or_year user_category')
        .populate('parentId', 'name email');

      return reservation;
    } catch (error) {
      logger.error('Get reservation by ID error:', error);
      return null;
    }
  }

  /**
   * Get all reservations for a date range
   */
  async getReservations(params = {}) {
    try {
      let query = {};
      
      if (params.date) {
        const date = new Date(params.date);
        const startOfDay = new Date(date.setHours(0, 0, 0, 0));
        const endOfDay = new Date(date.setHours(23, 59, 59, 999));
        query.reservationDate = { $gte: startOfDay, $lte: endOfDay };
      }
      
      if (params.status) {
        query.status = params.status;
      }
      
      if (params.mealType) {
        query.mealType = params.mealType;
      }

      const reservations = await MealReservation.find(query)
        .populate('foodId', 'name category price')
        .populate('studentId', 'name uid class_or_year')
        .populate('parentId', 'name email')
        .sort({ reservationDate: 1, mealType: 1 });

      return reservations;
    } catch (error) {
      logger.error('Get reservations error:', error);
      return [];
    }
  }

  /**
   * Update reservation status
   */
  async updateReservationStatus(reservationId, status, notes = '') {
    try {
      const reservation = await MealReservation.findById(reservationId);
      
      if (!reservation) {
        throw new Error('Reservation not found');
      }

      reservation.status = status;
      reservation.notes = notes;
      
      if (status === 'served') {
        reservation.servedAt = new Date();
        reservation.rfidProcessedAt = new Date();
        reservation.servedByStation = process.env.STATION_ID || 'STATION_001';
      }
      
      await reservation.save();
      
      logger.info('✅ Reservation status updated:', { 
        reservationId, 
        status,
        station: process.env.STATION_ID 
      });
      
      return reservation;
    } catch (error) {
      logger.error('Update reservation status error:', error);
      throw error;
    }
  }

  /**
   * Get reservation statistics
   */
  async getReservationStats() {
    try {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);

      const totalReservations = await MealReservation.countDocuments();
      const todayReservations = await MealReservation.countDocuments({
        reservationDate: { $gte: today, $lt: tomorrow }
      });
      const pendingReservations = await MealReservation.countDocuments({ 
        status: 'pending',
        reservationDate: { $gte: today }
      });
      const servedToday = await MealReservation.countDocuments({
        reservationDate: { $gte: today, $lt: tomorrow },
        status: 'served'
      });

      return {
        totalReservations,
        todayReservations,
        pendingReservations,
        servedToday
      };
    } catch (error) {
      logger.error('Get reservation stats error:', error);
      return {
        totalReservations: 0,
        todayReservations: 0,
        pendingReservations: 0,
        servedToday: 0
      };
    }
  }

  /**
   * Get reservations by meal type for today
   */
  async getTodayReservationsByMealType() {
    try {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const tomorrow = new Date(today);
      tomorrow.setDate(tomorrow.getDate() + 1);

      const reservations = await MealReservation.aggregate([
        {
          $match: {
            reservationDate: { $gte: today, $lt: tomorrow },
            status: { $in: ['pending', 'confirmed', 'prepared'] }
          }
        },
        {
          $group: {
            _id: '$mealType',
            count: { $sum: '$quantity' },
            reservations: { $sum: 1 }
          }
        }
      ]);

      return reservations.reduce((acc, item) => {
        acc[item._id] = {
          count: item.count,
          reservations: item.reservations
        };
        return acc;
      }, {});
    } catch (error) {
      logger.error('Get reservations by meal type error:', error);
      return {};
    }
  }
}

module.exports = ReservationService;