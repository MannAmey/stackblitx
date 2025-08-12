import os
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
import structlog

logger = structlog.get_logger()

class AuthService:
    def __init__(self):
        self.jwt_secret = os.getenv('JWT_SECRET', 'rfid-server-secret')
        self.jwt_expires_in = timedelta(hours=8)
    
    def authenticate_admin(self, credentials):
        """Authenticate admin user for RFID system"""
        try:
            logger.info("🔐 Authenticating admin for RFID system", username=credentials.get('username'))
            
            # For now, we'll use simple admin validation
            # In production, you might want to connect to admin database
            valid_admins = [
                {
                    'username': 'admin',
                    'password': 'admin123',
                    'name': 'RFID Administrator',
                    'role': 'rfid_admin',
                    'permissions': ['rfid.read', 'rfid.write', 'users.read', 'purchases.write']
                },
                {
                    'username': 'cafeteria',
                    'password': 'cafeteria123',
                    'name': 'Cafeteria Staff',
                    'role': 'cafeteria_staff',
                    'permissions': ['rfid.read', 'rfid.write', 'purchases.write']
                }
            ]
            
            admin = next((a for a in valid_admins 
                         if a['username'] == credentials.get('username') 
                         and a['password'] == credentials.get('password')), None)
            
            if not admin:
                raise ValueError('Invalid credentials')
            
            # Generate RFID server specific token
            rfid_token = self.generate_rfid_token(admin)
            
            logger.info("✅ Admin authenticated successfully", 
                       username=admin['username'], role=admin['role'])
            
            return {
                'success': True,
                'admin': {
                    'id': admin['username'],
                    'username': admin['username'],
                    'name': admin['name'],
                    'role': admin['role'],
                    'permissions': admin['permissions']
                },
                'token': rfid_token
            }
        except Exception as e:
            logger.error("Admin authentication error", error=str(e))
            raise ValueError(str(e) or 'Authentication failed')
    
    def has_rfid_permissions(self, admin):
        """Check if admin has RFID permissions"""
        if admin.get('role') in ['rfid_admin', 'cafeteria_staff']:
            return True
        
        required_permissions = ['rfid.read', 'rfid.write']
        admin_permissions = admin.get('permissions', [])
        return any(perm in admin_permissions for perm in required_permissions)
    
    def generate_rfid_token(self, admin):
        """Generate RFID server specific JWT token"""
        additional_claims = {
            'username': admin['username'],
            'role': admin['role'],
            'permissions': admin['permissions'],
            'system': 'rfid_server',
            'cafeteria': os.getenv('CAFETERIA_NAME', 'School Cafeteria'),
            'station': os.getenv('STATION_ID', 'STATION_001')
        }
        
        return create_access_token(
            identity=admin['username'],
            expires_delta=self.jwt_expires_in,
            additional_claims=additional_claims
        )