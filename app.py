from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from psycopg2.extras import RealDictCursor
import requests
import os
from config import Config
from database import init_db, get_db
from auth import AuthService
from search import SearchService
from utils import validate_email, validate_password, allowed_file
import json

app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for WordPress embedding and local testing
CORS(app, origins=[Config.FRONTEND_URL, 'http://localhost:5000', 'http://127.0.0.1:5000'])

# JWT setup
jwt = JWTManager(app)

@jwt.invalid_token_loader
def invalid_token_callback(error):
    print(f"❌ Invalid Token: {error}")
    return jsonify({'error': 'Invalid token', 'details': error}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    print(f"❌ Missing Token: {error}")
    return jsonify({'error': 'Missing token', 'details': error}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    print(f"❌ Expired Token: {jwt_payload}")
    return jsonify({'error': 'Token has expired', 'details': 'token_expired'}), 401

# Database is already initialized in PostgreSQL - no need to create tables
# if not os.path.exists(Config.DATABASE_PATH):
#     init_db()

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    data = request.get_json()
    
    # Validate input
    required_fields = ['email', 'password', 'first_name', 'last_name', 'tier', 'region', 'reason']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
            
    # Verify reCAPTCHA
    # Skip verification for localhost/127.0.0.1 to allow local testing
    if request.remote_addr not in ['127.0.0.1', 'localhost']:
        recaptcha_token = data.get('recaptcha_token')
        if not recaptcha_token:
            if Config.RECAPTCHA_SECRET_KEY:
                return jsonify({'error': 'Missing CAPTCHA token'}), 400
        
        if Config.RECAPTCHA_SECRET_KEY and recaptcha_token:
            try:
                verify_response = requests.post(
                    'https://www.google.com/recaptcha/api/siteverify',
                    data={
                        'secret': Config.RECAPTCHA_SECRET_KEY,
                        'response': recaptcha_token
                    }
                )
                result = verify_response.json()
                
                if not result.get('success'):
                    print(f"CAPTCHA failed: {result}")
                    return jsonify({'error': 'CAPTCHA verification failed'}), 400
                    
                # Check score for v3 (0.0 to 1.0)
                if result.get('score', 1.0) < 0.5:
                    print(f"CAPTCHA low score: {result.get('score')}")
                    return jsonify({'error': 'CAPTCHA verification failed (low score)'}), 400
                    
            except Exception as e:
                print(f"CAPTCHA error: {e}")
                return jsonify({'error': 'CAPTCHA verification error'}), 500
    
    # Validate email
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password
    if not validate_password(data['password']):
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    # Validate tier
    if data['tier'] not in Config.USER_TIERS:
        return jsonify({'error': 'Invalid tier'}), 400
    
    # Validate region
    if data['region'] not in Config.USER_REGIONS:
        return jsonify({'error': 'Invalid region'}), 400
    
    # Create user
    result = AuthService.create_user(
        email=data['email'],
        password=data['password'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        tier=data['tier'],
        region=data['region'],
        reason=data['reason']
    )
    
    return jsonify({
        'message': result.get('message', 'Registration successful! Please check your email to verify your account.')
    }), 201

@app.route('/verify', methods=['GET'])
def verify_email_link():
    """Email verification endpoint - handles verification links from emails"""
    token = request.args.get('token')
    if not token:
        return jsonify({'error': 'Missing token'}), 400
        
    result = AuthService.verify_email(token)
    if result['success']:
        # Redirect to WordPress success page
        return redirect('https://asi2.org/email-confirmed/')
    else:
        return jsonify({'error': result['error']}), 400

@app.route('/api/verify', methods=['GET', 'POST'])
def verify_email():
    """Email verification endpoint (API)"""
    # Handle GET request (from email link)
    if request.method == 'GET':
        token = request.args.get('token')
        if not token:
            return jsonify({'error': 'Missing token'}), 400
            
        result = AuthService.verify_email(token)
        if result['success']:
            # Redirect to WordPress success page
            return redirect('https://asi2.org/email-confirmed/')
        else:
            return jsonify({'error': result['error']}), 400

    # Handle POST request (legacy/manual)
    data = request.get_json()
    if not data or 'token' not in data:
        return jsonify({'error': 'Missing token'}), 400
    
    result = AuthService.verify_email(data['token'])
    if result['success']:
        return jsonify({'message': 'Email verified successfully'}), 200
    else:
        return jsonify({'error': result['error']}), 400

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'error': 'Missing email or password'}), 400
    
    result = AuthService.login(email, password)
    
    if result['success']:
        # Create JWT token (identity must be string)
        access_token = create_access_token(identity=str(result['user']['id']))
        
        return jsonify({
            'access_token': access_token,
            'user': result['user']
        }), 200
    else:
        return jsonify({'error': result['error']}), 401

@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user info"""
    user_id = int(get_jwt_identity())
    
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT id, email, first_name, last_name, tier, created_at 
            FROM users WHERE id = %s
        """, (user_id,))
        user = cursor.fetchone()
    
    if user:
        return jsonify(dict(user)), 200
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/api/password-reset/request', methods=['POST'])
def request_password_reset():
    """Request password reset email"""
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    result = AuthService.request_password_reset(email)
    return jsonify(result), 200

@app.route('/api/password-reset/confirm', methods=['POST'])
def confirm_password_reset():
    """Reset password with token"""
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')
    
    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400
    
    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    result = AuthService.reset_password(token, new_password)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

# ============================================================================
# SEARCH ROUTES
# ============================================================================

@app.route('/api/search', methods=['POST'])
@jwt_required()
def search():
    """Unified search endpoint"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    query = data.get('query', '').strip()
    sources = data.get('sources', ['internal'])  # Default to internal only
    tags = data.get('tags', [])
    year_from = data.get('year_from')
    asip_funded_only = data.get('asip_funded_only', False)
    
    if not query:
        return jsonify({'error': 'Query cannot be empty'}), 400
    
    # Perform search
    result = SearchService.unified_search(
        query=query,
        sources=sources,
        tags=tags,
        year_from=year_from,
        asip_funded_only=asip_funded_only,
        user_id=user_id
    )
    
    return jsonify({
        'papers': [paper.to_dict() for paper in result.papers],
        'total_count': result.total_count,
        'query': result.query,
        'sources_used': result.sources_used,
        'execution_time': round(result.execution_time, 2)
    }), 200

@app.route('/api/papers/featured', methods=['GET'])
def get_featured_papers():
    """Get ASIP-funded research highlights"""
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT * FROM papers 
            WHERE asip_funded = TRUE 
            ORDER BY year DESC, citation_count DESC 
            LIMIT 10
        """)
        rows = cursor.fetchall()
    
    from models import Paper
    papers = [Paper.from_db_row(row).to_dict() for row in rows]
    return jsonify({'papers': papers}), 200

@app.route('/api/papers/<int:paper_id>', methods=['GET'])
@jwt_required()
def get_paper(paper_id):
    """Get single paper details"""
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM papers WHERE id = %s", (paper_id,))
        row = cursor.fetchone()
    
    if row:
        from models import Paper
        paper = Paper.from_db_row(row)
        return jsonify(paper.to_dict()), 200
    else:
        return jsonify({'error': 'Paper not found'}), 404

@app.route('/api/papers/<int:paper_id>/references', methods=['GET'])
@jwt_required()
def get_paper_references(paper_id):
    """Get related papers (references) based on shared tags"""
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get the current paper's tags
        cursor.execute("SELECT tags FROM papers WHERE id = %s", (paper_id,))
        row = cursor.fetchone()
        
        if not row:
            return jsonify({'error': 'Paper not found'}), 404
        
        current_tags = row[0] if row[0] else ''
        
        if not current_tags:
            return jsonify({'references': []}), 200
        
        # Find papers with overlapping tags (excluding the current paper)
        # This is a simple implementation - in production, you'd have a proper citations table
        cursor.execute("""
            SELECT * FROM papers 
            WHERE id != %s 
            AND tags IS NOT NULL 
            AND tags != ''
            ORDER BY citation_count DESC, year DESC
            LIMIT 10
        """, (paper_id,))
        
        rows = cursor.fetchall()
    
    from models import Paper
    
    # Filter papers that share at least one tag
    current_tag_set = set(current_tags.lower().split(',')) if current_tags else set()
    related_papers = []
    
    for row in rows:
        paper = Paper.from_db_row(row)
        paper_tags = set(t.lower() for t in paper.tags) if paper.tags else set()
        
        # Check if there's any overlap
        if current_tag_set & paper_tags:
            related_papers.append(paper.to_dict())
        
        if len(related_papers) >= 5:  # Limit to 5 references
            break
    
    return jsonify({'references': related_papers}), 200

# ============================================================================
# BOOKMARK ROUTES
# ============================================================================

@app.route('/api/bookmarks', methods=['GET'])
@jwt_required()
def get_bookmarks():
    """Get user's bookmarked papers"""
    user_id = int(get_jwt_identity())
    
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT p.*, b.notes, b.created_at as bookmarked_at
            FROM papers p
            JOIN user_bookmarks b ON p.id = b.paper_id
            WHERE b.user_id = %s
            ORDER BY b.created_at DESC
        """, (user_id,))
        rows = cursor.fetchall()
    
    from models import Paper
    papers = [Paper.from_db_row(row).to_dict() for row in rows]
    return jsonify({'bookmarks': papers}), 200

@app.route('/api/bookmarks', methods=['POST'])
@jwt_required()
def add_bookmark():
    """Add paper to bookmarks"""
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    paper_id = data.get('paper_id')
    notes = data.get('notes', '')
    
    if not paper_id:
        return jsonify({'error': 'Missing paper_id'}), 400
    
    try:
        with get_db() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                INSERT INTO user_bookmarks (user_id, paper_id, notes)
                VALUES (%s, %s, %s)
            """, (user_id, paper_id, notes))
        
        return jsonify({'message': 'Bookmark added successfully'}), 201
    except Exception as e:
        return jsonify({'error': 'Bookmark already exists or paper not found'}), 400

@app.route('/api/bookmarks/<int:paper_id>', methods=['DELETE'])
@jwt_required()
def remove_bookmark(paper_id):
    """Remove paper from bookmarks"""
    user_id = int(get_jwt_identity())
    
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            DELETE FROM user_bookmarks 
            WHERE user_id = %s AND paper_id = %s
        """, (user_id, paper_id))
    
    return jsonify({'message': 'Bookmark removed successfully'}), 200

# ============================================================================
# ANALYTICS ROUTES (Admin only)
# ============================================================================

@app.route('/api/analytics/searches', methods=['GET'])
@jwt_required()
def get_search_analytics():
    """Get search analytics (simplified for V1)"""
    user_id = int(get_jwt_identity())
    
    # TODO: Add admin check in V2
    
    with get_db() as conn:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Top searches
        cursor.execute("""
            SELECT query, COUNT(*) as count 
            FROM search_logs 
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY query 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_searches = [row for row in cursor.fetchall()]
        
        # Searches by user tier
        cursor.execute("""
            SELECT u.tier, COUNT(*) as count 
            FROM search_logs s 
            JOIN users u ON s.user_id = u.id 
            WHERE s.created_at >= NOW() - INTERVAL '30 days'
            GROUP BY u.tier
        """)
        by_tier = [row for row in cursor.fetchall()]
        
        # Total searches
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM search_logs 
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)
        result = cursor.fetchone()
        total = result['total'] if result else 0
    
    return jsonify({
        'top_searches': top_searches,
        'by_tier': by_tier,
        'total_searches': total
    }), 200

# ============================================================================
# UTILITY ROUTES
# ============================================================================

@app.route('/api/tags', methods=['GET'])
def get_tags():
    """Get list of valid tags"""
    return jsonify({'tags': Config.VALID_TAGS}), 200

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': '1.0.0'}), 200

@app.route('/')
def index():
    """Serve test interface"""
    return app.send_static_file('index.html')

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    # Ensure upload directory exists
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    # Run app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
