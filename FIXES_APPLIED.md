# Fixes Applied

## 1. Robust Tag Parsing
- Updated `models.py` to handle invalid JSON in `tags` column.
- Now falls back to comma-separated string parsing or empty list.
- Prevents 500 Internal Server Error when encountering malformed tags.

## 2. Caching Issue Identified
- The "Full Paper View Coming Soon" alert is from an old version of the code.
- This confirms the browser is serving cached JavaScript.
- **Action Required**: Hard refresh (Cmd+Shift+R) to load the new code.

## 3. Server Restarted
- Restarted the Flask server to apply changes.
