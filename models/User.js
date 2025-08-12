const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
  uid: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    index: true
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  class_or_year: {
    type: String,
    required: true,
    trim: true
  },
  user_category: {
    type: String,
    required: true,
    enum: ['staff', 'student'],
    lowercase: true
  },
  email: {
    type: String,
    required: true,
    unique: true,
    trim: true,
    lowercase: true,
    match: [/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/, 'Please enter a valid email']
  },
  gender: {
    type: String,
    required: true,
    enum: ['male', 'female', 'other'],
    lowercase: true
  },
  isActive: {
    type: Boolean,
    default: true
  },
  lastScanAt: {
    type: Date,
    default: null
  },
  scanCount: {
    type: Number,
    default: 0
  },
  // Blocking system
  isBlocked: {
    type: Boolean,
    default: false
  },
  blockInfo: {
    reason: {
      type: String,
      trim: true,
      default: ''
    },
    notes: {
      type: String,
      trim: true,
      default: ''
    },
    blockedAt: {
      type: Date,
      default: null
    },
    blockedBy: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'Admin',
      default: null
    },
    expiresAt: {
      type: Date,
      default: null
    },
    autoUnblockProcessed: {
      type: Boolean,
      default: false
    }
  }
}, {
  timestamps: true
});

// Index for better query performance
userSchema.index({ uid: 1 });
userSchema.index({ email: 1 });
userSchema.index({ user_category: 1 });
userSchema.index({ createdAt: -1 });

// Method to update last scan
userSchema.methods.updateLastScan = function() {
  this.lastScanAt = new Date();
  this.scanCount += 1;
  return this.save();
};

// Method to check if user can access system
userSchema.methods.canAccess = function() {
  if (!this.isActive) return false;
  if (!this.isBlocked) return true;
  
  // Check if block has expired
  if (this.blockInfo.expiresAt && new Date() > this.blockInfo.expiresAt) {
    return false; // Will be handled by middleware
  }
  
  return false;
};

module.exports = mongoose.model('User', userSchema);