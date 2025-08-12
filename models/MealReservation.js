const mongoose = require('mongoose');

const mealReservationSchema = new mongoose.Schema({
  parentId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Parent',
    required: true
  },
  studentId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  foodId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Food',
    required: true
  },
  reservationDate: {
    type: Date,
    required: true
  },
  quantity: {
    type: Number,
    required: true,
    min: 1,
    default: 1
  },
  mealType: {
    type: String,
    enum: ['breakfast', 'lunch', 'dinner', 'snack'],
    required: true,
    default: 'lunch'
  },
  specialInstructions: {
    type: String,
    trim: true,
    maxlength: 500,
    default: ''
  },
  status: {
    type: String,
    enum: ['pending', 'confirmed', 'prepared', 'served', 'cancelled'],
    default: 'pending'
  },
  estimatedCost: {
    type: Number,
    required: true,
    min: 0
  },
  actualCost: {
    type: Number,
    default: null
  },
  preparedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Admin',
    default: null
  },
  preparedAt: {
    type: Date,
    default: null
  },
  servedAt: {
    type: Date,
    default: null
  },
  notes: {
    type: String,
    trim: true,
    default: ''
  },
  allergyNotes: {
    type: String,
    trim: true,
    default: ''
  },
  isUrgent: {
    type: Boolean,
    default: false
  },
  // RFID-specific fields
  servedByStation: {
    type: String,
    default: ''
  },
  rfidProcessedAt: {
    type: Date,
    default: null
  }
}, {
  timestamps: true
});

// Index for better query performance
mealReservationSchema.index({ parentId: 1 });
mealReservationSchema.index({ studentId: 1 });
mealReservationSchema.index({ foodId: 1 });
mealReservationSchema.index({ reservationDate: 1 });
mealReservationSchema.index({ status: 1 });
mealReservationSchema.index({ mealType: 1 });

// Method to mark as served via RFID
mealReservationSchema.methods.markServedByRFID = function(stationId) {
  this.status = 'served';
  this.servedAt = new Date();
  this.rfidProcessedAt = new Date();
  this.servedByStation = stationId;
  return this.save();
};

module.exports = mongoose.model('MealReservation', mealReservationSchema);