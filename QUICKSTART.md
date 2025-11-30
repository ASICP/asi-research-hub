# 🚀 QUICK START GUIDE

## Get Your ASI Research Hub Running in 15 Minutes

### Step 1: Upload to Replit (2 minutes)

1. Go to [replit.com](https://replit.com) and sign in
2. Click **"Create Repl"**
3. Choose **"Python"** template
4. Name it: `asi-research-hub`
5. Upload all files from this folder

### Step 2: Set Secrets (3 minutes)

Click the **🔒 lock icon** in left sidebar, then add:

```
SECRET_KEY = paste-output-from-command-below
JWT_SECRET_KEY = paste-output-from-command-below
SENDGRID_API_KEY = get-from-sendgrid.com
FRONTEND_URL = https://asi2.org
```

**Generate keys** (run in Replit Shell):
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Run this twice to get two different keys.

### Step 3: Install & Setup (5 minutes)

In Replit Shell, run these commands:

```bash
# Install dependencies
pip install -r requirements.txt

# Check everything is working
python check_system.py

# Initialize database
python -c "from database import init_db; init_db()"

# Add sample papers
python upload_papers.py
```

### Step 4: Run the App (1 minute)

Click the green **▶ Run** button at top.

Your API is now live at: `https://asi-research-hub.YOUR-USERNAME.repl.co`

### Step 5: Test It (4 minutes)

#### Test Health Check
Open: `https://asi-research-hub.YOUR-USERNAME.repl.co/api/health`

You should see: `{"status": "healthy", "version": "1.0.0"}`

#### Test Registration
Open Replit's Web View and navigate to your API URL + `/api/register`

Or use curl in Shell:
```bash
curl -X POST https://asi-research-hub.YOUR-USERNAME.repl.co/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User",
    "tier": "researcher",
    "reason": "Testing"
  }'
```

#### Test Featured Papers
```bash
curl https://asi-research-hub.YOUR-USERNAME.repl.co/api/papers/featured
```

You should see 3 ASIP-funded papers!

---

## 🎨 Add to WordPress (5 minutes)

### Simple Embed

1. Edit your asi2.org page in WordPress
2. Add HTML block
3. Paste this code:

```html
<div style="width: 100%; max-width: 1400px; margin: 0 auto; padding: 20px;">
    <iframe 
        src="https://asi-research-hub.YOUR-USERNAME.repl.co" 
        width="100%" 
        height="900px" 
        frameborder="0"
        style="border: none; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);"
    ></iframe>
</div>
```

4. Replace `YOUR-USERNAME` with your Replit username
5. Save and publish

---

## 📧 Email Setup (Optional but Recommended)

### SendGrid Free Tier Setup

1. Go to [sendgrid.com/free](https://sendgrid.com/free)
2. Sign up (100 emails/day free)
3. Verify your account
4. Go to **Settings → Sender Authentication**
5. Verify **noreply@asi2.org**
6. Go to **Settings → API Keys**
7. Create new key (Full Access)
8. Copy key and add to Replit Secrets as `SENDGRID_API_KEY`

Without this, users won't receive verification emails (but you can verify them manually).

---

## 🔧 Common Issues

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Database locked"
Stop the app and run again. Only one process can access SQLite.

### "CORS error" in WordPress
Check `FRONTEND_URL` in Secrets matches your WordPress domain exactly.

### Emails not sending
- Check SendGrid API key is correct
- Verify sender email at sendgrid.com
- Check Replit logs for errors

---

## ✅ You're Done!

Your Research Hub is now:
- ✅ Running on Replit
- ✅ Accepting user registrations
- ✅ Searchable with 10 sample papers
- ✅ Ready to embed in WordPress

### Next Steps:

1. **Add your own papers**: Edit `upload_papers.py`
2. **Customize tags**: Edit `config.py` → `VALID_TAGS`
3. **Monitor usage**: Check `/api/analytics/searches`
4. **Upgrade Replit**: Get Hacker plan for always-on hosting ($20/mo)

---

## 📞 Need Help?

1. Run `python check_system.py` to diagnose issues
2. Check `README.md` for detailed documentation
3. Review error logs in Replit console

---

**Total Time**: ~15 minutes  
**Monthly Cost**: $20 (Replit Hacker)  
**Status**: Production Ready ✅
