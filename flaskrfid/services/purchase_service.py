from datetime import datetime, timedelta
from models.purchase import Purchase, PurchaseItem
from models.food import Food
from models.user import User
import structlog

logger = structlog.get_logger()

class PurchaseService:
    def __init__(self):
        pass
    
    def get_available_foods(self):
        """Get available foods for purchase"""
        try:
            logger.info("🍽️ Fetching available foods...")
            
            foods = Food.objects(is_active=True, is_available=True).order_by('category', 'name')
            
            # Group by category
            grouped_foods = {}
            for food in foods:
                if food.category not in grouped_foods:
                    grouped_foods[food.category] = []
                grouped_foods[food.category].append(food.to_dict())
            
            logger.info("✅ Available foods fetched", 
                       categories=len(grouped_foods.keys()),
                       total_foods=len(foods))
            
            return grouped_foods
        except Exception as e:
            logger.error("Get available foods error", error=str(e))
            return {}
    
    def complete_purchase(self, purchase_data):
        """Complete a purchase transaction"""
        try:
            logger.info("💳 Processing purchase", 
                       user_id=purchase_data.get('user_id'),
                       item_count=len(purchase_data.get('items', [])),
                       total_amount=purchase_data.get('total_amount'),
                       payment_method=purchase_data.get('payment_method'))
            
            # Validate purchase data
            if not purchase_data.get('user_id') or not purchase_data.get('items'):
                raise ValueError('Invalid purchase data')
            
            user_category = purchase_data.get('user_category', 'student')
            
            # Determine payment status based on payment method
            payment_status = 'pending'
            paid_at = None
            notes = purchase_data.get('notes', '')
            cash_amount = None
            change = None
            
            if purchase_data.get('payment_method') == 'cash':
                payment_status = 'paid'
                paid_at = datetime.utcnow()
                cash_amount = purchase_data.get('paid_amount')
                notes += f" | Cash payment: €{purchase_data.get('paid_amount', 0):.2f}"
                if purchase_data.get('paid_amount', 0) > purchase_data.get('total_amount', 0):
                    change = purchase_data.get('paid_amount') - purchase_data.get('total_amount')
                    notes += f" | Change: €{change:.2f}"
            elif purchase_data.get('payment_method') == 'monthly_billing':
                payment_status = 'pending'
                notes += ' | Added to monthly bill - parent will be charged'
            
            # Create purchase items
            purchase_items = []
            for item_data in purchase_data['items']:
                purchase_item = PurchaseItem(
                    food_id=item_data['food_id'],
                    name=item_data['name'],
                    price=item_data['price'],
                    quantity=item_data['quantity'],
                    subtotal=item_data['subtotal']
                )
                purchase_items.append(purchase_item)
            
            # Create purchase record
            purchase = Purchase(
                user_id=purchase_data['user_id'],
                uid=purchase_data['uid'],
                user_name=purchase_data['user_name'],
                user_category=user_category,
                items=purchase_items,
                total_amount=purchase_data['total_amount'],
                cafeteria_station=purchase_data.get('cafeteria_station', 'STATION_001'),
                purchased_at=datetime.utcnow(),
                payment_status=payment_status,
                paid_at=paid_at,
                payment_method=purchase_data['payment_method'],
                cash_amount=cash_amount,
                change=change,
                notes=notes,
                processed_by=purchase_data.get('processed_by', 'rfid_system')
            )
            
            purchase.save()
            
            # Update user's last scan time
            User.objects(id=purchase_data['user_id']).update_one(
                set__last_scan_at=datetime.utcnow(),
                inc__scan_count=1
            )
            
            logger.info("✅ Purchase completed successfully", 
                       purchase_id=str(purchase.id),
                       user_id=purchase.user_id,
                       total_amount=purchase.total_amount,
                       payment_method=purchase_data['payment_method'],
                       payment_status=payment_status,
                       source=purchase_data.get('processed_by', 'rfid_system'))
            
            return {
                'success': True,
                'purchase': purchase.to_dict(),
                'message': ('Cash payment completed successfully' 
                           if purchase_data['payment_method'] == 'cash' 
                           else 'Purchase added to monthly bill'),
                'payment_method': purchase_data['payment_method'],
                'change': (purchase_data.get('paid_amount', 0) - purchase_data.get('total_amount', 0)
                          if purchase_data.get('payment_method') == 'cash' 
                          and purchase_data.get('paid_amount', 0) > purchase_data.get('total_amount', 0)
                          else 0)
            }
        except Exception as e:
            logger.error("Purchase completion error", error=str(e))
            raise ValueError(str(e) or 'Purchase failed')
    
    def validate_purchase_items(self, items):
        """Validate purchase items against available foods"""
        try:
            for item in items:
                food = Food.objects(id=item['food_id']).first()
                
                if not food:
                    raise ValueError(f"Food item not found: {item['name']}")
                
                if not food.is_available or not food.is_active:
                    raise ValueError(f"Food item not available: {food.name}")
                
                if abs(item['price'] - food.price) > 0.01:
                    raise ValueError(f"Price mismatch for {food.name}. Expected: ${food.price}, Got: ${item['price']}")
            
            return True
        except Exception as e:
            logger.error("Purchase validation error", error=str(e))
            raise e
    
    def calculate_total(self, items):
        """Calculate purchase total"""
        return sum(item['price'] * item['quantity'] for item in items)
    
    def get_user_purchases(self, user_id, limit=10):
        """Get purchase history for a user"""
        try:
            purchases = Purchase.objects(user_id=user_id).order_by('-purchased_at').limit(limit)
            return [purchase.to_dict() for purchase in purchases]
        except Exception as e:
            logger.error("Get user purchases error", error=str(e))
            return []
    
    def get_purchase_stats(self):
        """Get purchase statistics"""
        try:
            total_purchases = Purchase.objects().count()
            
            # Calculate total revenue
            pipeline = [
                {'$group': {'_id': None, 'total': {'$sum': '$total_amount'}}}
            ]
            total_revenue_result = list(Purchase.objects.aggregate(pipeline))
            total_revenue = total_revenue_result[0]['total'] if total_revenue_result else 0
            
            # Today's stats
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_purchases = Purchase.objects(purchased_at__gte=today_start).count()
            
            # Today's revenue
            today_pipeline = [
                {'$match': {'purchased_at': {'$gte': today_start}}},
                {'$group': {'_id': None, 'total': {'$sum': '$total_amount'}}}
            ]
            today_revenue_result = list(Purchase.objects.aggregate(today_pipeline))
            today_revenue = today_revenue_result[0]['total'] if today_revenue_result else 0
            
            return {
                'total_purchases': total_purchases,
                'total_revenue': total_revenue,
                'today_purchases': today_purchases,
                'today_revenue': today_revenue
            }
        except Exception as e:
            logger.error("Get purchase stats error", error=str(e))
            return {
                'total_purchases': 0,
                'total_revenue': 0,
                'today_purchases': 0,
                'today_revenue': 0
            }
    
    def get_food_by_id(self, food_id):
        """Get food by ID with full details"""
        try:
            food = Food.objects(id=food_id).first()
            return food
        except Exception as e:
            logger.error("Get food by ID error", error=str(e))
            return None