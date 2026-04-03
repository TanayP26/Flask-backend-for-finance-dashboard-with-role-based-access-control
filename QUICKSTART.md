# Quick Start Guide

Get the Finance Dashboard Backend running in under 5 minutes.

---

## Prerequisites

- Python 3.7+ installed
- pip (comes with Python)

## Setup

```bash
# 1. Go to project folder
cd finance-backend

# 2. (Optional but recommended) Create virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
python app.py
```

Server will start at **http://localhost:5000**

---

## Demo Credentials

| Role     | Username       | Password     |
|----------|---------------|-------------|
| Viewer   | viewer_user   | viewer123   |
| Analyst  | analyst_user  | analyst123  |
| Admin    | admin_user    | admin123    |

---

## Quick Test Commands

### Check if server is running
```bash
curl http://localhost:5000/health
```

### Login
```bash
curl -X POST http://localhost:5000/auth/login -H "Content-Type: application/json" -d "{\"username\":\"admin_user\",\"password\":\"admin123\"}"
```

### View your profile
```bash
curl http://localhost:5000/auth/me -H "Authorization: Bearer analyst_user:analyst123"
```

### List records
```bash
curl http://localhost:5000/records -H "Authorization: Bearer analyst_user:analyst123"
```

### Create a record
```bash
curl -X POST http://localhost:5000/records -H "Authorization: Bearer analyst_user:analyst123" -H "Content-Type: application/json" -d "{\"amount\":5000,\"type\":\"income\",\"category\":\"Salary\",\"description\":\"Monthly salary\",\"record_date\":\"2024-01-31\"}"
```

### Dashboard summary
```bash
curl http://localhost:5000/dashboard/summary -H "Authorization: Bearer analyst_user:analyst123"
```

### Category breakdown
```bash
curl http://localhost:5000/dashboard/category-breakdown -H "Authorization: Bearer analyst_user:analyst123"
```

---

## Authentication

Use the `Authorization` header with `Bearer username:password` format:

```
Authorization: Bearer analyst_user:analyst123
```

---

## Resetting the Database

If you want to start fresh, just delete the `finance.db` file and restart the server. It'll recreate everything with the demo data.

```bash
del finance.db
python app.py
```

---

## Need Help?

Check the full [README.md](README.md) for detailed API documentation, curl examples, and architecture explanation.
