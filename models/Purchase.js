const mongoose = require('mongoose');

const purchaseItemSchema = new mongoose.Schema({
  foodId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Food',
    required: true
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  price: {
    type: Number,
    required: true,
    min: 0
  },
  quantity: {
    type: Number,
    required: true,
    min: 1
  },
  subtotal: {
    type: Number,
    required: true,
    min: 0
  }
});

const purchaseSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  uid: {
    type: String,
    required: true,
    trim: true
  },
  userName: {
    type: String,
    required: true,
    trim: true
  },
  userCategory: {
    type: String,
    required: true,
    enum: ['staff', 'student']
  },
  items: [purchaseItemSchema],
  totalAmount: {
    type: Number,
    required: true,
    min: 0
  },
  purchasedAt: {
    type: Date,
    default: Date.now
  },
  paymentStatus: {
    type: String,
    enum: ['pending', 'paid', 'cancelled'],
    default: 'pending'
  },
  paidAt: {
    type: Date,
    default: null
  },
  paymentMethod: {
    type: String,
    enum: ['cash', 'monthly_billing'],
    default: 'monthly_billing'
  },
  cashAmount: {
    type: Number,
    default: null
  },
  change: {
    type: Number,
    default: null
  },
  notes: {
    type: String,
    trim: true,
    default: ''
  },
  // RFID-specific fields
  cafeteriaStation: {
    type: String,
    default: 'STATION_001'
  },
  processedBy: {
    type: String, // Admin username who processed
    default: ''
  }
}, {
  timestamps: true
});

// Index for better query performance
purchaseSchema.index({ userId: 1 });
purchaseSchema.index({ uid: 1 });
purchaseSchema.index({ purchasedAt: -1 });
purchaseSchema.index({ paymentStatus: 1 });
purchaseSchema.index({ paymentMethod: 1 });
purchaseSchema.index({ cafeteriaStation: 1 });

module.exports = mongoose.model('Purchase', purchaseSchema);