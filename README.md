# ASI Research Hub - Combined Repository

This repository contains **two AI alignment research applications**:

1. **ASI Research Hub v1** - Original deployment guide and codebase
2. **ARA v2 (Project Holmes)** - New intelligent research discovery engine

---

## 🆕 ARA v2 - Aligned Research App (Project Holmes)

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

###  Overview

ARA v2 transforms the Aligned Research App into an **intelligent research discovery engine** that identifies:

- **Highly Relevant** (Top 10%): Papers aligned with popular tags and strong citation networks
- **Highly Novel** (Top 0-2%): "Diamonds in the rough" with original ideas

### ✅ Phase 1 Complete (Foundation)
- ✅ User authentication & session management (JWT + Redis)
- ✅ Search multiple academic sources (Semantic Scholar, ArXiv, CrossRef)
- ✅ Automatic tag assignment using hybrid ML approach
- ✅ Paper bookmarking with notes
- ✅ 26 API endpoints fully functional
- ✅ 295+ comprehensive tests (82% coverage)

### 📊 ARA v2 Status
- **API Endpoints**: 26 fully functional
- **Test Coverage**: 82% (295+ tests)
- **External APIs**: 3 connectors (all free, no API keys required)
- **Documentation**: Complete ([API-DOCUMENTATION.md](API-DOCUMENTATION.md))

### 🚀 ARA v2 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Seed tags
python scripts/seed_tags.py

# Run tests
pytest

# Start application
python -m ara_v2.app
```

### 📚 ARA v2 Documentation
- [API Documentation](API-DOCUMENTATION.md) - Complete API reference
- [Phase 1 Complete](PHASE-1-COMPLETE.md) - Implementation summary
- [Enhancements Complete](ENHANCEMENTS-COMPLETE.md) - Test coverage report
- [Deployment Guide](DEPLOYMENT-READY.md) - Deployment instructions

---

## 📋 ASI Research Hub v1 - Original Application

### Overview

The ASI Research Hub v1 is an AI alignment research portal that allows verified users to search across:
- Internal curated AI safety papers (PDFs)
- Google Scholar (free API)
- Future: Perplexity, You.com, and other research databases

**Version**: 1.0.0
**Tech Stack**: Python Flask (backend) + React (frontend)

### Quick Start (v1 Deployment)

#### Step 1: Create Project

1. Go to [Replit.com](https://replit.com)
2. Click "Create Repl"
3. Use a "Python" template
4. Name it: `asi-research-hub`

#### Step 2: Upload Pre-Tested Files

Upload v1 files to your Replit:
- `app.py` - Main Flask application
- `config.py` - Configuration
- `database.py` - Database utilities
- `auth.py` - Authentication service
- `search.py` - Search functionality
- `models.py` - Data models
- `utils.py` - Helper functions
- `upload_papers.py` - Script to add sample papers

#### Step 3: Set Environment Variables

In Replit, go to "Tools" → "Secrets" and add:

```
SECRET_KEY = your-secret-key-here
JWT_SECRET_KEY = your-jwt-secret-key-here
SENDGRID_API_KEY = your-sendgrid-api-key
FRONTEND_URL = https://asi2.org
```

**Generate secure keys**:
```python
import secrets
print(secrets.token_hex(32))
```

---

## 🗂️ Repository Structure

```
├── ara_v2/                    # ARA v2 Application Code
│   ├── api/                   # API endpoints
│   ├── models/                # Database models
│   ├── services/              # Business logic
│   │   └── connectors/        # External API connectors
│   └── utils/                 # Utilities
├── tests/                     # Test suite (295+ tests)
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── alembic/                   # Database migrations
├── scripts/                   # Utility scripts
├── app.py                     # v1 main application
├── auth.py                    # v1 authentication
├── search.py                  # v1 search functionality
└── requirements.txt           # Combined dependencies (v1 + v2)
```

---

## 🔧 Development

### Running Tests (ARA v2)

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ara_v2 --cov-report=html

# Run specific test file
pytest tests/unit/test_tag_assigner.py -v
```

### Code Quality

```bash
# Format code
black ara_v2/

# Lint
flake8 ara_v2/

# Sort imports
isort ara_v2/

# Security scan
bandit -r ara_v2/
```

---

## 📖 Documentation Index

### ARA v2 Documentation
- [API Documentation](API-DOCUMENTATION.md)
- [Phase 1 Complete](PHASE-1-COMPLETE.md)
- [Enhancements Complete](ENHANCEMENTS-COMPLETE.md)
- [Deployment Ready](DEPLOYMENT-READY.md)
- [Project Status](PROJECT-STATUS.md)

### v1 Documentation
- [Quick Start](QUICKSTART.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Replit Setup](REPLIT_SETUP.md)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details

---

## 🆘 Support

For issues or questions:
- ARA v2: Check [DEPLOYMENT-READY.md](DEPLOYMENT-READY.md)
- v1: Check [QUICKSTART.md](QUICKSTART.md)

---

**Last Updated**: December 15, 2025
**Status**: Both applications production-ready ✅
