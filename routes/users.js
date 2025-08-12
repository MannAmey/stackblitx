const express = require('express');
const router = express.Router();
const logger = require('../utils/logger');

// Get user by UID
router.get('/uid/:uid', async (req, res) => {
  try {
    const { uid } = req.params;
    const userService = req.app.locals.services.user;
    
    if (!userService) {
      return res.status(503).json({
        success: false,
        error: 'User service not available'
      });
    }

    const userData = await userService.getUserForRFIDDisplay(uid);
    
    if (!userData) {
      return res.status(404).json({
        success: false,
        error: 'User not found'
      });
    }

    res.json({
      success: true,
      data: userData.user,
      accessCheck: userData.accessCheck,
      displayData: userData.displayData
    });
  } catch (error) {
    logger.error('Get user by UID error:', error);
    
    res.status(500).json({
      success: false,
      error: error.message || 'Failed to get user'
    });
  }
});
// Get user by ID (for purchase flow fallback)
router.get("/:id", async (req, res) => {
  try {
    const { id } = req.params
    const userService = req.app.locals.services.user

    if (!userService) {
      return res.status(503).json({
        success: false,
        error: "User service not available",
      })
    }

    const user = await userService.getUserById(id)

    if (!user) {
      return res.status(404).json({
        success: false,
        error: "User not found",
      })
    }

    res.json({
      success: true,
      data: user,
    })
  } catch (error) {
    logger.error("Get user by ID error:", error)
    res.status(500).json({
      success: false,
      error: error.message || "Failed to get user",
    })
  }
})

// Search users
router.get('/search', async (req, res) => {
  try {
    const { q } = req.query;
    
    if (!q || q.length < 2) {
      return res.status(400).json({
        success: false,
        error: 'Search query must be at least 2 characters'
      });
    }

    const userService = req.app.locals.services.user;
    
    if (!userService) {
      return res.status(503).json({
        success: false,
        error: 'User service not available'
      });
    }

    const users = await userService.searchUsers(q);
    
    res.json({
      success: true,
      data: users
    });
  } catch (error) {
    logger.error('Search users error:', error);
    
    res.status(500).json({
      success: false,
      error: 'Failed to search users'
    });
  }
});

// Create new user (for unregistered cards)
router.post('/register', async (req, res) => {
  try {
    const userService = req.app.locals.services.user;
    
    if (!userService) {
      return res.status(503).json({
        success: false,
        error: 'User service not available'
      });
    }

    const user = await userService.createUser(req.body);
    
    logger.logUserAction('User Created via RFID', user._id, {
      name: user.name,
      uid: user.uid,
      cafeteria: process.env.CAFETERIA_NAME
    });

    res.status(201).json({
      success: true,
      message: 'User created successfully',
      data: user
    });
  } catch (error) {
    logger.error('Create user error:', error);
    
    res.status(400).json({
      success: false,
      error: error.message || 'Failed to create user'
    });
  }
});

module.exports = router;