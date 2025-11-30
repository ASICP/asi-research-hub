# Replit Deployment Guide

## Quick Setup (5 minutes)

### 1. Import from GitHub
- Click "Create Repl" → "Import from GitHub"
- Paste: `https://github.com/ASICP/asi-research-hub`
- Click "Import from GitHub"

### 2. Configure Secrets
Go to **Tools** → **Secrets** and add these 7 required secrets:

**⚠️ IMPORTANT**: Contact the project administrator to get the actual secret values. Do NOT use the example values below.

```
SECRET_KEY = [Get from project admin - Flask session security key]
JWT_SECRET_KEY = [Get from project admin - JWT token signing key]
SENDGRID_API_KEY = [Get from project admin - SendGrid email service key]
SENDGRID_FROM_EMAIL = team@asi2.org
FRONTEND_URL = https://asi2.org
RECAPTCHA_SITE_KEY = [Get from project admin - Google reCAPTCHA site key]
RECAPTCHA_SECRET_KEY = [Get from project admin - Google reCAPTCHA secret]
```

**Need the secrets?** If you're the project owner, check your local `.env` file or password manager.

### 3. Initialize Database
Run this command once in the Shell:
```bash
python database.py
```

### 4. Run the App
Click the **Run** button at the top!

## Troubleshooting

### Database doesn't exist
```bash
python database.py
```

### Dependencies missing
```bash
pip install -r requirements.txt
```

### Check system status
```bash
python check_system.py
```

### Port already in use
The app will automatically use Replit's PORT environment variable.

## Production Deployment

To deploy publicly:
1. Click **Deploy** button
2. Choose deployment type (Reserved VM recommended for databases)
3. Your app will be live at: `https://your-repl-name.username.repl.co`

## Database Persistence

**Important**: Replit's free tier may not persist the SQLite database across restarts. For production:
- Upgrade to a paid plan with persistent storage
- Or migrate to PostgreSQL/external database

## What's Included

- ✅ 100+ AI Safety research papers
- ✅ Full-text search
- ✅ User authentication & email verification
- ✅ Paper upload & management
- ✅ Citation tracking
- ✅ Responsive UI

## Support

For issues, check:
- README.md - Main documentation
- QUICKSTART.md - Detailed setup
- STRUCTURE.md - Architecture overview
