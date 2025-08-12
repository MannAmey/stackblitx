from datetime import datetime
from mongoengine import Document, StringField, BooleanField, DateTimeField, ListField, ReferenceField, EmbeddedDocument, EmbeddedDocumentField, FloatField
import bcrypt

class BlockInfo(EmbeddedDocument):
    reason = StringField(default='')
    notes = StringField(default='')
    blocked_at = DateTimeField()
    blocked_by = ReferenceField('Admin')
    expires_at = DateTimeField()
    auto_unblock_processed = BooleanField(default=False)

class BankDetails(EmbeddedDocument):
    account_holder_name = StringField()
    bank_name = StringField()
    account_number = StringField()
    routing_number = StringField()
    iban = StringField()
    swift_code = StringField()

class SepaDetails(EmbeddedDocument):
    account_holder_name = StringField()
    iban = StringField()
    bic = StringField()
    mandate_reference = StringField()
    mandate_date = DateTimeField()

class PaymentDetails(EmbeddedDocument):
    bank_details = EmbeddedDocumentField(BankDetails)
    sepa_details = EmbeddedDocumentField(SepaDetails)

class PaymentPreferences(EmbeddedDocument):
    auto_debit = BooleanField(default=False)
    monthly_limit = FloatField(min_value=0, default=0)
    notifications = BooleanField(default=True)

class Parent(Document):
    name = StringField(required=True)
    email = StringField(required=True, unique=True)
    password = StringField(required=True, min_length=6)
    children = ListField(ReferenceField('User'), default=list)
    is_active = BooleanField(default=True)
    is_temporary_password = BooleanField(default=False)
    last_login_at = DateTimeField()
    password_reset_token = StringField()
    password_reset_expires = DateTimeField()
    is_blocked = BooleanField(default=False)
    block_info = EmbeddedDocumentField(BlockInfo, default=BlockInfo)
    payment_method = StringField(choices=['bank_transfer', 'sepa_direct_debit'])
    payment_details = EmbeddedDocumentField(PaymentDetails)
    payment_preferences = EmbeddedDocumentField(PaymentPreferences, default=PaymentPreferences)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'parents',
        'indexes': [
            'email',
            '-created_at'
        ]
    }
    
    def clean(self):
        """Clean and validate data before saving"""
        if self.email:
            self.email = self.email.lower().strip()
        self.updated_at = datetime.utcnow()
        
        # Hash password if it's been modified
        if self._changed_fields and 'password' in self._changed_fields:
            self.password = bcrypt.hashpw(self.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, candidate_password):
        """Check if provided password matches stored hash"""
        return bcrypt.checkpw(candidate_password.encode('utf-8'), self.password.encode('utf-8'))
    
    def add_child(self, child_id):
        """Add child to parent"""
        if child_id not in self.children:
            self.children.append(child_id)
            self.save()
        return self
    
    def remove_child(self, child_id):
        """Remove child from parent"""
        if child_id in self.children:
            self.children.remove(child_id)
            self.save()
        return self
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login_at = datetime.utcnow()
        self.save()
        return self
    
    @property
    def children_count(self):
        """Get number of children"""
        return len(self.children) if self.children else 0
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'name': self.name,
            'email': self.email,
            'children_count': self.children_count,
            'is_active': self.is_active,
            'is_temporary_password': self.is_temporary_password,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'is_blocked': self.is_blocked,
            'payment_method': self.payment_method,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }