from datetime import datetime
from mongoengine import Document, StringField, BooleanField, DateTimeField, IntField, EmbeddedDocument, EmbeddedDocumentField, ReferenceField

class BlockInfo(EmbeddedDocument):
    reason = StringField(default='')
    notes = StringField(default='')
    blocked_at = DateTimeField()
    blocked_by = ReferenceField('Admin')  # We'll create Admin model if needed
    expires_at = DateTimeField()
    auto_unblock_processed = BooleanField(default=False)

class User(Document):
    uid = StringField(required=True, unique=True)
    name = StringField(required=True)
    class_or_year = StringField(required=True)
    user_category = StringField(required=True, choices=['staff', 'student'])
    email = StringField(required=True, unique=True)
    gender = StringField(required=True, choices=['male', 'female', 'other'])
    is_active = BooleanField(default=True)
    last_scan_at = DateTimeField()
    scan_count = IntField(default=0)
    is_blocked = BooleanField(default=False)
    block_info = EmbeddedDocumentField(BlockInfo, default=BlockInfo)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'users',
        'indexes': [
            'uid',
            'email',
            'user_category',
            '-created_at'
        ]
    }
    
    def update_last_scan(self):
        """Update user's last scan time and increment scan count"""
        self.last_scan_at = datetime.utcnow()
        self.scan_count += 1
        self.updated_at = datetime.utcnow()
        self.save()
        return self
    
    def can_access(self):
        """Check if user can access the system"""
        if not self.is_active:
            return False
        if not self.is_blocked:
            return True
        
        # Check if block has expired
        if self.block_info.expires_at and datetime.utcnow() > self.block_info.expires_at:
            return False  # Will be handled by service
        
        return False
    
    def clean(self):
        """Clean and validate data before saving"""
        if self.email:
            self.email = self.email.lower().strip()
        if self.user_category:
            self.user_category = self.user_category.lower()
        if self.gender:
            self.gender = self.gender.lower()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'uid': self.uid,
            'name': self.name,
            'class_or_year': self.class_or_year,
            'user_category': self.user_category,
            'email': self.email,
            'gender': self.gender,
            'is_active': self.is_active,
            'last_scan_at': self.last_scan_at.isoformat() if self.last_scan_at else None,
            'scan_count': self.scan_count,
            'is_blocked': self.is_blocked,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }