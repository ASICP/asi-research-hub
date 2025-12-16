## ARA v2 - API Documentation

**Version:** 2.0.0
**Base URL:** `http://localhost:5000` (development)
**Authentication:** JWT Bearer tokens

---

## Table of Contents

1. [Authentication](#authentication)
2. [Papers](#papers)
3. [Tags](#tags)
4. [Bookmarks](#bookmarks)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)

---

## Authentication

### POST /api/register

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "tier": "researcher"  // Optional: student, researcher, institutional
}
```

**Response:** `201 Created`
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "tier": "researcher",
    "created_at": "2025-12-14T10:00:00Z"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer"
}
```

**Rate Limit:** 5 per hour

---

### POST /api/login

Authenticate and receive tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "tier": "researcher"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer"
}
```

**Rate Limit:** 10 per minute

---

### POST /api/refresh

Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer"
}
```

**Rate Limit:** 20 per hour

---

### POST /api/logout

Revoke refresh token (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

**Rate Limit:** 30 per hour

---

### GET /api/me

Get current user profile (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "tier": "researcher",
  "created_at": "2025-12-14T10:00:00Z",
  "last_active": "2025-12-14T12:30:00Z"
}
```

---

## Papers

### POST /api/papers/search

Search for papers across multiple sources.

**Headers (optional):**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "query": "AI alignment",
  "sources": ["semantic_scholar", "arxiv", "crossref"],  // Optional
  "max_results": 20,  // Optional, default: 20, max: 100
  "ingest": false,  // Optional, whether to save to DB
  "assign_tags": true  // Optional, auto-assign tags if ingesting
}
```

**Response:** `200 OK`

*Without ingestion (`ingest: false`):*
```json
{
  "total_fetched": 45,
  "papers": [
    {
      "source": "semantic_scholar",
      "source_id": "abc123",
      "doi": "10.1000/xyz",
      "arxiv_id": null,
      "title": "Paper Title",
      "abstract": "Abstract text...",
      "authors": ["Author One", "Author Two"],
      "year": 2024,
      "venue": "Conference Name",
      "citation_count": 42,
      "url": "https://..."
    }
  ]
}
```

*With ingestion (`ingest: true`):*
```json
{
  "total_fetched": 45,
  "total_ingested": 30,
  "new_papers": 20,
  "duplicates_found": 10,
  "fetch_stats": {
    "semantic_scholar": 20,
    "arxiv": 15,
    "crossref": 10
  },
  "papers": [...]  // Array of ingested Paper objects
}
```

**Rate Limit:** 30 per minute

---

### GET /api/papers

List papers from database with filtering and pagination.

**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Results per page (default: 20, max: 100)
- `tag` - Filter by tag name
- `year` - Filter by publication year
- `source` - Filter by source (semantic_scholar, arxiv, crossref)
- `sort` - Sort by (recent, citations, relevance) (default: recent)
- `q` - Search query (searches title and abstract)

**Example:**
```
GET /api/papers?tag=interpretability&year=2024&sort=citations&page=1&per_page=20
```

**Response:** `200 OK`
```json
{
  "total": 150,
  "page": 1,
  "per_page": 20,
  "total_pages": 8,
  "papers": [
    {
      "id": 1,
      "title": "Paper Title",
      "abstract": "Abstract text...",
      "authors": ["Author One", "Author Two"],
      "year": 2024,
      "venue": "Conference Name",
      "citation_count": 42,
      "url": "https://...",
      "created_at": "2025-12-14T10:00:00Z"
    }
  ]
}
```

---

### GET /api/papers/:id

Get detailed information about a specific paper.

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Paper Title",
  "abstract": "Abstract text...",
  "authors": ["Author One", "Author Two"],
  "year": 2024,
  "venue": "Conference Name",
  "citation_count": 42,
  "url": "https://...",
  "tags": [
    {
      "name": "interpretability",
      "slug": "interpretability",
      "confidence": 0.95
    }
  ],
  "cited_by": [
    {
      "id": 2,
      "title": "Citing Paper",
      "year": 2024,
      "authors": ["..."]
    }
  ],
  "references": [
    {
      "id": 3,
      "title": "Referenced Paper",
      "year": 2023,
      "authors": ["..."]
    }
  ]
}
```

---

### POST /api/papers/:id/citations

Build citation network for a paper (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "max_citations": 50,  // Optional, default: 50
  "max_references": 50  // Optional, default: 50
}
```

**Response:** `200 OK`
```json
{
  "citations_added": 25,
  "references_added": 30
}
```

**Rate Limit:** 10 per hour

---

### GET /api/papers/featured

Get top cited papers.

**Response:** `200 OK`
```json
{
  "papers": [...]  // Top 20 most cited papers
}
```

---

## Tags

### GET /api/tags

List all tags with statistics.

**Query Parameters:**
- `category` - Filter by category
- `min_papers` - Minimum paper count (default: 0)
- `sort` - Sort by (name, papers, recent) (default: papers)
- `limit` - Maximum number of tags to return

**Example:**
```
GET /api/tags?min_papers=5&sort=papers&limit=50
```

**Response:** `200 OK`
```json
{
  "total": 50,
  "tags": [
    {
      "id": 1,
      "name": "interpretability",
      "slug": "interpretability",
      "category": "core",
      "paper_count": 150,
      "description": "Research on model interpretability...",
      "created_at": "2025-12-14T10:00:00Z",
      "last_used": "2025-12-14T12:00:00Z"
    }
  ]
}
```

---

### GET /api/tags/:slug

Get detailed information about a specific tag.

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "interpretability",
  "slug": "interpretability",
  "category": "core",
  "paper_count": 150,
  "description": "Research on model interpretability...",
  "related_tags": [
    {
      "id": 2,
      "name": "explainability",
      "slug": "explainability",
      "co_occurrence_count": 75
    }
  ],
  "recent_papers": [
    {
      "id": 1,
      "title": "Recent Paper",
      "year": 2024,
      "authors": ["..."],
      "citation_count": 42
    }
  ]
}
```

---

### GET /api/tags/trending

Get trending tags.

**Query Parameters:**
- `limit` - Maximum number of tags (default: 10)

**Response:** `200 OK`
```json
{
  "tags": [...]  // Recently used tags with good paper counts
}
```

---

### GET /api/tags/combos

Get frequently occurring tag combinations.

**Query Parameters:**
- `min_count` - Minimum occurrence count (default: 2)
- `limit` - Maximum number of combos (default: 20)

**Response:** `200 OK`
```json
{
  "total": 15,
  "combos": [
    {
      "id": 1,
      "tag_ids": [1, 2, 5],
      "tags": [
        {"id": 1, "name": "interpretability", "slug": "interpretability"},
        {"id": 2, "name": "llm", "slug": "llm"},
        {"id": 5, "name": "alignment", "slug": "alignment"}
      ],
      "count": 25,
      "first_seen": "2025-12-01T00:00:00Z",
      "last_seen": "2025-12-14T12:00:00Z"
    }
  ]
}
```

---

### GET /api/tags/categories

Get all tag categories with counts.

**Response:** `200 OK`
```json
{
  "categories": [
    {
      "name": "core",
      "tag_count": 15,
      "paper_count": 500
    },
    {
      "name": "auto_assigned",
      "tag_count": 30,
      "paper_count": 300
    }
  ]
}
```

---

### GET /api/tags/search

Search for tags by name or description.

**Query Parameters:**
- `q` - Search query (required)
- `limit` - Maximum number of results (default: 20)

**Example:**
```
GET /api/tags/search?q=safety&limit=10
```

**Response:** `200 OK`
```json
{
  "total": 5,
  "tags": [
    {
      "id": 3,
      "name": "safety",
      "slug": "safety",
      "paper_count": 75,
      "description": "AI safety research..."
    }
  ]
}
```

---

## Bookmarks

**Note:** All bookmark endpoints require authentication.

### GET /api/bookmarks

Get current user's bookmarks.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `page` - Page number (default: 1)
- `per_page` - Results per page (default: 20, max: 100)
- `tag` - Filter by bookmark tag
- `sort` - Sort by (recent, title, year) (default: recent)

**Response:** `200 OK`
```json
{
  "total": 50,
  "page": 1,
  "per_page": 20,
  "total_pages": 3,
  "bookmarks": [
    {
      "id": 1,
      "paper_id": 42,
      "notes": "Important paper for my research",
      "tags": ["to-read", "important"],
      "created_at": "2025-12-14T10:00:00Z",
      "updated_at": "2025-12-14T11:00:00Z",
      "paper": {
        "id": 42,
        "title": "Paper Title",
        "authors": ["..."],
        "year": 2024
      }
    }
  ]
}
```

---

### POST /api/bookmarks

Create a new bookmark.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "paper_id": 42,
  "notes": "Important paper for my research",  // Optional
  "tags": ["to-read", "important"]  // Optional, max 10 tags
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "paper_id": 42,
  "notes": "Important paper for my research",
  "tags": ["to-read", "important"],
  "created_at": "2025-12-14T10:00:00Z"
}
```

**Rate Limit:** 30 per minute

---

### GET /api/bookmarks/:paper_id

Get a specific bookmark.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "paper_id": 42,
  "notes": "Important paper for my research",
  "tags": ["to-read", "important"],
  "created_at": "2025-12-14T10:00:00Z",
  "updated_at": "2025-12-14T11:00:00Z",
  "paper": {
    "id": 42,
    "title": "Paper Title",
    "abstract": "...",
    "authors": ["..."],
    "year": 2024
  }
}
```

---

### PATCH /api/bookmarks/:paper_id

Update bookmark notes and tags.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request:**
```json
{
  "notes": "Updated notes",  // Optional
  "tags": ["read", "important"]  // Optional
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "paper_id": 42,
  "notes": "Updated notes",
  "tags": ["read", "important"],
  "updated_at": "2025-12-14T12:00:00Z"
}
```

**Rate Limit:** 60 per minute

---

### DELETE /api/bookmarks/:paper_id

Delete a bookmark.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Bookmark deleted successfully"
}
```

**Rate Limit:** 30 per minute

---

### GET /api/bookmarks/stats

Get bookmark statistics for current user.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "total_bookmarks": 50,
  "most_used_tags": [
    {"tag": "to-read", "count": 25},
    {"tag": "important", "count": 15}
  ],
  "papers_by_year": {
    "2024": 30,
    "2023": 15,
    "2022": 5
  }
}
```

---

### GET /api/bookmarks/check/:paper_id

Check if a paper is bookmarked.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

*If bookmarked:*
```json
{
  "bookmarked": true,
  "bookmark": {
    "id": 1,
    "notes": "...",
    "tags": [...]
  }
}
```

*If not bookmarked:*
```json
{
  "bookmarked": false
}
```

---

## Error Handling

All errors follow a consistent format:

**Response:** `4xx` or `5xx`
```json
{
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "status": 400
}
```

### Common Error Codes

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | VALIDATION_ERROR | Invalid request data |
| 401 | AUTHENTICATION_ERROR | Invalid or missing authentication |
| 403 | AUTHORIZATION_ERROR | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource conflict (e.g., duplicate) |
| 429 | RATE_LIMIT_EXCEEDED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |

### Example Error Response

```json
{
  "error": "Password must be at least 12 characters",
  "error_code": "VALIDATION_ERROR",
  "status": 400
}
```

---

## Rate Limiting

Rate limits are enforced per endpoint and per IP address (or per user if authenticated).

**Rate Limit Headers:**
```
X-RateLimit-Limit: 30
X-RateLimit-Remaining: 25
X-RateLimit-Reset: 1702561200
```

### Default Limits

- **Global:** 1000 per day, 100 per hour
- **Registration:** 5 per hour
- **Login:** 10 per minute
- **Token Refresh:** 20 per hour
- **Search:** 30 per minute
- **Citation Building:** 10 per hour
- **Bookmark Creation:** 30 per minute
- **Bookmark Updates:** 60 per minute

---

## Authentication Flow

### 1. Register or Login

```bash
# Register
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!","tier":"researcher"}'

# Or Login
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'
```

Response includes `access_token` and `refresh_token`.

### 2. Use Access Token

```bash
curl http://localhost:5000/api/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 3. Refresh When Expired

```bash
curl -X POST http://localhost:5000/api/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
```

### 4. Logout

```bash
curl -X POST http://localhost:5000/api/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'
```

---

## Complete Examples

### Search and Bookmark Workflow

```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}' \
  | jq -r '.access_token')

# 2. Search for papers
curl -X POST http://localhost:5000/api/papers/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "mechanistic interpretability",
    "sources": ["semantic_scholar"],
    "max_results": 10,
    "ingest": true,
    "assign_tags": true
  }'

# 3. Get paper details
curl http://localhost:5000/api/papers/1

# 4. Bookmark paper
curl -X POST http://localhost:5000/api/bookmarks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "paper_id": 1,
    "notes": "Foundational paper on mechanistic interpretability",
    "tags": ["important", "to-read"]
  }'

# 5. List bookmarks
curl http://localhost:5000/api/bookmarks \
  -H "Authorization: Bearer $TOKEN"
```

---

## Pagination

All list endpoints support pagination:

**Query Parameters:**
- `page` - Page number (starts at 1)
- `per_page` - Results per page (max varies by endpoint)

**Response includes:**
```json
{
  "total": 150,
  "page": 1,
  "per_page": 20,
  "total_pages": 8,
  "items": [...]
}
```

**Navigation:**
- First page: `?page=1`
- Next page: `?page=2`
- Last page: `?page=8`

---

## Filtering and Sorting

### Papers Filtering

```bash
# By tag
GET /api/papers?tag=interpretability

# By year
GET /api/papers?year=2024

# By source
GET /api/papers?source=arxiv

# Search in title/abstract
GET /api/papers?q=alignment

# Combine filters
GET /api/papers?tag=safety&year=2024&sort=citations
```

### Tags Filtering

```bash
# By category
GET /api/tags?category=core

# Minimum paper count
GET /api/tags?min_papers=10

# Sort by name
GET /api/tags?sort=name

# Limit results
GET /api/tags?limit=50
```

---

## Notes

- All timestamps are in UTC and ISO 8601 format
- All requests must use `Content-Type: application/json`
- Authentication tokens expire (access: 24h, refresh: 30d)
- Rate limits reset hourly
- Soft-deleted papers are excluded from all queries
- Tag confidence scores range from 0.0 to 1.0

---

**For more information, see:**
- [README.md](README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - Setup guide
- [WEEK-2-COMPLETE.md](WEEK-2-COMPLETE.md) - Authentication details
- [WEEK-3-COMPLETE.md](WEEK-3-COMPLETE.md) - Paper search details
