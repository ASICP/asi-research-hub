# ASI Research Hub - Deployment Guide

## 📋 Overview

The ASI Research Hub is an AI alignment research portal that allows verified users to search across:
- Internal curated AI safety papers (PDFs)
- Google Scholar (free API)
- Future: Perplexity, You.com, and other research databases

**Version**: 1.0.0  
**Tech Stack**: Python Flask (backend) + React (frontend)

---

## 🚀 Quick Start (Deployment)

### Step 1: Create Project

1. Go to [Replit.com](https://replit.com)
2. Click "Create Repl"
3. Use a "Python" template
4. Name it: `asi-research-hub`

### Step 2: Upload these Pre-Tested Files

Upload all files from this package to your Replit:
- `app.py` - Main Flask application
- `config.py` - Configuration
- `database.py` - Database utilities
- `auth.py` - Authentication service
- `search.py` - Search functionality
- `models.py` - Data models
- `utils.py` - Helper functions
- `requirements.txt` - Python dependencies
- `upload_papers.py` - Script to add sample papers

### Step 3: Set Environment Variables

In Replit (other), go to "Tools" → "Secrets" and add:

```
SECRET_KEY = your-secret-key-here-change-in-production
JWT_SECRET_KEY = your-jwt-secret-key-here
SENDGRID_API_KEY = your-sendgrid-api-key
FRONTEND_URL = https://asi2.org
```

**Generate secure keys**:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Step 4: Install Dependencies

In Replit Shell, run:
```bash
pip install -r requirements.txt
```

### Step 5: Initialize Database

```bash
python -c "from database import init_db; init_db()"
```

### Step 6: Add Sample Papers

```bash
python upload_papers.py
```

This will add 10 AI safety research papers to test the system.

### Step 7: Run the App

```bash
python app.py
```

Your API will be available at: `https://asi-research-hub.YOUR-USERNAME.repl.co`

---

## 📧 SendGrid Email Setup

### 1. Sign Up for SendGrid

- Go to [sendgrid.com](https://sendgrid.com)
- Create free account (100 emails/day)

### 2. Verify Sender Email

- Go to Settings → Sender Authentication
- Verify `noreply@asi2.org`
- Complete email verification

### 3. Create API Key

- Go to Settings → API Keys
- Create new API key (Full Access)
- Copy key and add to Replit Secrets

### 4. Test Email

```bash
python -c "from auth import AuthService; AuthService.send_verification_email('test@example.com', 'Test', 'abc123')"
```

---

## 🌐 WordPress Integration

### Option A: Iframe Embed (Recommended for V1)

Add this to your WordPress page:

```html
<div style="width: 100%; max-width: 1200px; margin: 0 auto;">
    <iframe 
        src="https://asi-research-hub.YOUR-USERNAME.repl.co" 
        width="100%" 
        height="900px" 
        frameborder="0"
        style="border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"
    ></iframe>
</div>
```

### Option B: Subdomain Setup (Advanced)

1. In Replit, upgrade to Hacker plan
2. Go to Replit project settings
3. Link custom domain: `hub.asi2.org`
4. Update DNS settings at your domain provider

---

## 🧪 Testing the API

### Test Registration

```bash
curl -X POST https://YOUR-REPLIT-URL/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User",
    "tier": "researcher",
    "reason": "Testing the system"
  }'
```

### Test Login

```bash
curl -X POST https://YOUR-REPLIT-URL/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

Save the `access_token` from the response.

### Test Search

```bash
curl -X POST https://YOUR-REPLIT-URL/api/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "query": "interpretability",
    "sources": ["internal"]
  }'
```

### Test Featured Papers

```bash
curl https://YOUR-REPLIT-URL/api/papers/featured
```

---

## 📁 Adding Your Own Papers

### Method 1: Using Python Script

Edit `upload_papers.py` and add your papers:

```python
upload_paper(
    title="Your Paper Title",
    authors="Author Names",
    year=2024,
    abstract="Brief description...",
    pdf_path="static/uploads/your-paper.pdf",  # Optional
    tags=["interpretability", "technical_safety"],
    arxiv_id="2401.12345",  # Optional
    doi="10.1234/example",  # Optional
    asip_funded=True,  # If ASIP funded
    citation_count=50
)
```

Then run:
```bash
python upload_papers.py
```

### Method 2: Direct SQL

```sql
INSERT INTO papers (title, authors, year, abstract, tags, asip_funded)
VALUES (
    'Paper Title',
    'Author Names',
    2024,
    'Abstract text',
    '["interpretability", "robustness"]',
    FALSE
);
```

---

## 📊 Database Schema

### Users Table
- `id` - Primary key
- `email` - Unique email address
- `password_hash` - Bcrypt hashed password
- `first_name`, `last_name` - User name
- `tier` - student, researcher, or institutional
- `is_verified` - Email verification status
- `verification_token` - One-time verification token

### Papers Table
- `id` - Primary key
- `title` - Paper title
- `authors` - Comma-separated authors
- `abstract` - Paper abstract
- `year` - Publication year
- `tags` - JSON array of tags
- `asip_funded` - Boolean flag
- `pdf_path` - Path to PDF file
- `pdf_text` - Extracted full text for search

### User Bookmarks Table
- Links users to their saved papers

### Search Logs Table
- Tracks all searches for analytics

---

## 🔒 Security Best Practices

### 1. Change Default Keys

**CRITICAL**: Change `SECRET_KEY` and `JWT_SECRET_KEY` in production!

```python
import secrets
print(secrets.token_urlsafe(32))  # Generate secure key
```

### 2. Enable HTTPS

Replit provides HTTPS by default. Always use `https://` URLs.

### 3. Rate Limiting (V2)

Consider adding Flask-Limiter:
```bash
pip install Flask-Limiter
```

### 4. Input Validation

All endpoints validate input. Don't disable validation checks.

### 5. SQL Injection Protection

All queries use parameterized statements. Never use string concatenation.

---

## 📈 Monitoring & Analytics

### View Search Analytics

```bash
curl -X GET https://YOUR-REPLIT-URL/api/analytics/searches \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Database Stats

```bash
sqlite3 asi_research_hub.db "SELECT COUNT(*) FROM users WHERE is_verified = TRUE;"
sqlite3 asi_research_hub.db "SELECT COUNT(*) FROM papers;"
sqlite3 asi_research_hub.db "SELECT COUNT(*) FROM search_logs;"
```

### Daily Backup

Add this to your routine:
```bash
cp asi_research_hub.db backups/backup_$(date +%Y%m%d).db
```

---

## 🐛 Troubleshooting

### Problem: "Database locked" error

**Solution**: Only one process should access SQLite at a time. Restart Replit.

### Problem: Email not sending

**Solutions**:
1. Check SendGrid API key in Secrets
2. Verify sender email in SendGrid dashboard
3. Check logs for error messages
4. Manually get verification token from database:
   ```sql
   SELECT verification_token FROM users WHERE email = 'user@example.com';
   ```

### Problem: Google Scholar not working

**Solution**: Google Scholar can rate-limit. Add delays or use internal search only.

### Problem: CORS errors in WordPress

**Solution**: Check `FRONTEND_URL` in config.py matches your WordPress domain.

### Problem: "Module not found" errors

**Solution**: 
```bash
pip install -r requirements.txt
```

---

## 🚦 Next Steps

### Week 1: Launch
- [ ] Deploy to Replit
- [ ] Configure SendGrid
- [ ] Add 20-30 curated papers
- [ ] Test all features
- [ ] Embed in WordPress

### Week 2: User Testing
- [ ] Invite 5-10 beta testers
- [ ] Gather feedback
- [ ] Fix bugs
- [ ] Monitor usage

### Month 2: Version 2 Planning
- [ ] Review analytics
- [ ] Prioritize features
- [ ] Consider adding Perplexity API
- [ ] Plan RAG/AI assistant

---

## 📞 Support

For issues or questions:
1. Check this README
2. Review error logs in Replit
3. Contact your development team

---

## 📄 License

Proprietary - ASI Institute 2025

---

## 🎯 Success Metrics

Track these KPIs:

**Week 1**:
- 20+ verified users
- 50+ searches
- 0 critical bugs

**Month 1**:
- 50+ verified users
- 200+ searches
- 10+ bookmarked papers

**Month 3**:
- 100+ users
- 500+ searches
- User feedback gathered

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Deployment Guide by**: ASI Institute Development Team
