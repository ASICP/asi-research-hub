# SerpAPI Google Scholar Setup

## Overview

This application uses **SerpAPI** for Google Scholar searches. SerpAPI handles all the complexity of accessing Google Scholar:

- ✅ Automatic proxy rotation
- ✅ Anti-scraping bypass
- ✅ CAPTCHA solving
- ✅ Rate limit management
- ✅ IP rotation

You just need an API key - SerpAPI handles everything else!

---

## Quick Setup

### 1. Get API Key

Sign up at [serpapi.com](https://serpapi.com/):

- **Free tier:** 100 searches/month
- **Paid plans:** Starting at $50/month for 5,000 searches

### 2. Add to Environment

Add your API key to `.env`:

```bash
SERPAPI_API_KEY=your_serpapi_key_here
```

### 3. Test It

Restart your application and try a Google Scholar search. You should see:

```
✓ Google Scholar (SerpAPI): Found 10 papers
```

---

## Configuration

### Environment Variable

```bash
# .env file
SERPAPI_API_KEY=your_serpapi_key_here
```

### Code Location

The SerpAPI connector is in:
```
ara_v2/services/connectors/serpapi_google_scholar.py
```

Used by:
```
search.py → search_google_scholar() method
```

---

## API Limits

| Plan | Searches/Month | Cost |
|------|----------------|------|
| Free | 100 | $0 |
| Starter | 5,000 | $50 |
| Developer | 15,000 | $125 |
| Production | 30,000+ | Custom |

Check your usage at: https://serpapi.com/dashboard

---

## Features

### Basic Search

```python
from ara_v2.services.connectors import SerpAPIGoogleScholarConnector

connector = SerpAPIGoogleScholarConnector(api_key=your_key)
results = connector.search_papers(
    query="machine learning",
    limit=10
)
```

### Advanced Filters

```python
results = connector.search_papers(
    query="neural networks",
    limit=20,
    year_low=2020,        # Papers from 2020 onwards
    year_high=2024,       # Papers up to 2024
    sort_by="date"        # or "relevance"
)
```

### Author Search

```python
papers = connector.get_author_papers(
    author_name="Geoffrey Hinton",
    limit=10
)
```

### Citation Search

```python
# Find papers citing a specific paper
citing_papers = connector.search_by_citation(
    citing_paper_id="cluster_id_here",
    limit=10
)
```

---

## Error Handling

### No API Key

```
⚠️ SerpAPI key not configured. Set SERPAPI_API_KEY in .env
   Get API key from https://serpapi.com/ (100 free searches/month)
```

**Fix:** Add `SERPAPI_API_KEY` to your `.env` file

### Rate Limit Exceeded

```
⚠️ Google Scholar API error: HTTPError: 429 Too Many Requests
```

**Fix:** Wait for your monthly limit to reset or upgrade your plan

### Invalid API Key

```
⚠️ SerpAPI configuration error: Invalid API key
```

**Fix:** Check your API key at https://serpapi.com/dashboard

---

## Comparison: SerpAPI vs scholarly Library

| Feature | SerpAPI | scholarly |
|---------|---------|-----------|
| Setup | Easy (just API key) | Complex (proxies, Tor, etc.) |
| Reliability | Very High (99.9% uptime) | Low (frequently blocked) |
| Maintenance | None (SerpAPI handles it) | High (constant proxy issues) |
| Cost | $50/month (5K searches) | Free but unreliable |
| Speed | Fast (< 2 seconds) | Slow (3-10 seconds with Tor) |
| Success Rate | 99%+ | < 20% without proxy |

**Recommendation:** Use SerpAPI for production. The $50/month is worth it for reliable Google Scholar access.

---

## Alternative Sources

If you want to avoid SerpAPI costs, use these reliable free alternatives:

### 1. Semantic Scholar
- **Free tier:** 100 requests per 5 minutes
- **Reliability:** Excellent
- **Coverage:** 200M+ papers

```bash
# .env
SEMANTIC_SCHOLAR_API_KEY=your_key  # Optional but recommended
```

### 2. arXiv
- **Free:** Unlimited with polite delays
- **Reliability:** Excellent
- **Coverage:** STEM papers (physics, CS, math, etc.)

No configuration needed - works out of the box!

### 3. CrossRef
- **Free:** Unlimited
- **Reliability:** Excellent
- **Coverage:** Comprehensive academic metadata

```bash
# .env
CROSSREF_EMAIL=your-email@example.com  # Required for polite pool
```

---

## Migration from scholarly Library

If you previously used the `scholarly` library:

### Old Code (scholarly)
```python
from scholarly import scholarly

search_query = scholarly.search_pubs('machine learning')
for pub in search_query:
    print(pub['bib']['title'])
```

### New Code (SerpAPI)
```python
from ara_v2.services.connectors import SerpAPIGoogleScholarConnector

connector = SerpAPIGoogleScholarConnector(api_key=api_key)
results = connector.search_papers('machine learning')
for paper in results['papers']:
    print(paper['title'])
```

---

## Troubleshooting

### Q: Search returns 0 results but query is valid

**A:** Check your SerpAPI dashboard for errors. Ensure your API key is active and has remaining searches.

### Q: Slow searches (> 5 seconds)

**A:** SerpAPI should be fast (< 2 sec). If slow, check:
- Your internet connection
- SerpAPI status: https://status.serpapi.com/

### Q: Want to reduce costs

**A:** Options:
1. Cache results in your database (already implemented in ARA v2)
2. Use alternative sources first (Semantic Scholar, arXiv)
3. Only use Google Scholar for specific queries not found elsewhere

---

## Support

- **SerpAPI Docs:** https://serpapi.com/google-scholar-api
- **SerpAPI Support:** support@serpapi.com
- **Dashboard:** https://serpapi.com/dashboard
- **Status:** https://status.serpapi.com/

---

## Summary

✅ **Setup is simple:**
1. Get API key from serpapi.com
2. Add to `.env` as `SERPAPI_API_KEY`
3. Restart application

✅ **Benefits:**
- No proxy configuration needed
- Handles all anti-scraping automatically
- Reliable 99%+ uptime
- Fast (< 2 second responses)

✅ **Cost:**
- Free: 100 searches/month
- Paid: $50/month for 5,000 searches
- Alternative: Use free sources (Semantic Scholar, arXiv, CrossRef)
