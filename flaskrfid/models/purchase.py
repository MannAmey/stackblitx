from datetime import datetime
from mongoengine import Document, StringField, FloatField, IntField, DateTimeField, ListField, EmbeddedDocument, EmbeddedDocumentField, ReferenceField

class PurchaseItem(EmbeddedDocument):
    food_id = ReferenceField('Food', required=True)
    name = StringField(required=True)
    price = FloatField(required=True, min_value=0)
    quantity = IntField(required=True, min_value=1)
    subtotal = FloatField(required=True, min_value=0)

class Purchase(Document):
    user_id = ReferenceField('User', required=True)
    uid = StringField(required=True)
    user_name = StringField(required=True)
    user_category = StringField(required=True, choices=['staff', 'student'])
    items = ListField(EmbeddedDocumentField(PurchaseItem))
    total_amount = FloatField(required=True, min_value=0)
    purchased_at = DateTimeField(default=datetime.utcnow)
    payment_status = StringField(choices=['pending', 'paid', 'cancelled'], default='pending')
    paid_at = DateTimeField()
    payment_method = StringField(choices=['cash', 'monthly_billing'], default='monthly_billing')
    cash_amount = FloatField()
    change = FloatField()
    notes = StringField(default='')
    cafeteria_station = StringField(default='STATION_001')
    processed_by = StringField(default='')
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'purchases',
        'indexes': [
            'user_id',
            'uid',
            '-purchased_at',
            'payment_status',
            'payment_method',
            'cafeteria_station'
        ]
    }
    
    def clean(self):
        """Clean and validate data before saving"""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id.id) if self.user_id else None,
            'uid': self.uid,
            'user_name': self.user_name,
            'user_category': self.user_category,
            'items': [item.to_mongo() for item in self.items],
            'total_amount': self.total_amount,
            'purchased_at': self.purchased_at.isoformat() if self.purchased_at else None,
            'payment_status': self.payment_status,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'payment_method': self.payment_method,
            'cash_amount': self.cash_amount,
            'change': self.change,
            'notes': self.notes,
            'cafeteria_station': self.cafeteria_station,
            'processed_by': self.processed_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }