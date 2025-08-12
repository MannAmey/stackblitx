const mongoose = require("mongoose")
const bcrypt = require("bcryptjs")

const parentSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true,
      trim: true,
    },
    email: {
      type: String,
      required: true,
      unique: true,
      trim: true,
      lowercase: true,
      match: [/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/, "Please enter a valid email"],
    },
    password: {
      type: String,
      required: true,
      minlength: 6,
    },
    children: [
      {
        type: mongoose.Schema.Types.ObjectId,
        ref: "User",
        default: [], // Add default empty array
      },
    ],
    isActive: {
      type: Boolean,
      default: true,
    },
    isTemporaryPassword: {
      type: Boolean,
      default: false,
    },
    lastLoginAt: {
      type: Date,
      default: null,
    },
    passwordResetToken: {
      type: String,
      default: null,
    },
    passwordResetExpires: {
      type: Date,
      default: null,
    },
    // Blocking system
    isBlocked: {
      type: Boolean,
      default: false,
    },
    blockInfo: {
      reason: {
        type: String,
        trim: true,
        default: "",
      },
      notes: {
        type: String,
        trim: true,
        default: "",
      },
      blockedAt: {
        type: Date,
        default: null,
      },
      blockedBy: {
        type: mongoose.Schema.Types.ObjectId,
        ref: "Admin",
        default: null,
      },
      expiresAt: {
        type: Date,
        default: null,
      },
      autoUnblockProcessed: {
        type: Boolean,
        default: false,
      },
    },
    paymentMethod: {
      type: String,
      enum: ["bank_transfer", "sepa_direct_debit"],
      default: null,
    },
    paymentDetails: {
      bankDetails: {
        accountHolderName: { type: String, trim: true },
        bankName: { type: String, trim: true },
        accountNumber: { type: String, trim: true },
        routingNumber: { type: String, trim: true },
        iban: { type: String, trim: true },
        swiftCode: { type: String, trim: true },
      },
      sepaDetails: {
        accountHolderName: { type: String, trim: true },
        iban: { type: String, trim: true },
        bic: { type: String, trim: true },
        mandateReference: { type: String, trim: true },
        mandateDate: { type: Date },
      },
    },
    paymentPreferences: {
      autoDebit: { type: Boolean, default: false },
      monthlyLimit: { type: Number, min: 0, default: 0 },
      notifications: { type: Boolean, default: true },
    },
  },
  {
    timestamps: true,
  },
)

// Index for better query performance
parentSchema.index({ email: 1 })
parentSchema.index({ createdAt: -1 })

// Hash password before saving
parentSchema.pre("save", async function (next) {
  // Only hash the password if it has been modified (or is new)
  if (!this.isModified("password")) return next()

  try {
    // Hash password with cost of 12
    const hashedPassword = await bcrypt.hash(this.password, 12)
    this.password = hashedPassword
    next()
  } catch (error) {
    next(error)
  }
})

// Method to check password
parentSchema.methods.checkPassword = async function (candidatePassword) {
  return await bcrypt.compare(candidatePassword, this.password)
}

// Method to add child to parent
parentSchema.methods.addChild = function (childId) {
  // Ensure children array exists
  if (!this.children) {
    this.children = []
  }

  // Check if child is already linked
  if (!this.children.includes(childId)) {
    this.children.push(childId)
    return this.save()
  }
  return Promise.resolve(this)
}

// Method to remove child from parent
parentSchema.methods.removeChild = function (childId) {
  // Ensure children array exists
  if (!this.children) {
    this.children = []
    return this.save()
  }

  this.children = this.children.filter((child) => !child.equals(childId))
  return this.save()
}

// Method to update last login
parentSchema.methods.updateLastLogin = function () {
  this.lastLoginAt = new Date()
  return this.save()
}

// Virtual for children count with null check
parentSchema.virtual("childrenCount").get(function () {
  return this.children ? this.children.length : 0
})

// Ensure virtual fields are serialized
parentSchema.set("toJSON", { virtuals: true })

module.exports = mongoose.model("Parent", parentSchema)
