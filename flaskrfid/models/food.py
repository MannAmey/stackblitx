from datetime import datetime
from mongoengine import Document, StringField, FloatField, BooleanField, ListField, EmbeddedDocument, EmbeddedDocumentField, DateTimeField, IntField

class NutritionInfo(EmbeddedDocument):
    calories = FloatField(min_value=0)
    protein = FloatField(min_value=0)
    carbs = FloatField(min_value=0)
    fat = FloatField(min_value=0)
    fiber = FloatField(min_value=0)
    sugar = FloatField(min_value=0)

class Food(Document):
    name = StringField(required=True)
    description = StringField(default='')
    price = FloatField(required=True, min_value=0)
    image = StringField(default='')
    category = StringField(required=True)
    category_id = StringField(default='')
    is_available = BooleanField(default=True)
    ingredients = ListField(StringField())
    allergens = ListField(StringField())
    nutrition_info = EmbeddedDocumentField(NutritionInfo)
    preparation_time = IntField(min_value=0, default=0)
    is_vegetarian = BooleanField(default=False)
    is_vegan = BooleanField(default=False)
    is_gluten_free = BooleanField(default=False)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'foods',
        'indexes': [
            'category',
            'is_available',
            'is_active',
            ('name', 'description')  # Text index
        ]
    }
    
    def clean(self):
        """Clean and validate data before saving"""
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': str(self.id),
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'image': self.image,
            'category': self.category,
            'category_id': self.category_id,
            'is_available': self.is_available,
            'ingredients': self.ingredients,
            'allergens': self.allergens,
            'nutrition_info': self.nutrition_info.to_mongo() if self.nutrition_info else None,
            'preparation_time': self.preparation_time,
            'is_vegetarian': self.is_vegetarian,
            'is_vegan': self.is_vegan,
            'is_gluten_free': self.is_gluten_free,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }