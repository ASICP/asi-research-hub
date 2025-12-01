import bcrypt
import secrets
import os
import certifi
from datetime import datetime
from database import get_db
from psycopg2.extras import RealDictCursor
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config import Config

# Fix for SSL certificate verification on some systems
os.environ['SSL_CERT_FILE'] = certifi.where()

class AuthService:
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate secure random token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_user(email: str, password: str, first_name: str, 
                   last_name: str, tier: str, region: str, reason: str) -> dict:
        """Create new user account"""
        password_hash = AuthService.hash_password(password)
        verification_token = AuthService.generate_verification_token()
        
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return {'success': False, 'error': 'Email already registered'}
            
            # Insert user
            cursor.execute("""
                INSERT INTO users (email, password_hash, first_name, last_name, 
                                 tier, region, reason, verification_token)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (email, password_hash, first_name, last_name, tier, region, reason, verification_token))
            
            result = cursor.fetchone()
            user_id = result['id'] if result else None
        
        # Send verification email
        AuthService.send_verification_email(email, first_name, verification_token)
        
        return {'success': True, 'user_id': user_id}
    
    @staticmethod
    def send_verification_email(email: str, first_name: str, token: str):
        """Send email verification link"""
        verification_url = f"{Config.FRONTEND_URL}/verify?token={token}"
        
        message = Mail(
            from_email=Config.SENDGRID_FROM_EMAIL,
            to_emails=email,
            subject='Verify your ASI Research Hub account',
            html_content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px; text-align: center;">
                    <h2 style="color: #2563eb; margin-bottom: 20px;">Welcome to ASI Research Hub, {first_name}!</h2>
                    <p style="color: #4b5563; font-size: 16px; margin-bottom: 30px;">
                        Please verify your email address to access the AI alignment research database.
                    </p>
                    <a href="{verification_url}" 
                       style="display: inline-block; background-color: #2563eb; color: white; 
                              padding: 15px 40px; text-decoration: none; border-radius: 5px; 
                              font-weight: bold; font-size: 16px;">
                        Verify Email Address
                    </a>
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                        Or copy and paste this link into your browser:
                    </p>
                    <p style="color: #2563eb; font-size: 12px; word-break: break-all;">
                        {verification_url}
                    </p>
                    <p style="color: #9ca3af; font-size: 12px; margin-top: 30px;">
                        This link will expire in 24 hours.
                    </p>
                </div>
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 12px;">
                        ASI Research Hub | Advancing AI Safety Research
                    </p>
                    <p style="color: #9ca3af; font-size: 11px;">
                        If you didn't create this account, please ignore this email.
                    </p>
                </div>
            </body>
            </html>
            """
        )
        
        try:
            if Config.SENDGRID_API_KEY:
                sg = SendGridAPIClient(Config.SENDGRID_API_KEY)
                response = sg.send(message)
                print(f"✅ Verification email sent to {email}")
            else:
                print(f"⚠️ SendGrid not configured. Verification token: {token}")
                print(f"   Verification URL: {verification_url}")
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            print(f"   Verification token for manual use: {token}")
    
    @staticmethod
    def verify_email(token: str) -> dict:
        """Verify user email with token"""
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, email FROM users 
                WHERE verification_token = %s AND is_verified = FALSE
            """, (token,))
            
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'error': 'Invalid or expired token'}
            
            cursor.execute("""
                UPDATE users 
                SET is_verified = TRUE, verification_token = NULL 
                WHERE id = %s
            """, (user['id'],))
        
        return {'success': True, 'email': user['email']}
    
    @staticmethod
    def login(email: str, password: str) -> dict:
        """Authenticate user and return JWT token"""
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, email, password_hash, first_name, last_name, 
                       tier, is_verified 
                FROM users 
                WHERE email = %s
            """, (email,))
            
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'error': 'Invalid credentials'}
            
            if not user['is_verified']:
                return {'success': False, 'error': 'Email not verified. Please check your inbox.'}
            
            if not AuthService.verify_password(password, user['password_hash']):
                return {'success': False, 'error': 'Invalid credentials'}
            
            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s
            """, (user['id'],))
        
        return {
            'success': True,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'tier': user['tier']
            }
        }
    
    @staticmethod
    def request_password_reset(email: str) -> dict:
        """Generate password reset token and send email"""
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("SELECT id, first_name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            
            if not user:
                # Don't reveal if email exists for security
                return {'success': True, 'message': 'If the email exists, a reset link has been sent'}
            
            # Generate reset token
            reset_token = AuthService.generate_verification_token()
            
            cursor.execute("""
                UPDATE users 
                SET password_reset_token = %s, password_reset_expires = NOW() + INTERVAL '1 hour'
                WHERE id = %s
            """, (reset_token, user['id']))
        
        # Send reset email
        AuthService.send_password_reset_email(email, user['first_name'], reset_token)
        
        return {'success': True, 'message': 'If the email exists, a reset link has been sent'}
    
    @staticmethod
    def send_password_reset_email(email: str, first_name: str, token: str):
        """Send password reset email"""
        reset_url = f"{Config.FRONTEND_URL}/reset-password?token={token}"
        
        message = Mail(
            from_email=Config.SENDGRID_FROM_EMAIL,
            to_emails=email,
            subject='Reset your ASI Research Hub password',
            html_content=f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px; text-align: center;">
                    <h2 style="color: #2563eb; margin-bottom: 20px;">Password Reset Request</h2>
                    <p style="color: #4b5563; font-size: 16px; margin-bottom: 30px;">
                        Hi {first_name}, we received a request to reset your password.
                    </p>
                    <a href="{reset_url}" 
                       style="display: inline-block; background-color: #2563eb; color: white; 
                              padding: 15px 40px; text-decoration: none; border-radius: 5px; 
                              font-weight: bold; font-size: 16px;">
                        Reset Password
                    </a>
                    <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                        Or copy and paste this link into your browser:
                    </p>
                    <p style="color: #2563eb; font-size: 12px; word-break: break-all;">
                        {reset_url}
                    </p>
                    <p style="color: #9ca3af; font-size: 12px; margin-top: 30px;">
                        This link will expire in 1 hour.
                    </p>
                </div>
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb;">
                    <p style="color: #6b7280; font-size: 12px;">
                        ASI Research Hub | Advancing AI Safety Research
                    </p>
                    <p style="color: #9ca3af; font-size: 11px;">
                        If you didn't request this reset, please ignore this email.
                    </p>
                </div>
            </body>
            </html>
            """
        )
        
        try:
            if Config.SENDGRID_API_KEY:
                sg = SendGridAPIClient(Config.SENDGRID_API_KEY)
                response = sg.send(message)
                print(f"✅ Password reset email sent to {email}")
            else:
                print(f"⚠️ SendGrid not configured. Reset token: {token}")
                print(f"   Reset URL: {reset_url}")
        except Exception as e:
            print(f"❌ Error sending email: {e}")
            print(f"   Reset token for manual use: {token}")
    
    @staticmethod
    def reset_password(token: str, new_password: str) -> dict:
        """Reset password using valid token"""
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, email FROM users 
                WHERE password_reset_token = %s 
                AND password_reset_expires > NOW()
            """, (token,))
            
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'error': 'Invalid or expired reset token'}
            
            # Hash new password
            password_hash = AuthService.hash_password(new_password)
            
            # Update password and clear reset token
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s, 
                    password_reset_token = NULL,
                    password_reset_expires = NULL
                WHERE id = %s
            """, (password_hash, user['id']))
        
        return {'success': True, 'message': 'Password reset successful'}

