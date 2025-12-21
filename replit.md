# ASI Research Hub

## Overview
ASI Research Hub is a production-ready AI alignment research portal designed for verified academics and researchers. Its core purpose is to facilitate the search, discovery, and organization of AI safety papers from both an internal curated database and external sources like Google Scholar. The project aims to provide professional features such as user authentication, email verification, full-text search, and bookmark management, all while maintaining a low-cost deployment model ($20/month on Replit).

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
The backend is built with Python Flask, following a RESTful API pattern with JWT authentication. It employs a modular, service-oriented architecture with `app.py` for routing, `auth.py` for authentication, `search.py` for unified search across internal and external sources, `models.py` for data entities, and `utils.py` for validation. Key design decisions include stateless JWT tokens, bcrypt for password hashing, and a service layer pattern for business logic separation.

### Frontend Architecture
The frontend uses vanilla JavaScript to achieve Single Page Application-like behavior across `search.html`, `register.html`, and `login.html`. Design choices include a dark mode by default with a theme toggle, a paper detail modal with keyword highlighting, and a responsive card-based layout. The choice of vanilla JS prioritizes simplicity and reduces deployment overhead.

### Data Storage
The system uses SQLite with Full-Text Search (FTS5) for data storage. The schema includes tables for `users`, `papers`, `bookmarks`, `searches`, and `tags`. SQLite was chosen for its zero-configuration deployment and Replit compatibility, with FTS5 enabling efficient full-text searches. JSON storage is used for flexible tagging.

### Authentication & Authorization
Authentication uses JWT tokens (24-hour validity) issued after email verification. Security measures include bcrypt for password hashing, secure random tokens, email verification with expiration, email case normalization, anti-enumeration tactics, and login rate limiting (5 failed attempts lead to a 5-minute lockout). Password reset functionality is also implemented with time-limited tokens.

### Search Functionality
The system provides a unified search interface capable of querying an internal database (SQLite FTS5), Google Scholar (via SerpAPI), arXiv, CrossRef, and Semantic Scholar. It supports filters by tags, year range, and funding status. The design incorporates a connector pattern for pluggable source integrations, result normalization, and deduplication to offer comprehensive research coverage at minimal cost.

### Email System
SendGrid is used for transactional emails such as account verification and password resets, leveraging its free tier (100 emails/day). The implementation includes SSL certificate verification and HTML email templates.

## External Dependencies

### Third-Party Services
1.  **SendGrid Email API**: For transactional emails (verification, password reset).
2.  **SerpAPI Google Scholar Integration**: Provides reliable Google Scholar search access.
3.  **arXiv, CrossRef, Semantic Scholar APIs**: Additional free-tier research paper sources.
4.  **Replit Hosting**: Recommended for deployment, offering always-on hosting and environment secrets.
5.  **Google reCAPTCHA v3**: Optional bot protection for registration.

### Python Packages
*   **Core Framework**: `Flask`, `Flask-CORS`, `Flask-JWT-Extended`.
*   **Security**: `bcrypt`, `validators`.
*   **PDF & Search**: `PyPDF2`, `feedparser`, `requests`.
*   **Email**: `sendgrid`.
*   **Production**: `gunicorn`.

### Database Integration
Currently uses **SQLite**. A migration path to PostgreSQL is supported for future scalability needs.

### WordPress Integration
The `search.html` page can be embedded into WordPress using an `<iframe>`, with CORS configured to allow interaction from specified origins.