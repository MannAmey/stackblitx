from datetime import datetime, timedelta
from models.user import User
import structlog

logger = structlog.get_logger()

class UserService:
    def __init__(self):
        pass
    
    def get_user_by_uid(self, uid):
        """Get user by UID from database"""
        try:
            logger.info("👤 Looking up user by UID", uid=uid)
            
            user = User.objects(uid=uid, is_active=True).first()
            
            if user:
                logger.info("✅ User found", 
                           uid=user.uid, name=user.name, 
                           category=user.user_category,
                           is_active=user.is_active, is_blocked=user.is_blocked)
                return user
            
            logger.warning("❌ User not found for UID", uid=uid)
            return None
        except Exception as e:
            logger.error("User lookup error", uid=uid, error=str(e))
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID (for purchase flow)"""
        try:
            logger.info("👤 Looking up user by ID", user_id=user_id)
            
            user = User.objects(id=user_id).first()
            
            if user:
                logger.info("✅ User found by ID", 
                           user_id=str(user.id), uid=user.uid, 
                           name=user.name, category=user.user_category)
                return user
            
            logger.warning("❌ User not found for ID", user_id=user_id)
            return None
        except Exception as e:
            logger.error("User lookup by ID error", user_id=user_id, error=str(e))
            return None
    
    def update_last_scan(self, user_id):
        """Update user's last scan time"""
        try:
            logger.info("📝 Updating last scan time", user_id=user_id)
            
            user = User.objects(id=user_id).first()
            if user:
                user.update_last_scan()
                logger.info("✅ Last scan time updated successfully")
                return True
            
            return False
        except Exception as e:
            logger.error("Update last scan error", error=str(e))
            return False
    
    def search_users(self, query):
        """Search users by name or UID"""
        try:
            users = User.objects(
                is_active=True
            ).filter(
                __raw__={
                    '$or': [
                        {'name': {'$regex': query, '$options': 'i'}},
                        {'uid': {'$regex': query, '$options': 'i'}},
                        {'email': {'$regex': query, '$options': 'i'}}
                    ]
                }
            ).limit(20)
            
            return list(users)
        except Exception as e:
            logger.error("User search error", error=str(e))
            return []
    
    def validate_user_access(self, user):
        """Check if user can access system (not blocked)"""
        try:
            if not user.is_active:
                return {
                    'can_access': False,
                    'reason': 'Account is inactive',
                    'message': 'This account has been deactivated. Please contact administration.'
                }
            
            if user.is_blocked:
                # Check if block has expired
                if (user.block_info.expires_at and 
                    datetime.utcnow() > user.block_info.expires_at):
                    # Auto-unblock expired blocks
                    user.is_blocked = False
                    user.block_info.reason = ''
                    user.block_info.notes = ''
                    user.block_info.blocked_at = None
                    user.block_info.blocked_by = None
                    user.block_info.expires_at = None
                    user.block_info.auto_unblock_processed = False
                    user.save()
                    
                    logger.info("✅ Auto-unblocked expired user", 
                               user_id=str(user.id), uid=user.uid)
                    return {'can_access': True}
                
                return {
                    'can_access': False,
                    'reason': 'Account is blocked',
                    'message': user.block_info.reason or 'This account has been temporarily blocked.',
                    'expires_at': user.block_info.expires_at
                }
            
            return {'can_access': True}
        except Exception as e:
            logger.error("User access validation error", error=str(e))
            return {
                'can_access': False,
                'reason': 'System error',
                'message': 'Unable to validate account access. Please try again.'
            }
    
    def get_user_for_rfid_display(self, uid):
        """Get user with populated data for RFID display"""
        try:
            user = self.get_user_by_uid(uid)
            if not user:
                return None
            
            # Validate access
            access_check = self.validate_user_access(user)
            
            return {
                'user': user,
                'access_check': access_check,
                'display_data': {
                    'name': user.name,
                    'class_or_year': user.class_or_year,
                    'user_category': user.user_category,
                    'uid': user.uid,
                    'scan_count': user.scan_count or 0,
                    'last_scan_at': user.last_scan_at,
                    'status': 'active' if access_check['can_access'] else 'blocked'
                }
            }
        except Exception as e:
            logger.error("Get user for RFID display error", error=str(e))
            return None
    
    def create_user(self, user_data):
        """Create new user (for unregistered cards)"""
        try:
            logger.info("👤 Creating new user", uid=user_data.get('uid'), 
                       name=user_data.get('name'))
            
            user = User(
                uid=user_data['uid'],
                name=user_data['name'].strip(),
                class_or_year=user_data['class_or_year'].strip(),
                user_category=user_data['user_category'].lower(),
                email=user_data['email'].lower().strip(),
                gender=user_data['gender'].lower()
            )
            
            user.save()
            
            logger.info("✅ User created successfully", 
                       user_id=str(user.id), name=user.name, uid=user.uid)
            
            return user
        except Exception as e:
            logger.error("User creation error", error=str(e))
            
            if 'duplicate key' in str(e).lower():
                if 'uid' in str(e):
                    raise ValueError('User with this UID already exists')
                elif 'email' in str(e):
                    raise ValueError('User with this email already exists')
            
            raise ValueError(str(e) or 'Failed to create user')
    
    def get_user_stats(self):
        """Get user statistics for dashboard"""
        try:
            total_users = User.objects(is_active=True).count()
            total_students = User.objects(user_category='student', is_active=True).count()
            total_staff = User.objects(user_category='staff', is_active=True).count()
            blocked_users = User.objects(is_blocked=True, is_active=True).count()
            
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_scans = User.objects(
                last_scan_at__gte=today_start,
                is_active=True
            ).count()
            
            return {
                'total_users': total_users,
                'total_students': total_students,
                'total_staff': total_staff,
                'blocked_users': blocked_users,
                'today_scans': today_scans
            }
        except Exception as e:
            logger.error("Get user stats error", error=str(e))
            return {
                'total_users': 0,
                'total_students': 0,
                'total_staff': 0,
                'blocked_users': 0,
                'today_scans': 0
            }
    
    def get_recent_activity(self, limit=10):
        """Get recent user activity"""
        try:
            recent_scans = User.objects(
                last_scan_at__exists=True,
                is_active=True
            ).order_by('-last_scan_at').limit(limit).only(
                'name', 'uid', 'class_or_year', 'user_category', 
                'last_scan_at', 'scan_count'
            )
            
            return list(recent_scans)
        except Exception as e:
            logger.error("Get recent activity error", error=str(e))
            return []