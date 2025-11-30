# 📁 ASI Research Hub - Project Structure

## File Overview

```
asi-research-hub/
│
├── 📄 app.py                    # Main Flask application (API endpoints)
├── 📄 config.py                 # Configuration settings
├── 📄 database.py               # Database utilities and initialization
├── 📄 auth.py                   # Authentication service (register, login, verify)
├── 📄 search.py                 # Search functionality (internal + Google Scholar)
├── 📄 models.py                 # Data models (User, Paper, SearchResult)
├── 📄 utils.py                  # Helper functions (validation, file handling)
│
├── 📄 requirements.txt          # Python dependencies
├── 📄 .env.template             # Environment variables template
│
├── 📄 upload_papers.py          # Script to add papers to database
├── 📄 check_system.py           # System verification script
│
├── 📄 README.md                 # Comprehensive documentation
├── 📄 QUICKSTART.md             # 15-minute setup guide
├── 📄 STRUCTURE.md              # This file
│
├── 📁 static/
│   ├── 📄 index.html            # Test interface
│   └── 📁 uploads/              # PDF storage (created automatically)
│
└── 🗄️ asi_research_hub.db      # SQLite database (created on first run)
```

---

## Core Files Explained

### 🔧 Backend Core

#### `app.py` - Main Application
- All API endpoints
- Request handling
- CORS configuration
- JWT authentication
- Error handling

**Key Routes**:
- `/api/register` - User registration
- `/api/login` - User authentication
- `/api/verify` - Email verification
- `/api/search` - Unified search
- `/api/papers/featured` - ASIP-funded papers
- `/api/bookmarks` - Save/retrieve papers
- `/api/analytics` - Usage statistics

#### `config.py` - Configuration
- Environment variables
- Security keys
- API limits
- Valid tags list
- File upload settings

**Key Settings**:
- `SECRET_KEY` - Flask session security
- `JWT_SECRET_KEY` - Token signing
- `SENDGRID_API_KEY` - Email service
- `PERPLEXITY_MONTHLY_LIMIT` - Cost control (500/month)
- `VALID_TAGS` - Research categories

#### `database.py` - Database Layer
- SQLite connection management
- Database initialization
- Schema creation
- Context managers

**Tables Created**:
- `users` - User accounts
- `papers` - Research papers
- `user_bookmarks` - Saved papers
- `search_logs` - Analytics
- `api_usage` - Cost tracking

#### `auth.py` - Authentication Service
- Password hashing (bcrypt)
- User registration
- Email verification
- Login validation
- JWT token generation

**Key Functions**:
- `create_user()` - Register new user
- `verify_email()` - Confirm email
- `login()` - Authenticate user
- `send_verification_email()` - SendGrid integration

#### `search.py` - Search Service
- Internal database search
- Google Scholar integration
- API rate limiting
- Search logging
- Result aggregation

**Key Functions**:
- `search_internal()` - Full-text search on PDFs
- `search_google_scholar()` - External search
- `unified_search()` - Combine sources
- `check_api_limit()` - Cost control

#### `models.py` - Data Models
- User model
- Paper model
- SearchResult model
- BibTeX generation

**Key Classes**:
- `User` - User data structure
- `Paper` - Paper with tags, citations
- `SearchResult` - Search response wrapper

#### `utils.py` - Helper Functions
- Email validation
- Password validation
- File upload handling
- Keyword extraction

---

### 🛠️ Helper Scripts

#### `upload_papers.py` - Paper Uploader
Add papers to database:
```python
upload_paper(
    title="Paper Title",
    authors="Author Names",
    year=2024,
    tags=["interpretability"],
    asip_funded=True
)
```

#### `check_system.py` - System Verification
Checks:
- Dependencies installed
- Database initialized
- Configuration set
- Basic functionality

Run: `python check_system.py`

---

### 📚 Documentation

#### `README.md` - Full Documentation
- Complete deployment guide
- API documentation
- Troubleshooting
- Security best practices
- Cost breakdown

#### `QUICKSTART.md` - Fast Setup
- 15-minute deployment
- Step-by-step instructions
- Quick testing guide

#### `STRUCTURE.md` - This File
- Project organization
- File explanations
- Database schema
- Development workflow

---

## Database Schema

### `users` Table
```sql
id              INTEGER PRIMARY KEY
email           TEXT UNIQUE NOT NULL
password_hash   TEXT NOT NULL
first_name      TEXT NOT NULL
last_name       TEXT NOT NULL
tier            TEXT NOT NULL (student/researcher/institutional)
reason          TEXT NOT NULL
is_verified     BOOLEAN DEFAULT FALSE
verification_token TEXT
created_at      TIMESTAMP
last_login      TIMESTAMP
```

### `papers` Table
```sql
id              INTEGER PRIMARY KEY
title           TEXT NOT NULL
authors         TEXT NOT NULL
abstract        TEXT
year            INTEGER
source          TEXT (arxiv/internal/etc)
arxiv_id        TEXT
doi             TEXT
pdf_path        TEXT
pdf_text        TEXT (for full-text search)
asip_funded     BOOLEAN
tags            TEXT (JSON array)
citation_count  INTEGER
added_by        INTEGER (user_id)
created_at      TIMESTAMP
```

### `user_bookmarks` Table
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER NOT NULL
paper_id        INTEGER NOT NULL
notes           TEXT
created_at      TIMESTAMP
```

### `search_logs` Table
```sql
id              INTEGER PRIMARY KEY
user_id         INTEGER
query           TEXT NOT NULL
sources         TEXT (JSON array)
tags_filter     TEXT (JSON array)
result_count    INTEGER
created_at      TIMESTAMP
```

### `api_usage` Table
```sql
id              INTEGER PRIMARY KEY
service         TEXT (perplexity/youcom)
month           TEXT (YYYY-MM)
call_count      INTEGER
updated_at      TIMESTAMP
```

---

## API Endpoints Reference

### Public Endpoints (No Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register` | Create user account |
| POST | `/api/login` | Get JWT token |
| POST | `/api/verify` | Verify email |
| GET | `/api/papers/featured` | Get ASIP papers |
| GET | `/api/tags` | Get valid tags |
| GET | `/api/health` | Health check |

### Protected Endpoints (JWT Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/me` | Current user info |
| POST | `/api/search` | Search papers |
| GET | `/api/papers/:id` | Get paper details |
| GET | `/api/bookmarks` | User's bookmarks |
| POST | `/api/bookmarks` | Add bookmark |
| DELETE | `/api/bookmarks/:id` | Remove bookmark |
| GET | `/api/analytics/searches` | Search analytics |

---

## Development Workflow

### 1. Initial Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from database import init_db; init_db()"

# Add sample papers
python upload_papers.py

# Verify system
python check_system.py
```

### 2. Running Locally
```bash
# Set environment variables
export SECRET_KEY="your-secret-key"
export JWT_SECRET_KEY="your-jwt-key"
export SENDGRID_API_KEY="your-sendgrid-key"

# Run app
python app.py
```

### 3. Testing
```bash
# Test registration
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123",...}'

# Test search
curl -X POST http://localhost:5000/api/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query":"interpretability","sources":["internal"]}'
```

### 4. Adding Papers
```python
# Edit upload_papers.py
upload_paper(
    title="Your Paper",
    authors="Authors",
    year=2024,
    tags=["interpretability"],
    asip_funded=True
)

# Run script
python upload_papers.py
```

### 5. Deployment to Replit
1. Upload all files
2. Set Secrets (environment variables)
3. Click Run
4. Monitor logs for errors

---

## Environment Variables

Required in Replit Secrets:

```
SECRET_KEY              # Flask session security
JWT_SECRET_KEY          # JWT token signing
SENDGRID_API_KEY        # Email verification
FRONTEND_URL            # CORS (https://asi2.org)
PERPLEXITY_API_KEY      # Optional for V2
```

Generate secure keys:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Version 2 Roadmap

### Planned Features

1. **Perplexity Integration**
   - Add to search sources
   - Implement cost caps (500/month)
   - Update `search.py`

2. **RAG AI Assistant**
   - Answer questions about papers
   - Use LangChain + ChromaDB
   - Implement in new `ai_assistant.py`

3. **Advanced Filtering**
   - Date range picker
   - Citation count filter
   - Multiple tag selection

4. **User Profiles**
   - Save search history
   - Custom preferences
   - Research interests

5. **Social Features**
   - Follow researchers
   - Share collections
   - Comment on papers

---

## File Modification Guide

### To Add New API Endpoint:
**Edit**: `app.py`
```python
@app.route('/api/your-endpoint', methods=['GET'])
@jwt_required()
def your_function():
    # Your code here
    return jsonify({'data': 'result'}), 200
```

### To Add New Database Table:
**Edit**: `database.py` → `init_db()` function
```sql
CREATE TABLE IF NOT EXISTS your_table (
    id INTEGER PRIMARY KEY,
    field TEXT NOT NULL
);
```

### To Add New Tag Category:
**Edit**: `config.py` → `VALID_TAGS` list
```python
VALID_TAGS = [
    'existing_tag',
    'your_new_tag'
]
```

### To Change Email Template:
**Edit**: `auth.py` → `send_verification_email()` function

### To Modify Search Logic:
**Edit**: `search.py` → `unified_search()` function

---

## Security Notes

### Critical Security Settings

1. **Change Default Keys**: Never use default SECRET_KEY in production
2. **HTTPS Only**: Always use HTTPS URLs (Replit provides this)
3. **JWT Expiry**: Tokens expire after 24 hours
4. **Password Hashing**: bcrypt with salt (automatic)
5. **SQL Injection**: All queries use parameterization
6. **CORS**: Limited to FRONTEND_URL only

### Security Checklist

- [ ] Changed SECRET_KEY from default
- [ ] Changed JWT_SECRET_KEY from default
- [ ] SendGrid API key in Secrets (not code)
- [ ] FRONTEND_URL matches WordPress domain exactly
- [ ] Replit set to private (not public fork)
- [ ] Database backups scheduled

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Module not found | `pip install -r requirements.txt` |
| Database locked | Restart app (only one process allowed) |
| CORS error | Check FRONTEND_URL matches exactly |
| Email not sending | Verify SendGrid API key + sender email |
| 401 Unauthorized | Check JWT token in Authorization header |
| Search returns 0 | Run `python upload_papers.py` first |

---

## Support & Resources

- **Full Documentation**: README.md
- **Quick Setup**: QUICKSTART.md
- **System Check**: `python check_system.py`
- **Database Backup**: `cp asi_research_hub.db backups/backup.db`

---

**Project Version**: 1.0.0  
**Last Updated**: November 2025  
**Maintainer**: ASI Institute Development Team
