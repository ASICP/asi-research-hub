#!/usr/bin/env python3
"""
System check script for ASI Research Hub
Run this to verify everything is set up correctly
"""

import sys
import os

def check_dependencies():
    """Check if all required packages are installed"""
    print("🔍 Checking dependencies...\n")
    
    required_packages = [
        'flask',
        'flask_cors',
        'flask_jwt_extended',
        'bcrypt',
        'PyPDF2',
        'scholarly',
        'requests',
        'sendgrid',
        'validators'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed!\n")
        return True

def check_database():
    """Check if database exists and is initialized"""
    print("🔍 Checking database...\n")
    
    if not os.path.exists('asi_research_hub.db'):
        print("   ❌ Database not found")
        print("   Run: python -c \"from database import init_db; init_db()\"")
        return False
    
    try:
        from database import get_db
        
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row['name'] for row in cursor.fetchall()]
            
            required_tables = ['users', 'papers', 'user_bookmarks', 'search_logs', 'api_usage']
            
            for table in required_tables:
                if table in tables:
                    print(f"   ✅ Table: {table}")
                else:
                    print(f"   ❌ Table: {table} - MISSING")
                    return False
            
            # Check paper count
            cursor.execute("SELECT COUNT(*) as count FROM papers")
            paper_count = cursor.fetchone()['count']
            print(f"\n   📚 Papers in database: {paper_count}")
            
            if paper_count == 0:
                print("   ⚠️  No papers yet. Run: python upload_papers.py")
        
        print("\n✅ Database OK!\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def check_config():
    """Check if configuration is set up"""
    print("🔍 Checking configuration...\n")
    
    try:
        from config import Config
        
        # Check secret keys
        if Config.SECRET_KEY == 'dev-secret-key-change-in-production':
            print("   ⚠️  Using default SECRET_KEY (OK for dev, change for production)")
        else:
            print("   ✅ Custom SECRET_KEY set")
        
        if Config.JWT_SECRET_KEY == 'jwt-secret-key-change-in-production':
            print("   ⚠️  Using default JWT_SECRET_KEY (OK for dev, change for production)")
        else:
            print("   ✅ Custom JWT_SECRET_KEY set")
        
        # Check SendGrid
        if Config.SENDGRID_API_KEY:
            print("   ✅ SendGrid API key configured")
        else:
            print("   ⚠️  SendGrid API key not set (emails won't send)")
            print("      Set SENDGRID_API_KEY in Replit Secrets")
        
        # Check frontend URL
        print(f"   ℹ️  Frontend URL: {Config.FRONTEND_URL}")
        
        print("\n✅ Configuration OK!\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False

def check_directories():
    """Check if required directories exist"""
    print("🔍 Checking directories...\n")
    
    from config import Config
    
    if not os.path.exists(Config.UPLOAD_FOLDER):
        print(f"   ⚠️  Creating upload directory: {Config.UPLOAD_FOLDER}")
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    print(f"   ✅ Upload directory: {Config.UPLOAD_FOLDER}")
    print("\n✅ Directories OK!\n")
    return True

def test_basic_functionality():
    """Test basic app functionality"""
    print("🔍 Testing basic functionality...\n")
    
    try:
        from auth import AuthService
        from utils import validate_email, validate_password
        
        # Test email validation
        assert validate_email('test@example.com') == True
        assert validate_email('invalid-email') == False
        print("   ✅ Email validation")
        
        # Test password validation
        assert validate_password('password123') == True
        assert validate_password('short') == False
        print("   ✅ Password validation")
        
        # Test password hashing
        hashed = AuthService.hash_password('testpassword')
        assert AuthService.verify_password('testpassword', hashed) == True
        assert AuthService.verify_password('wrongpassword', hashed) == False
        print("   ✅ Password hashing")
        
        print("\n✅ Basic functionality OK!\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Functionality error: {e}")
        return False

def main():
    """Run all checks"""
    print("\n" + "="*50)
    print("ASI RESEARCH HUB - SYSTEM CHECK")
    print("="*50 + "\n")
    
    results = []
    
    results.append(("Dependencies", check_dependencies()))
    results.append(("Configuration", check_config()))
    results.append(("Directories", check_directories()))
    results.append(("Database", check_database()))
    results.append(("Functionality", test_basic_functionality()))
    
    print("="*50)
    print("SUMMARY")
    print("="*50 + "\n")
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {check_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*50)
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED! System is ready to run.")
        print("\nRun the app with: python app.py")
        print("Your API will be at: http://0.0.0.0:5000\n")
        return 0
    else:
        print("\n⚠️  SOME CHECKS FAILED. Please fix the issues above.")
        print("\nFor help, check README.md\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
