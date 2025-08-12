from datetime import datetime
from mongoengine import Document, StringField, FloatField, IntField, DateTimeField, BooleanField, ReferenceField
import os

class MealReservation(Document):
    parent_id = ReferenceField('Parent', required=True)
    student_id = ReferenceField('User', required=True)
    food_id = ReferenceField('Food', required=True)
    reservation_date = DateTimeField(required=True)
    quantity = IntField(required=True, min_value=1, default=1)
    meal_type = StringField(choices=['breakfast', 'lunch', 'dinner', 'snack'], required=True, default='lunch')
    special_instructions = StringField(max_length=500, default='')
    status = StringField(choices=['pending', 'confirmed', 'prepared', 'served', 'cancelled'], default='pending')
    estimated_cost = FloatField(required=True, min_value=0)
    actual_cost = FloatField()
    prepared_by = ReferenceField('Admin')  # We'll create Admin model if needed
    prepared_at = DateTimeField()
    served_at = DateTimeField()
    notes = StringField(default='')
    allergy_notes = StringField(default='')
    is_urgent = BooleanField(default=False)
    served_by_station = StringField(default='')
    rfid_processed_at = DateTimeField()
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'meal_reservations',
        'indexes': [
            'parent_id',
            'student_id',
            'food_id',
            'reservation_date',
            'status',
            'meal_type'
        ]
    }
    
    def mark_served_by_rfid(self, station_id):
        """Mark reservation as served via RFID"""
        self.status = 'served'
        self.served_at = datetime.utcnow()
        self.rfid_processed_at = datetime.utcnow()
        self.served_by_station = station_id
        self.updated_at = datetime.utcnow()
        self.save()
        return self
    
    def clean(self):
        """Clean and validate data before saving"""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'parent_id': str(self.parent_id.id) if self.parent_id else None,
            'student_id': str(self.student_id.id) if self.student_id else None,
            'food_id': str(self.food_id.id) if self.food_id else None,
            'reservation_date': self.reservation_date.isoformat() if self.reservation_date else None,
            'quantity': self.quantity,
            'meal_type': self.meal_type,
            'special_instructions': self.special_instructions,
            'status': self.status,
            'estimated_cost': self.estimated_cost,
            'actual_cost': self.actual_cost,
            'prepared_at': self.prepared_at.isoformat() if self.prepared_at else None,
            'served_at': self.served_at.isoformat() if self.served_at else None,
            'notes': self.notes,
            'allergy_notes': self.allergy_notes,
            'is_urgent': self.is_urgent,
            'served_by_station': self.served_by_station,
            'rfid_processed_at': self.rfid_processed_at.isoformat() if self.rfid_processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }