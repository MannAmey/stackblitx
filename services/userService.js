const User = require('../models/User');
const logger = require('../utils/logger');

class UserService {
  constructor() {
    // Direct database access - no API calls needed
  }

  /**
   * Get user by UID from database
   */
  async getUserByUID(uid) {
    try {
      logger.info('👤 Looking up user by UID:', { uid });

      // Direct database query
      const user = await User.findOne({ uid, isActive: true });

      if (user) {
        logger.info('✅ User found:', { 
          uid: user.uid,
          name: user.name,
          category: user.user_category,
          isActive: user.isActive,
          isBlocked: user.isBlocked
        });

        return user;
      }
      
      logger.warn('❌ User not found for UID:', { uid });
      return null;
    } catch (error) {
      logger.error('User lookup error:', {
        uid,
        error: error.message,
        stack: error.stack
      });

      return null;
    }
  }

  /**
   * Get user by ID (for purchase flow)
   */
  async getUserById(userId) {
    try {
      logger.info('👤 Looking up user by ID:', { userId });

      const user = await User.findById(userId);

      if (user) {
        logger.info('✅ User found by ID:', { 
          userId: user._id,
          uid: user.uid,
          name: user.name,
          category: user.user_category
        });

        return user;
      }
      
      logger.warn('❌ User not found for ID:', { userId });
      return null;
    } catch (error) {
      logger.error('User lookup by ID error:', {
        userId,
        error: error.message,
        stack: error.stack
      });

      return null;
    }
  }

  /**
   * Update user's last scan time
   */
  async updateLastScan(userId) {
    try {
      logger.info('📝 Updating last scan time:', { userId });

      // Direct database update
      const user = await User.findById(userId);
      if (user) {
        await user.updateLastScan();
        logger.info('✅ Last scan time updated successfully');
        return true;
      }

      return false;
    } catch (error) {
      logger.error('Update last scan error:', error);
      return false;
    }
  }

  /**
   * Search users by name or UID
   */
  async searchUsers(query) {
    try {
      const users = await User.find({
        isActive: true,
        $or: [
          { name: { $regex: query, $options: 'i' } },
          { uid: { $regex: query, $options: 'i' } },
          { email: { $regex: query, $options: 'i' } }
        ]
      }).limit(20);

      return users;
    } catch (error) {
      logger.error('User search error:', error);
      return [];
    }
  }

  /**
   * Check if user can access system (not blocked)
   */
  async validateUserAccess(user) {
    try {
      if (!user.isActive) {
        return { 
          canAccess: false, 
          reason: 'Account is inactive',
          message: 'This account has been deactivated. Please contact administration.'
        };
      }

      if (user.isBlocked) {
        // Check if block has expired
        if (user.blockInfo.expiresAt && new Date() > user.blockInfo.expiresAt) {
          // Auto-unblock expired blocks
          user.isBlocked = false;
          user.blockInfo = {
            reason: '',
            notes: '',
            blockedAt: null,
            blockedBy: null,
            expiresAt: null,
            autoUnblockProcessed: false
          };
          await user.save();
          
          logger.info('✅ Auto-unblocked expired user:', { userId: user._id, uid: user.uid });
          return { canAccess: true };
        }
        
        return { 
          canAccess: false, 
          reason: 'Account is blocked',
          message: user.blockInfo.reason || 'This account has been temporarily blocked.',
          expiresAt: user.blockInfo.expiresAt
        };
      }

      return { canAccess: true };
    } catch (error) {
      logger.error('User access validation error:', error);
      return { 
        canAccess: false, 
        reason: 'System error',
        message: 'Unable to validate account access. Please try again.'
      };
    }
  }

  /**
   * Get user with populated data for RFID display
   */
  async getUserForRFIDDisplay(uid) {
    try {
      const user = await this.getUserByUID(uid);
      if (!user) {
        return null;
      }

      // Validate access
      const accessCheck = await this.validateUserAccess(user);
      
      return {
        user,
        accessCheck,
        displayData: {
          name: user.name,
          class_or_year: user.class_or_year,
          user_category: user.user_category,
          uid: user.uid,
          scanCount: user.scanCount || 0,
          lastScanAt: user.lastScanAt,
          status: accessCheck.canAccess ? 'active' : 'blocked'
        }
      };
    } catch (error) {
      logger.error('Get user for RFID display error:', error);
      return null;
    }
  }

  /**
   * Create new user (for unregistered cards)
   */
  async createUser(userData) {
    try {
      logger.info('👤 Creating new user:', { uid: userData.uid, name: userData.name });

      const user = new User({
        uid: userData.uid,
        name: userData.name.trim(),
        class_or_year: userData.class_or_year.trim(),
        user_category: userData.user_category.toLowerCase(),
        email: userData.email.toLowerCase().trim(),
        gender: userData.gender.toLowerCase()
      });

      await user.save();
      
      logger.info('✅ User created successfully:', { 
        userId: user._id,
        name: user.name,
        uid: user.uid
      });
      
      return user;
    } catch (error) {
      logger.error('User creation error:', error);
      
      if (error.code === 11000) {
        const field = Object.keys(error.keyPattern)[0];
        throw new Error(`User with this ${field} already exists`);
      }
      
      if (error.name === 'ValidationError') {
        const messages = Object.values(error.errors).map(err => err.message);
        throw new Error(messages.join(', '));
      }
      
      throw new Error(error.message || 'Failed to create user');
    }
  }

  /**
   * Get user statistics for dashboard
   */
  async getUserStats() {
    try {
      const totalUsers = await User.countDocuments({ isActive: true });
      const totalStudents = await User.countDocuments({ user_category: 'student', isActive: true });
      const totalStaff = await User.countDocuments({ user_category: 'staff', isActive: true });
      const blockedUsers = await User.countDocuments({ isBlocked: true, isActive: true });
      
      const todayStart = new Date();
      todayStart.setHours(0, 0, 0, 0);
      const todayScans = await User.countDocuments({
        lastScanAt: { $gte: todayStart },
        isActive: true
      });

      return {
        totalUsers,
        totalStudents,
        totalStaff,
        blockedUsers,
        todayScans
      };
    } catch (error) {
      logger.error('Get user stats error:', error);
      return {
        totalUsers: 0,
        totalStudents: 0,
        totalStaff: 0,
        blockedUsers: 0,
        todayScans: 0
      };
    }
  }

  /**
   * Get recent user activity
   */
  async getRecentActivity(limit = 10) {
    try {
      const recentScans = await User.find({ 
        lastScanAt: { $exists: true },
        isActive: true 
      })
      .sort({ lastScanAt: -1 })
      .limit(limit)
      .select('name uid class_or_year user_category lastScanAt scanCount');

      return recentScans;
    } catch (error) {
      logger.error('Get recent activity error:', error);
      return [];
    }
  }
}

module.exports = UserService;