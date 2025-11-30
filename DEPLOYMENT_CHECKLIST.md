# ✅ ASI Research Hub - Deployment Checklist

## Pre-Deployment Checklist

### Phase 1: Local Setup & Testing (Week 1)

#### Day 1: Environment Setup
- [ ] Install Python 3.9+ on local machine
- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate venv: `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Generate secure keys (run twice):
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Create `.env` file from `.env.template`
- [ ] Add generated keys to `.env`

#### Day 2: Database & Data
- [ ] Initialize database: `python -c "from database import init_db; init_db()"`
- [ ] Verify tables created: Check `asi_research_hub.db` exists
- [ ] Upload sample papers: `python upload_papers.py`
- [ ] Run system check: `python check_system.py`
- [ ] Verify all checks pass ✅

#### Day 3: Local Testing
- [ ] Start Flask app: `python app.py`
- [ ] Test health endpoint: Visit `http://localhost:5000/api/health`
- [ ] Open test interface: Visit `http://localhost:5000`
- [ ] Test registration with dummy email
- [ ] Manually verify user in database (since no SendGrid yet):
  ```sql
  UPDATE users SET is_verified = TRUE WHERE email = 'test@example.com';
  ```
- [ ] Test login with verified user
- [ ] Test search functionality
- [ ] Test featured papers endpoint
- [ ] Test bookmark functionality

#### Day 4: Add Real Papers
- [ ] Collect 20-30 AI safety PDFs from arXiv
- [ ] Place in `static/uploads/` directory
- [ ] Edit `upload_papers.py` with real paper metadata
- [ ] Run upload script: `python upload_papers.py`
- [ ] Test search with real papers
- [ ] Verify full-text search works

#### Day 5: SendGrid Setup
- [ ] Sign up at sendgrid.com (free tier)
- [ ] Complete account verification
- [ ] Verify sender email: `noreply@asi2.org`
- [ ] Create API key (Full Access)
- [ ] Add to `.env`: `SENDGRID_API_KEY=your-key`
- [ ] Test email: `python -c "from auth import AuthService; AuthService.send_verification_email('your-email@asi2.org', 'Test', 'abc123')"`
- [ ] Verify email received
- [ ] Test full registration flow with email verification

---

## Replit Deployment Checklist

### Phase 2: Replit Setup (Day 6-7)

#### Replit Account Setup
- [ ] Create account at replit.com
- [ ] Upgrade to Hacker plan ($20/month)
  - Provides: Always-on, 4GB RAM, faster CPU
  - Required for production use

#### Create Repl
- [ ] Click "Create Repl"
- [ ] Select "Python" template
- [ ] Name: `asi-research-hub`
- [ ] Click "Create Repl"

#### Upload Files
- [ ] Upload all Python files:
  - [ ] `app.py`
  - [ ] `config.py`
  - [ ] `database.py`
  - [ ] `auth.py`
  - [ ] `search.py`
  - [ ] `models.py`
  - [ ] `utils.py`
  - [ ] `upload_papers.py`
  - [ ] `check_system.py`
- [ ] Upload documentation:
  - [ ] `README.md`
  - [ ] `QUICKSTART.md`
  - [ ] `STRUCTURE.md`
  - [ ] `requirements.txt`
  - [ ] `.env.template`
- [ ] Upload static files:
  - [ ] `static/index.html`
- [ ] Create `static/uploads/` directory
- [ ] Upload your curated PDFs to `static/uploads/`

#### Configure Secrets
- [ ] Click 🔒 Lock icon in left sidebar
- [ ] Add secrets:
  ```
  SECRET_KEY = [paste generated key]
  JWT_SECRET_KEY = [paste generated key]
  SENDGRID_API_KEY = [paste SendGrid key]
  FRONTEND_URL = https://asi2.org
  ```
- [ ] Save each secret

#### Initialize in Replit
- [ ] Open Shell tab
- [ ] Run: `pip install -r requirements.txt`
  - Wait for completion (2-3 minutes)
- [ ] Run: `python check_system.py`
  - Verify all checks pass ✅
- [ ] Run: `python -c "from database import init_db; init_db()"`
- [ ] Run: `python upload_papers.py`
  - Verify papers uploaded successfully

#### Test in Replit
- [ ] Click green "Run" button
- [ ] Wait for app to start
- [ ] Note your URL: `https://asi-research-hub.YOUR-USERNAME.repl.co`
- [ ] Test health: Visit `YOUR-URL/api/health`
  - Should show: `{"status": "healthy", "version": "1.0.0"}`
- [ ] Test interface: Visit `YOUR-URL/`
- [ ] Test all features:
  - [ ] Registration
  - [ ] Login
  - [ ] Search
  - [ ] Featured papers

---

## WordPress Integration Checklist

### Phase 3: WordPress Embed (Day 7)

#### Create WordPress Page
- [ ] Log into WordPress admin at asi2.org
- [ ] Create new page: "Research Hub"
- [ ] Set URL slug: `hub` or `research-hub`

#### Embed Iframe
- [ ] Switch to "Code Editor" mode
- [ ] Paste embed code:
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
- [ ] Replace `YOUR-USERNAME` with your Replit username
- [ ] Save as draft
- [ ] Preview page
- [ ] Verify iframe loads correctly
- [ ] Test functionality in iframe
- [ ] Publish page

#### Add Navigation
- [ ] Go to Appearance → Menus
- [ ] Add "Research Hub" to main menu
- [ ] Save menu
- [ ] Visit asi2.org
- [ ] Verify menu link works

#### SEO Setup
- [ ] Add page title: "AI Safety Research Hub"
- [ ] Add meta description: "Search and explore AI alignment research papers..."
- [ ] Add featured image (optional)
- [ ] Submit to Google Search Console

---

## Production Checklist

### Phase 4: Go Live (Day 8-10)

#### Security Hardening
- [ ] Verify SECRET_KEY is NOT default value
- [ ] Verify JWT_SECRET_KEY is NOT default value
- [ ] Verify Replit is set to Private (not public)
- [ ] Test CORS only allows asi2.org
- [ ] Review all error messages (no sensitive data exposed)
- [ ] Enable Replit's Always-On feature
- [ ] Set up Replit monitoring/alerts

#### Database Backup
- [ ] Create `backups/` directory in Replit
- [ ] Manually backup database:
  ```bash
  cp asi_research_hub.db backups/backup_$(date +%Y%m%d).db
  ```
- [ ] Schedule weekly backups (manual until automated)
- [ ] Test restore from backup

#### Documentation
- [ ] Update README.md with production URL
- [ ] Document admin procedures
- [ ] Create runbook for common issues
- [ ] Document emergency contacts

#### User Testing
- [ ] Invite 5-10 beta testers
- [ ] Provide test credentials
- [ ] Collect feedback via form
- [ ] Monitor error logs
- [ ] Fix critical bugs immediately

#### Analytics Setup
- [ ] Verify search logging works
- [ ] Check analytics endpoint: `/api/analytics/searches`
- [ ] Create weekly analytics review process
- [ ] Set up usage monitoring dashboard

---

## Post-Launch Checklist

### Week 1 After Launch

#### Daily Monitoring
- [ ] Check Replit uptime
- [ ] Review error logs
- [ ] Monitor SendGrid deliverability
- [ ] Check database size
- [ ] Verify API response times

#### User Support
- [ ] Create support email: support@asi2.org
- [ ] Set up ticket system or shared inbox
- [ ] Document common user questions
- [ ] Create FAQ page

#### Content
- [ ] Add 10+ new papers weekly
- [ ] Tag all papers correctly
- [ ] Mark ASIP-funded research
- [ ] Keep abstracts updated

### Month 1 Goals

#### Metrics to Track
- [ ] Total registered users: Target 50+
- [ ] Verified users: Target 40+
- [ ] Total searches: Target 200+
- [ ] Papers bookmarked: Target 20+
- [ ] Search success rate: Target 80%+

#### User Feedback
- [ ] Survey 10+ users
- [ ] Identify top 3 requested features
- [ ] Plan Version 2 roadmap
- [ ] Estimate V2 timeline

#### Performance
- [ ] Average search time: Target <2s
- [ ] API uptime: Target 99%+
- [ ] Email delivery rate: Target 95%+
- [ ] Zero critical bugs

---

## Version 2 Preparation

### Month 2-3 Planning

#### Technical Improvements
- [ ] Evaluate Perplexity API integration
- [ ] Research RAG/AI assistant options
- [ ] Plan PostgreSQL migration
- [ ] Design advanced filtering UI
- [ ] Plan mobile app (if needed)

#### Features to Consider
- [ ] User profiles & preferences
- [ ] Social features (following, sharing)
- [ ] Paper annotations & notes
- [ ] Citation graph visualization
- [ ] Email digests of new papers
- [ ] Integration with Zotero/Mendeley
- [ ] Discussion forums
- [ ] Collaborative collections

#### Infrastructure
- [ ] Evaluate moving from Replit to AWS/GCP
- [ ] Plan CDN for static assets
- [ ] Consider Redis for caching
- [ ] Set up proper CI/CD pipeline
- [ ] Implement automated testing

---

## Emergency Procedures

### If Site Goes Down

1. **Check Replit Status**
   - Log into Replit
   - Check if app is running
   - Click "Stop" then "Run" to restart

2. **Check Logs**
   - Review Replit console logs
   - Look for error messages
   - Check database locks

3. **Database Issues**
   - Stop app
   - Copy database to backup
   - Restart app
   - If corrupt, restore from backup

4. **SendGrid Issues**
   - Check SendGrid dashboard
   - Verify API key is valid
   - Check sender verification status
   - Review rate limits

5. **CORS Issues**
   - Verify FRONTEND_URL in Secrets
   - Check WordPress domain hasn't changed
   - Clear browser cache

### Contact Information

- **Replit Support**: support@replit.com
- **SendGrid Support**: support.sendgrid.com
- **Internal Team**: [Add your contacts]

---

## Success Criteria

### Launch Success (Week 1)
- ✅ Site accessible 24/7
- ✅ 20+ verified users
- ✅ 50+ searches performed
- ✅ 0 critical bugs
- ✅ Email delivery working
- ✅ Positive user feedback

### Month 1 Success
- ✅ 50+ verified users
- ✅ 200+ searches
- ✅ 10+ bookmarked papers
- ✅ 99%+ uptime
- ✅ User feedback collected
- ✅ V2 roadmap created

### Month 3 Success
- ✅ 100+ verified users
- ✅ 500+ searches
- ✅ 30+ curated papers added
- ✅ Integration with academic outreach
- ✅ Positive ROI on $20/month cost
- ✅ Clear path to Version 2

---

## Sign-Off

### Pre-Launch Sign-Off

- [ ] Technical Lead: All systems tested ✅
- [ ] Project Manager: Checklist complete ✅
- [ ] Security: No critical vulnerabilities ✅
- [ ] Legal: Terms of Service reviewed ✅
- [ ] CEO: Approved for launch ✅

**Launch Date**: _______________

**Launched By**: _______________

**Production URL**: _______________

---

**Checklist Version**: 1.0  
**Last Updated**: November 2025  
**Next Review**: After Month 1
