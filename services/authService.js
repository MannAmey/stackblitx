const jwt = require('jsonwebtoken');
const logger = require('../utils/logger');

class AuthService {
  constructor() {
    this.jwtSecret = process.env.JWT_SECRET || 'rfid-server-secret';
    this.jwtExpiresIn = process.env.JWT_EXPIRES_IN || '8h';
  }

  /**
   * Authenticate admin user with database
   */
  async authenticateAdmin(credentials) {
    try {
      logger.info('🔐 Authenticating admin for RFID system:', { 
        username: credentials.username
      });

      // For now, we'll use a simple admin validation
      // In production, you might want to connect to the admin database
      // or create a dedicated RFID admin system
      
      const validAdmins = [
        { 
          username: 'admin', 
          password: 'admin123',
          name: 'RFID Administrator',
          role: 'rfid_admin',
          permissions: ['rfid.read', 'rfid.write', 'users.read', 'purchases.write']
        },
        {
          username: 'cafeteria',
          password: 'cafeteria123', 
          name: 'Cafeteria Staff',
          role: 'cafeteria_staff',
          permissions: ['rfid.read', 'rfid.write', 'purchases.write']
        }
      ];
      
      const admin = validAdmins.find(a => 
        a.username === credentials.username && 
        a.password === credentials.password
      );

      if (!admin) {
        throw new Error('Invalid credentials');
      }

      // Generate RFID server specific token
      const rfidToken = this.generateRfidToken(admin);

      logger.info('✅ Admin authenticated successfully:', { 
        username: admin.username,
        role: admin.role 
      });

      return {
        success: true,
        admin: {
          id: admin.username, // Use username as ID for simplicity
          username: admin.username,
          name: admin.name,
          role: admin.role,
          permissions: admin.permissions
        },
        token: rfidToken
      };
    } catch (error) {
      logger.error('Admin authentication error:', error);
      throw new Error(error.message || 'Authentication failed');
    }
  }

  /**
   * Check if admin has RFID permissions
   */
  hasRfidPermissions(admin) {
    // RFID admin and cafeteria staff have permissions
    if (admin.role === 'rfid_admin' || admin.role === 'cafeteria_staff') {
      return true;
    }

    // Check for specific RFID permissions
    const requiredPermissions = ['rfid.read', 'rfid.write'];
    const hasPermissions = requiredPermissions.some(permission => 
      admin.permissions && admin.permissions.includes(permission)
    );


    return hasPermissions;
  }

  /**
   * Generate RFID server specific JWT token
   */
  generateRfidToken(admin) {
    const payload = {
      id: admin.username,
      username: admin.username,
      role: admin.role,
      permissions: admin.permissions,
      system: 'rfid_server',
      cafeteria: process.env.CAFETERIA_NAME || 'School Cafeteria',
      station: process.env.STATION_ID || 'STATION_001'
    };

    return jwt.sign(payload, this.jwtSecret, {
      expiresIn: this.jwtExpiresIn
    });
  }

  /**
   * Verify RFID server token
   */
  verifyToken(token) {
    try {
      const decoded = jwt.verify(token, this.jwtSecret);
      
      if (decoded.system !== 'rfid_server') {
        throw new Error('Invalid token system');
      }

      return decoded;
    } catch (error) {
      logger.error('Token verification error:', error);
      throw new Error('Invalid or expired token');
    }
  }

  /**
   * Middleware for protecting RFID routes
   */
  requireAuth() {
    return (req, res, next) => {
      try {
        const authHeader = req.header('Authorization');
        const token = authHeader && authHeader.startsWith('Bearer ') 
          ? authHeader.slice(7) 
          : null;

        if (!token) {
          return res.status(401).json({
            success: false,
            error: 'Access denied. No token provided.'
          });
        }

        const decoded = this.verifyToken(token);
        req.admin = decoded;
        
        logger.debug('🔐 Admin authenticated for RFID access:', { 
          adminId: decoded.id,
          username: decoded.username 
        });
        
        next();
      } catch (error) {
        logger.error('Auth middleware error:', error);
        
        return res.status(401).json({
          success: false,
          error: error.message || 'Invalid token'
        });
      }
    };
  }

}

module.exports = AuthService;