# ASI Research Hub

## Overview

ASI Research Hub is a production-ready AI alignment research portal that enables verified academics and researchers to search, discover, and organize AI safety papers. The system provides access to both an internal curated database of AI safety research papers and external sources like Google Scholar. Built with Python Flask backend and vanilla JavaScript frontend, it's designed for low-cost deployment ($20/month on Replit) while maintaining professional features like user authentication, email verification, full-text search, and bookmark management.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes & TODO

**Recent Updates (Dec 1, 2025)**:
- ✅ Migrated entire codebase from SQLite to PostgreSQL (100% compatible, all SQL uses %s placeholders)
- ✅ Fixed critical search bug in search.py (SQLite placeholder → PostgreSQL syntax)
- ✅ Restored session timeout: 15-minute inactivity logout with 10-minute warning popup
- ✅ Added mutually exclusive source selection (Internal Database OR Google Scholar only)
- ✅ Google Scholar papers now display "Explore Paper" button linking to original source
- ✅ Google Scholar Reference Papers sidebar auto-populates with related Internal Database papers
- ✅ Added reference links (arXiv/DOI/PDF) in Reference Papers sidebar

**TODO - When stable (remind in ~3 days)**:
- Set up automatic Github push integration for version control backup
- Ensure all bugs resolved before enabling auto-sync to Github

## System Architecture

### Backend Architecture

**Framework**: Python Flask  
**Pattern**: RESTful API with JWT authentication

The backend follows a modular service-oriented architecture:

- **`app.py`**: Main application entry point containing all API route handlers. Implements CORS for WordPress embedding and handles request/response cycles.
- **`auth.py`**: Authentication service handling user registration, login, password hashing (bcrypt), email verification tokens, and password reset flows.
- **`search.py`**: Search service providing unified search across internal database (full-text SQLite FTS) and external sources (Google Scholar API).
- **`models.py`**: Data models for User and Paper entities using Python dataclasses for type safety and serialization.
- **`utils.py`**: Validation utilities for emails, passwords, file uploads, and text processing.

**Design Decisions**:
- JWT tokens for stateless authentication (24-hour expiration)
- bcrypt for password hashing (security standard)
- Service layer pattern separates business logic from routing
- Context manager pattern (`@contextmanager`) for database connections ensures proper resource cleanup

### Frontend Architecture

**Technology**: Vanilla JavaScript (no framework)  
**Pattern**: Single Page Application behavior with multiple HTML files

Three separate pages for different use cases:
- **`search.html`**: Main search interface (embeddable in WordPress via iframe)
- **`register.html`**: User registration with password confirmation
- **`login.html`**: User login with password reset functionality

**Design Decisions**:
- Dark mode by default (avoiding pure black #0a0e27 for better contrast)
- Theme toggle persists in localStorage
- Paper detail modal with keyword highlighting and reference sidebar
- Clickable tags for related paper discovery
- Responsive card-based design with hover effects

**Why vanilla JS**: Reduces complexity, deployment size, and eliminates build steps. Suitable for the application's moderate interactivity needs.

### Data Storage

**Database**: SQLite with Full-Text Search (FTS5)

**Schema** (5 core tables):
1. **users**: Authentication, profile, tier (student/researcher/institutional), verification status
2. **papers**: Research papers with full-text content, tags (JSON array), ArXiv/DOI identifiers, ASIP funding flag
3. **bookmarks**: User-paper relationships for saved research
4. **searches**: Search analytics and query logging
5. **tags**: Standardized taxonomy of 148+ AI safety tags

**Design Decisions**:
- SQLite chosen for zero-configuration deployment and Replit compatibility
- FTS5 enables fast full-text search across titles, abstracts, authors, and PDF content
- JSON storage for tags allows flexible tagging without junction tables
- Row-level factory pattern (`sqlite3.Row`) returns dictionary-like objects

**Trade-offs**:
- **Pro**: File-based, no separate database server, simple backups
- **Con**: Not suitable for ephemeral filesystems (Heroku), limited concurrency
- **Migration Path**: Architecture supports switching to PostgreSQL by updating `database.py`

### Authentication & Authorization

**Flow**:
1. User registers → Email sent with verification token
2. User clicks link → Token verified → Account activated
3. User logs in → JWT token issued (24hr validity)
4. Protected endpoints require JWT in Authorization header

**Security Measures**:
- bcrypt password hashing (salt rounds automatically managed)
- Secure random tokens (`secrets.token_urlsafe(32)`)
- Email verification prevents spam accounts
- JWT secret rotation supported via environment variables
- CORS restricted to allowed origins (asi2.org + localhost)

**Password Reset**:
- Time-limited reset tokens stored in database
- Tokens expire after use or timeout
- SendGrid email delivery with fallback console logging for development

### Search Functionality

**Unified Search Interface**:
- **Internal Database**: SQLite FTS5 searches across title, authors, abstract, full PDF text
- **Google Scholar**: Free API integration via `scholarly` library with rate limiting
- **Filters**: Tags, year range, ASIP-funded only, source selection

**Design Decisions**:
- Search service abstracts complexity from API layer
- Results normalized to common `SearchResult` model regardless of source
- Rate limiting prevents Google Scholar API abuse
- PDF text extraction via PyPDF2 enables full-content search

**Why this approach**: Provides researchers with comprehensive coverage while keeping costs minimal (no paid API subscriptions required).

### Email System

**Service**: SendGrid (free tier: 100 emails/day)  
**Use Cases**: Account verification, password reset, future notifications

**Implementation**:
- SSL certificate verification via `certifi` package
- Environment-based configuration (API key, sender email)
- HTML email templates for professional appearance
- Graceful fallback: Development mode logs tokens to console instead of sending

**Design Decision**: SendGrid chosen for reliability, deliverability, and free tier suitability for moderate academic use.

### File Management

**Storage**: Local filesystem (`static/uploads/`)  
**Supported Formats**: PDF, TXT (16MB max size)

**Process**:
1. Upload → Filename sanitization (`werkzeug.secure_filename`)
2. PDF text extraction → Stored in database for search
3. File path stored as relative reference

**Security**: Filename sanitization prevents directory traversal attacks

## External Dependencies

### Third-Party Services

1. **SendGrid Email API**
   - Purpose: Transactional emails (verification, password reset)
   - Cost: Free tier (100 emails/day)
   - Configuration: API key + verified sender email
   - Alternative: SMTP server (requires additional setup)

2. **Google Scholar API** (via `scholarly` library)
   - Purpose: External research paper search
   - Cost: Free (rate-limited)
   - Integration: Python library with exponential backoff
   - Limitation: ~100 queries/hour recommended

3. **Replit Hosting** (recommended deployment)
   - Purpose: Always-on hosting
   - Cost: $20/month (Hacker plan)
   - Features: Auto-restart, environment secrets, custom domains
   - Alternative: DigitalOcean, Heroku, or any Python-capable host

4. **Google reCAPTCHA v3** (configured but optional)
   - Purpose: Bot protection on registration
   - Cost: Free
   - Configuration: Site key + secret key

### Python Packages

**Core Framework**:
- `Flask==3.0.0`: Web framework
- `Flask-CORS==4.0.0`: Cross-origin request handling
- `Flask-JWT-Extended==4.5.3`: JWT authentication

**Security**:
- `bcrypt==4.1.1`: Password hashing
- `validators==0.22.0`: Input validation

**PDF & Search**:
- `PyPDF2==3.0.1`: PDF text extraction
- `scholarly==1.7.11`: Google Scholar integration

**Email**:
- `sendgrid==6.11.0`: Email delivery

**Production**:
- `gunicorn==21.2.0`: WSGI production server (4 workers recommended)

### Database Integration

**Current**: SQLite (file-based, included with Python)  
**Future PostgreSQL Migration** (if needed):
- Update `database.py` to use SQLAlchemy or psycopg2
- Modify connection string in environment variables
- Re-run migrations
- Suitable for high-concurrency or cloud platforms with ephemeral storage

### WordPress Integration

**Method**: iframe embedding  
**Endpoint**: `/static/search.html`  
**CORS**: Configured to allow asi2.org origin  
**Embedding Code**:
```html
<iframe src="https://your-replit-url.repl.co/static/search.html" 
        width="100%" height="800px" frameborder="0"></iframe>
```

**Why iframe**: Simplest integration method, preserves authentication state, no WordPress plugin development required.