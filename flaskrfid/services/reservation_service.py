from datetime import datetime, timedelta
from models.meal_reservation import MealReservation
from models.food import Food
from models.user import User
from models.purchase import Purchase, PurchaseItem
import structlog
import os

logger = structlog.get_logger()

class ReservationService:
    def __init__(self):
        pass
    
    def get_today_reservations(self, user_id):
        """Get today's reservations for a user"""
        try:
            logger.info("📅 Fetching today's reservations", user_id=user_id)
            
            today = datetime.utcnow()
            start_of_day = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            reservations = MealReservation.objects(
                student_id=user_id,
                reservation_date__gte=start_of_day,
                reservation_date__lte=end_of_day,
                status__in=['pending', 'confirmed', 'prepared']  # Exclude 'served' and 'cancelled'
            ).order_by('meal_type', 'reservation_date')
            
            # Convert to dict format with populated references
            result = []
            for reservation in reservations:
                reservation_dict = reservation.to_dict()
                
                # Populate food details
                if reservation.food_id:
                    food = Food.objects(id=reservation.food_id.id).first()
                    if food:
                        reservation_dict['food'] = food.to_dict()
                
                # Populate student details
                if reservation.student_id:
                    student = User.objects(id=reservation.student_id.id).first()
                    if student:
                        reservation_dict['student'] = student.to_dict()
                
                result.append(reservation_dict)
            
            logger.info("✅ Reservations fetched", user_id=user_id, count=len(result))
            return result
        except Exception as e:
            logger.error("Get today reservations error", error=str(e))
            return []
    
    def confirm_reservation(self, reservation_id, purchase_service=None):
        """Confirm a reservation (mark as served and create purchase record)"""
        try:
            logger.info("✅ Confirming reservation", reservation_id=reservation_id)
            
            reservation = MealReservation.objects(id=reservation_id).first()
            
            if not reservation:
                raise ValueError('Reservation not found')
            
            if reservation.status == 'served':
                raise ValueError('Reservation has already been served')
            
            if reservation.status == 'cancelled':
                raise ValueError('Cannot confirm a cancelled reservation')
            
            # Mark as served
            station_id = os.getenv('STATION_ID', 'STATION_001')
            reservation.mark_served_by_rfid(station_id)
            
            # Create purchase record for the served reservation
            purchase_result = None
            try:
                # Get food and student details
                food = Food.objects(id=reservation.food_id.id).first()
                student = User.objects(id=reservation.student_id.id).first()
                
                if not food or not student:
                    raise ValueError('Food or student not found')
                
                purchase_data = {
                    'user_id': str(reservation.student_id.id),
                    'uid': student.uid,
                    'user_name': student.name,
                    'user_category': student.user_category or 'student',
                    'items': [{
                        'food_id': str(reservation.food_id.id),
                        'name': food.name,
                        'price': reservation.actual_cost or reservation.estimated_cost,
                        'quantity': reservation.quantity,
                        'subtotal': (reservation.actual_cost or reservation.estimated_cost) * reservation.quantity
                    }],
                    'total_amount': (reservation.actual_cost or reservation.estimated_cost) * reservation.quantity,
                    'cafeteria_station': station_id,
                    'processed_by': 'rfid_reservation_system',
                    'notes': f'Reservation fulfilled: {reservation.meal_type} meal on {datetime.utcnow().strftime("%Y-%m-%d")}',
                    'payment_method': 'monthly_billing',  # Parent will be charged
                    'payment_status': 'pending'
                }
                
                if purchase_service:
                    purchase_result = purchase_service.complete_purchase(purchase_data)
                else:
                    # Fallback: create purchase directly
                    purchase_items = [PurchaseItem(
                        food_id=purchase_data['items'][0]['food_id'],
                        name=purchase_data['items'][0]['name'],
                        price=purchase_data['items'][0]['price'],
                        quantity=purchase_data['items'][0]['quantity'],
                        subtotal=purchase_data['items'][0]['subtotal']
                    )]
                    
                    purchase = Purchase(
                        user_id=purchase_data['user_id'],
                        uid=purchase_data['uid'],
                        user_name=purchase_data['user_name'],
                        user_category=purchase_data['user_category'],
                        items=purchase_items,
                        total_amount=purchase_data['total_amount'],
                        cafeteria_station=purchase_data['cafeteria_station'],
                        processed_by=purchase_data['processed_by'],
                        notes=purchase_data['notes'],
                        payment_method=purchase_data['payment_method'],
                        payment_status=purchase_data['payment_status']
                    )
                    purchase.save()
                    purchase_result = {'success': True, 'purchase': purchase.to_dict()}
                
                logger.info("✅ Purchase record created for served reservation",
                           reservation_id=reservation_id,
                           purchase_id=purchase_result['purchase']['id'],
                           amount=purchase_data['total_amount'],
                           student_name=student.name,
                           food_name=food.name)
            except Exception as purchase_error:
                logger.error("Failed to create purchase record for reservation", error=str(purchase_error))
                raise ValueError(f"Reservation served but failed to create purchase record: {str(purchase_error)}")
            
            logger.info("✅ Reservation confirmed successfully", reservation_id=reservation_id)
            
            return {
                'success': True,
                'reservation': reservation.to_dict(),
                'purchase': purchase_result['purchase'] if purchase_result else None,
                'message': f"Reservation served and ${((reservation.actual_cost or reservation.estimated_cost) * reservation.quantity):.2f} purchase recorded for payment"
            }
        except Exception as e:
            logger.error("Confirm reservation error", error=str(e))
            raise ValueError(str(e) or 'Failed to confirm reservation')
    
    def get_reservation_by_id(self, reservation_id):
        """Get reservation details by ID"""
        try:
            reservation = MealReservation.objects(id=reservation_id).first()
            if reservation:
                return reservation.to_dict()
            return None
        except Exception as e:
            logger.error("Get reservation by ID error", error=str(e))
            return None
    
    def get_reservations(self, params=None):
        """Get all reservations for a date range"""
        try:
            if params is None:
                params = {}
            
            query = {}
            
            if params.get('date'):
                date = datetime.fromisoformat(params['date'].replace('Z', '+00:00'))
                start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
                query['reservation_date__gte'] = start_of_day
                query['reservation_date__lte'] = end_of_day
            
            if params.get('status'):
                query['status'] = params['status']
            
            if params.get('meal_type'):
                query['meal_type'] = params['meal_type']
            
            reservations = MealReservation.objects(**query).order_by('reservation_date', 'meal_type')
            return [reservation.to_dict() for reservation in reservations]
        except Exception as e:
            logger.error("Get reservations error", error=str(e))
            return []
    
    def update_reservation_status(self, reservation_id, status, notes=''):
        """Update reservation status"""
        try:
            reservation = MealReservation.objects(id=reservation_id).first()
            
            if not reservation:
                raise ValueError('Reservation not found')
            
            reservation.status = status
            reservation.notes = notes
            
            if status == 'served':
                reservation.served_at = datetime.utcnow()
                reservation.rfid_processed_at = datetime.utcnow()
                reservation.served_by_station = os.getenv('STATION_ID', 'STATION_001')
            
            reservation.save()
            
            logger.info("✅ Reservation status updated", 
                       reservation_id=reservation_id, status=status,
                       station=os.getenv('STATION_ID'))
            
            return reservation.to_dict()
        except Exception as e:
            logger.error("Update reservation status error", error=str(e))
            raise e
    
    def get_reservation_stats(self):
        """Get reservation statistics"""
        try:
            today = datetime.utcnow()
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today_start + timedelta(days=1)
            
            total_reservations = MealReservation.objects().count()
            today_reservations = MealReservation.objects(
                reservation_date__gte=today_start,
                reservation_date__lt=tomorrow
            ).count()
            pending_reservations = MealReservation.objects(
                status='pending',
                reservation_date__gte=today_start
            ).count()
            served_today = MealReservation.objects(
                reservation_date__gte=today_start,
                reservation_date__lt=tomorrow,
                status='served'
            ).count()
            
            return {
                'total_reservations': total_reservations,
                'today_reservations': today_reservations,
                'pending_reservations': pending_reservations,
                'served_today': served_today
            }
        except Exception as e:
            logger.error("Get reservation stats error", error=str(e))
            return {
                'total_reservations': 0,
                'today_reservations': 0,
                'pending_reservations': 0,
                'served_today': 0
            }
    
    def get_today_reservations_by_meal_type(self):
        """Get reservations by meal type for today"""
        try:
            today = datetime.utcnow()
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today_start + timedelta(days=1)
            
            pipeline = [
                {
                    '$match': {
                        'reservation_date': {'$gte': today_start, '$lt': tomorrow},
                        'status': {'$in': ['pending', 'confirmed', 'prepared']}
                    }
                },
                {
                    '$group': {
                        '_id': '$meal_type',
                        'count': {'$sum': '$quantity'},
                        'reservations': {'$sum': 1}
                    }
                }
            ]
            
            results = list(MealReservation.objects.aggregate(pipeline))
            
            return {
                result['_id']: {
                    'count': result['count'],
                    'reservations': result['reservations']
                }
                for result in results
            }
        except Exception as e:
            logger.error("Get reservations by meal type error", error=str(e))
            return {}