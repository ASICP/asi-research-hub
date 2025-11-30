# Deployment Guide for ASI Research Hub

Your application is functionally ready for deployment! Here are the steps to ensure a smooth production launch.

## 1. Prerequisites

- **Codebase**: Ensure all files are committed.
- **Requirements**: `requirements.txt` now includes `gunicorn` for production serving.

## 2. Environment Variables (CRITICAL)

In your production environment (Replit, Heroku, DigitalOcean, etc.), you **MUST** set the following environment variables. **DO NOT** rely on the `.env` file in production if possible, or ensure it is not publicly accessible.

| Variable | Value | Description |
|----------|-------|-------------|
| `FLASK_APP` | `app.py` | Entry point |
| `FLASK_ENV` | `production` | Disables debug mode |
| `SECRET_KEY` | `[Generate a Long Random String]` | For session security |
| `JWT_SECRET_KEY` | `[Generate a Long Random String]` | For API token security |
| `SENDGRID_API_KEY` | `SG...` | Your SendGrid Key |
| `SENDGRID_FROM_EMAIL` | `team@asi2.org` | Verified Sender Email |
| `RECAPTCHA_SITE_KEY` | `...` | Google reCAPTCHA v3 Site Key |
| `RECAPTCHA_SECRET_KEY` | `...` | Google reCAPTCHA v3 Secret Key |
| `FRONTEND_URL` | `https://asi2.org` | For CORS and Redirects |

## 3. Running in Production

Do **NOT** use `python app.py` in production. Use `gunicorn`:

```bash
gunicorn -w 4 -b 0.0.0.0:8080 app:app
```

- `-w 4`: Runs 4 worker processes (adjust based on CPU cores).
- `-b 0.0.0.0:8080`: Binds to port 8080 (standard for many cloud platforms).

## 4. Database Considerations

### SQLite (Current)
- **Pros**: Zero configuration, file-based.
- **Cons**: If your deployment platform has an **ephemeral filesystem** (like Heroku or some Docker containers), your database **WILL BE WIPED** every time you redeploy or restart.
- **Replit**: Replit persists files, so SQLite is fine there.
- **Production Recommendation**: For robust production, consider switching to PostgreSQL.
  - Update `database.py` to use `SQLAlchemy` or `psycopg2` if you switch.

## 5. WordPress Integration

To embed the search page in WordPress:
1. Create a new page in WordPress (e.g., `/research-hub`).
2. Add a **Custom HTML** block.
3. Paste an `iframe` code pointing to your deployed app:
   ```html
   <iframe src="https://your-deployed-app-url.com/static/search.html" style="width:100%; height:1000px; border:none;"></iframe>
   ```
   *Note: You might need to adjust the height or use a script to auto-resize.*

## 6. Final Checklist

- [ ] All environment variables set?
- [ ] `gunicorn` installed?
- [ ] Database persistence strategy confirmed?
- [ ] CORS `FRONTEND_URL` matches your WordPress domain?
- [ ] ReCAPTCHA domains updated (add your production domain to Google Admin console)?

## 7. Future Roadmap (Post-Deployment)

- **PDF Viewer (Option B)**: Implement custom PDF.js viewer.
- **Real Citations**: Populate database with actual citation links.
- **User Profiles**: Allow users to save papers/bookmarks.
