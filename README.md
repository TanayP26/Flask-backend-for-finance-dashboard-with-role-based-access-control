# Finance Dashboard Backend API

A Flask-based REST API for managing financial records with role-based access control. This project implements user management, financial records CRUD, and dashboard analytics — all backed by SQLite for zero-setup persistence.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Setup Instructions](#setup-instructions)
4. [Authentication](#authentication)
5. [API Endpoints](#api-endpoints)
   - [Auth Routes](#auth-routes)
   - [User Routes](#user-routes)
   - [Financial Records Routes](#financial-records-routes)
   - [Dashboard Routes](#dashboard-routes)
6. [Role Permissions](#role-permissions)
7. [Database Schema](#database-schema)
8. [Error Handling](#error-handling)
9. [Testing with cURL](#testing-with-curl)
10. [Design Decisions](#design-decisions)
11. [Assumptions](#assumptions)

---

## Project Overview

### What does this project do?

This is a backend system for a finance dashboard application. Think of it like a simplified version of what you'd find behind apps like Splitwise or Walnut — it tracks your income and expenses, gives you summaries, and lets admins manage everything.

The main features are:

- **User Management**: Create, update, and delete user accounts with different roles
- **Financial Records**: Full CRUD (Create, Read, Update, Delete) for income and expense entries
- **Role-Based Access**: Three roles (Viewer, Analyst, Admin) with different permission levels
- **Dashboard Analytics**: Summary stats, category breakdowns, monthly trends, and insights
- **Audit Logging**: Every create/update/delete operation is logged for accountability

### Why Flask?

I chose Flask because it's lightweight and doesn't force you into a particular project structure. For a project like this where we need a clean REST API without a lot of overhead, Flask is a good fit. Django would have been overkill with its ORM and admin panel that we don't really need here.

### Why SQLite?

SQLite is perfect for this use case because:
- No separate database server to install or configure
- The database is just a single file (`finance.db`)
- It supports all the SQL features we need (JOINs, aggregations, constraints)
- Easy to reset — just delete the file and restart the server

---

## Architecture

### Project Structure

```
finance-backend/
├── app.py                      # Main Flask app, error handlers, blueprints
├── database.py                 # SQLite connection, schema initialization
├── models.py                   # User, Role, FinancialRecord data models
├── middleware.py                # Authentication & authorization decorators
├── utils/
│   ├── __init__.py             # Validation functions
│   └── errors.py               # Custom error classes
├── routes/
│   ├── __init__.py             # Package marker
│   ├── auth_routes.py          # Login and profile endpoints
│   ├── user_routes.py          # User CRUD (admin-only for writes)
│   ├── record_routes.py        # Financial records CRUD
│   └── dashboard_routes.py     # Analytics and summary endpoints
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── QUICKSTART.md               # Quick setup guide
└── finance.db                  # Auto-generated SQLite database
```

### How the code is organized

The project follows a **layered architecture** pattern:

1. **Routes Layer** (`routes/`): Handles HTTP requests and responses. Each route file is a Flask Blueprint that groups related endpoints. Routes are responsible for parsing request data, calling the appropriate model methods, and returning JSON responses.

2. **Model Layer** (`models.py`): Contains all database queries. Each model class (Role, User, FinancialRecord) has static methods that perform SQL operations. This keeps the database logic separate from the HTTP handling logic.

3. **Middleware Layer** (`middleware.py`): Cross-cutting concerns like authentication and authorization are handled here using Python decorators. This means we can add `@authenticate_user` to any route and it automatically handles the auth check.

4. **Utilities Layer** (`utils/`): Input validation functions and custom error classes. Every piece of user input goes through validation before it touches the database.

5. **Database Layer** (`database.py`): Manages the SQLite connection, creates tables on startup, and seeds initial data (demo users and sample records).

### Data flow for a typical request

```
Client Request
    ↓
Flask Route Handler (routes/)
    ↓
Middleware Check (middleware.py)
    ↓ (authenticate + authorize)
Input Validation (utils/)
    ↓
Model Method (models.py)
    ↓
Database Query (database.py → SQLite)
    ↓
JSON Response back to Client
```

---

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Step 1: Clone or download the project

```bash
cd finance-backend
```

### Step 2: Create a virtual environment (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

This installs Flask 2.3.3 and Werkzeug 2.3.7. That's it — no other external dependencies.

### Step 4: Run the application

```bash
python app.py
```

You should see output like:
```
==================================================
  Finance Dashboard Backend
  Starting up...
==================================================
[+] Database initialized successfully!
[+] Inserted 26 sample financial records

[+] Server is ready!
[+] Running at: http://localhost:5000
[+] Press Ctrl+C to stop
```

### Step 5: Verify it's working

Open your browser and go to `http://localhost:5000`. You should see a JSON response with API information.

Or use curl:
```bash
curl http://localhost:5000
```

---

## Authentication

### How authentication works

This project uses a simplified Bearer token authentication. In a production system, you'd use JWT (JSON Web Tokens) with proper password hashing, but for this demo, we keep it straightforward.

### Login Flow

1. Send a POST request to `/auth/login` with your username and password
2. The server validates your credentials and returns an `auth_token`
3. Include this token in the `Authorization` header for all subsequent requests

### Token Format

The auth token is simply `username:password` encoded in the header:

```
Authorization: Bearer username:password
```

### Example

```bash
# Step 1: Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst_user", "password": "analyst123"}'

# Response includes auth_token: "analyst_user:analyst123"

# Step 2: Use the token in subsequent requests
curl http://localhost:5000/auth/me \
  -H "Authorization: Bearer analyst_user:analyst123"
```

### Demo Credentials

| Username       | Password     | Role     |
|---------------|-------------|----------|
| viewer_user   | viewer123   | Viewer   |
| analyst_user  | analyst123  | Analyst  |
| admin_user    | admin123    | Admin    |

### What happens without authentication?

If you try to access a protected endpoint without the Authorization header, you'll get a 401 response:

```json
{
  "error": "UnauthorizedError",
  "message": "Missing Authorization header. Please login first."
}
```

---

## API Endpoints

### Auth Routes

#### POST /auth/login

Login with username and password.

**Request:**
```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "analyst_user", "password": "analyst123"}'
```

**Response (200):**
```json
{
  "message": "Login successful!",
  "auth_token": "analyst_user:analyst123",
  "user": {
    "id": 2,
    "username": "analyst_user",
    "email": "analyst@example.com",
    "role_id": 2,
    "status": "active",
    "role_name": "analyst",
    "created_at": "2024-01-01 00:00:00",
    "updated_at": "2024-01-01 00:00:00"
  }
}
```

#### GET /auth/me

Get the current logged-in user's profile.

**Request:**
```bash
curl http://localhost:5000/auth/me \
  -H "Authorization: Bearer analyst_user:analyst123"
```

**Response (200):**
```json
{
  "user": {
    "id": 2,
    "username": "analyst_user",
    "email": "analyst@example.com",
    "role_id": 2,
    "status": "active",
    "role_name": "analyst"
  }
}
```

---

### User Routes

#### GET /users

List all users. Accessible by admin and analyst roles.

**Request:**
```bash
curl http://localhost:5000/users \
  -H "Authorization: Bearer admin_user:admin123"
```

**Response (200):**
```json
{
  "users": [
    {
      "id": 1,
      "username": "viewer_user",
      "email": "viewer@example.com",
      "role_id": 1,
      "status": "active",
      "role_name": "viewer"
    },
    ...
  ],
  "total": 3
}
```

#### GET /users/:id

Get details of a specific user.

**Request:**
```bash
curl http://localhost:5000/users/2 \
  -H "Authorization: Bearer admin_user:admin123"
```

#### POST /users

Create a new user. Admin only.

**Request:**
```bash
curl -X POST http://localhost:5000/users \
  -H "Authorization: Bearer admin_user:admin123" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "new_analyst",
    "email": "new_analyst@company.com",
    "password": "secure123",
    "role": "analyst"
  }'
```

**Response (201):**
```json
{
  "message": "User 'new_analyst' created successfully",
  "user": {
    "id": 4,
    "username": "new_analyst",
    "email": "new_analyst@company.com",
    "role_id": 2,
    "status": "active",
    "role_name": "analyst"
  }
}
```

#### PUT /users/:id

Update a user. Admin only. Can update any combination of: username, email, password, role, status.

**Request:**
```bash
curl -X PUT http://localhost:5000/users/2 \
  -H "Authorization: Bearer admin_user:admin123" \
  -H "Content-Type: application/json" \
  -d '{"status": "inactive"}'
```

#### DELETE /users/:id

Delete a user permanently. Admin only. Cannot delete yourself.

**Request:**
```bash
curl -X DELETE http://localhost:5000/users/4 \
  -H "Authorization: Bearer admin_user:admin123"
```

---

### Financial Records Routes

#### GET /records

List financial records with optional filters. Non-admins only see their own records.

**Query Parameters:**
| Parameter   | Type   | Description                              |
|------------ |--------|------------------------------------------|
| type        | string | Filter by 'income' or 'expense'          |
| category    | string | Filter by category name                  |
| start_date  | string | Records from this date (YYYY-MM-DD)      |
| end_date    | string | Records until this date (YYYY-MM-DD)     |
| user_id     | int    | Admin only: filter by user               |
| page        | int    | Page number (default: 1)                 |
| per_page    | int    | Records per page (default: 20, max: 100) |

**Request:**
```bash
# Get all records (admin sees all, others see own)
curl http://localhost:5000/records \
  -H "Authorization: Bearer analyst_user:analyst123"

# Filter by type
curl "http://localhost:5000/records?type=income" \
  -H "Authorization: Bearer analyst_user:analyst123"

# Filter by date range
curl "http://localhost:5000/records?start_date=2024-01-01&end_date=2024-06-30" \
  -H "Authorization: Bearer analyst_user:analyst123"

# Admin: view another user's records
curl "http://localhost:5000/records?user_id=1" \
  -H "Authorization: Bearer admin_user:admin123"
```

**Response (200):**
```json
{
  "records": [
    {
      "id": 1,
      "user_id": 2,
      "amount": 50000.0,
      "type": "income",
      "category": "Salary",
      "description": "Monthly salary - January",
      "record_date": "2024-01-31",
      "is_deleted": 0,
      "user_name": "analyst_user"
    }
  ],
  "total": 12,
  "page": 1,
  "per_page": 20,
  "total_pages": 1
}
```

#### GET /records/:id

Get a single record. Ownership check applies.

```bash
curl http://localhost:5000/records/1 \
  -H "Authorization: Bearer analyst_user:analyst123"
```

#### POST /records

Create a new financial record. Analyst and admin only.

**Request:**
```bash
curl -X POST http://localhost:5000/records \
  -H "Authorization: Bearer analyst_user:analyst123" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "type": "income",
    "category": "Freelance",
    "description": "Website design project",
    "record_date": "2024-04-15"
  }'
```

**Response (201):**
```json
{
  "message": "Record created successfully",
  "record": {
    "id": 27,
    "user_id": 2,
    "amount": 5000.0,
    "type": "income",
    "category": "Freelance",
    "description": "Website design project",
    "record_date": "2024-04-15"
  }
}
```

**Admin creating record for another user:**
```bash
curl -X POST http://localhost:5000/records \
  -H "Authorization: Bearer admin_user:admin123" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 3000,
    "type": "expense",
    "category": "Equipment",
    "description": "Office supplies",
    "record_date": "2024-04-10",
    "user_id": 1
  }'
```

#### PUT /records/:id

Update a record. Only the record owner or admin can update.

```bash
curl -X PUT http://localhost:5000/records/1 \
  -H "Authorization: Bearer analyst_user:analyst123" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 55000,
    "description": "Updated salary amount"
  }'
```

#### DELETE /records/:id

Soft delete a record. The record is not actually removed from the database — it's marked as deleted so we keep the audit trail.

```bash
curl -X DELETE http://localhost:5000/records/5 \
  -H "Authorization: Bearer analyst_user:analyst123"
```

#### GET /records/categories

Get list of unique categories used in records.

```bash
curl http://localhost:5000/records/categories \
  -H "Authorization: Bearer analyst_user:analyst123"
```

**Response:**
```json
{
  "categories": ["Entertainment", "Freelance", "Groceries", "Rent", "Salary", "Transport"],
  "total": 6
}
```

---

### Dashboard Routes

All dashboard routes support a `user_id` query parameter for admins to view other users' data.

#### GET /dashboard/summary

Get overall financial summary.

```bash
curl http://localhost:5000/dashboard/summary \
  -H "Authorization: Bearer analyst_user:analyst123"
```

**Response (200):**
```json
{
  "summary": {
    "total_income": 163000.0,
    "total_expense": 35200.0,
    "net_balance": 127800.0,
    "total_records": 12,
    "earliest_record_date": "2024-01-05",
    "latest_record_date": "2024-03-20"
  }
}
```

#### GET /dashboard/category-breakdown

Get income/expense totals broken down by category.

```bash
# All categories
curl http://localhost:5000/dashboard/category-breakdown \
  -H "Authorization: Bearer analyst_user:analyst123"

# Only expenses
curl "http://localhost:5000/dashboard/category-breakdown?type=expense" \
  -H "Authorization: Bearer analyst_user:analyst123"
```

**Response:**
```json
{
  "category_breakdown": [
    {
      "category": "Entertainment",
      "income_total": 0,
      "expense_total": 1500.0,
      "net": -1500.0
    },
    {
      "category": "Salary",
      "income_total": 150000.0,
      "expense_total": 0,
      "net": 150000.0
    }
  ],
  "total_categories": 6
}
```

#### GET /dashboard/monthly-trend

Get month-by-month financial trend.

```bash
# Last 12 months (default)
curl http://localhost:5000/dashboard/monthly-trend \
  -H "Authorization: Bearer analyst_user:analyst123"

# Last 6 months only
curl "http://localhost:5000/dashboard/monthly-trend?months=6" \
  -H "Authorization: Bearer analyst_user:analyst123"
```

**Response:**
```json
{
  "monthly_trend": [
    {
      "month": "2024-01",
      "income": 50000.0,
      "expense": 17500.0,
      "net": 32500.0,
      "transaction_count": 4
    },
    {
      "month": "2024-02",
      "income": 55000.0,
      "expense": 16200.0,
      "net": 38800.0,
      "transaction_count": 4
    }
  ],
  "months_requested": 12,
  "months_returned": 3
}
```

#### GET /dashboard/recent-activity

Get most recent transactions.

```bash
# Last 10 records (default)
curl http://localhost:5000/dashboard/recent-activity \
  -H "Authorization: Bearer analyst_user:analyst123"

# Last 5 records
curl "http://localhost:5000/dashboard/recent-activity?limit=5" \
  -H "Authorization: Bearer analyst_user:analyst123"
```

#### GET /dashboard/insights

Get analytical insights from your financial data.

```bash
curl http://localhost:5000/dashboard/insights \
  -H "Authorization: Bearer analyst_user:analyst123"
```

**Response:**
```json
{
  "insights": {
    "highest_expense_category": {
      "category": "Rent",
      "total": 36000.0
    },
    "highest_income_source": {
      "category": "Salary",
      "total": 150000.0
    },
    "average_transaction_amount": 16350.0,
    "most_active_month": {
      "month": "2024-01",
      "transaction_count": 4
    }
  }
}
```

---

## Role Permissions

### Permission Matrix

| Action                     | Viewer | Analyst | Admin |
|---------------------------|--------|---------|-------|
| Login                      | ✅     | ✅      | ✅    |
| View own profile           | ✅     | ✅      | ✅    |
| View own records           | ✅     | ✅      | ✅    |
| View own dashboard         | ✅     | ✅      | ✅    |
| List users                 | ❌     | ✅      | ✅    |
| Create records             | ❌     | ✅      | ✅    |
| Update own records         | ❌     | ✅      | ✅    |
| Delete own records         | ❌     | ✅      | ✅    |
| View all records           | ❌     | ❌      | ✅    |
| Create records for others  | ❌     | ❌      | ✅    |
| Update any record          | ❌     | ❌      | ✅    |
| Delete any record          | ❌     | ❌      | ✅    |
| View any user's dashboard  | ❌     | ❌      | ✅    |
| Create users               | ❌     | ❌      | ✅    |
| Update users               | ❌     | ❌      | ✅    |
| Delete users               | ❌     | ❌      | ✅    |

### Role Descriptions

**Viewer**: Read-only access. Can see their own records and dashboard data. Useful for stakeholders who need to see reports but shouldn't modify any data.

**Analyst**: Can manage their own financial records (create, update, delete). Has access to analytics. Cannot manage other users' data or user accounts.

**Admin**: Full access. Can manage all records, all users, and view anyone's dashboard. The "superuser" of the system.

---

## Database Schema

### Entity Relationship

```
roles (1) ──────────< users (1) ──────────< financial_records
  id                    id                      id
  name                  username                user_id (FK)
  description           email                   amount
                        password_hash           type
                        role_id (FK)            category
                        status                  description
                        created_at              record_date
                        updated_at              is_deleted
                                                created_at
                                                updated_at

users (1) ──────────< audit_log
                        id
                        user_id (FK)
                        action
                        resource_type
                        resource_id
                        details
                        timestamp
```

### Tables

#### roles
| Column      | Type    | Constraints          |
|------------|---------|----------------------|
| id         | INTEGER | PRIMARY KEY          |
| name       | TEXT    | UNIQUE, NOT NULL     |
| description| TEXT    |                      |

#### users
| Column        | Type      | Constraints                    |
|--------------|-----------|-------------------------------|
| id           | INTEGER   | PRIMARY KEY                   |
| username     | TEXT      | UNIQUE, NOT NULL              |
| email        | TEXT      | UNIQUE, NOT NULL              |
| password_hash| TEXT      | NOT NULL                      |
| role_id      | INTEGER   | FK → roles(id), NOT NULL      |
| status       | TEXT      | DEFAULT 'active', CHECK       |
| created_at   | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP     |
| updated_at   | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP     |

#### financial_records
| Column      | Type      | Constraints                    |
|------------|-----------|-------------------------------|
| id         | INTEGER   | PRIMARY KEY                   |
| user_id    | INTEGER   | FK → users(id), NOT NULL      |
| amount     | REAL      | NOT NULL                      |
| type       | TEXT      | CHECK ('income'/'expense')    |
| category   | TEXT      | NOT NULL                      |
| description| TEXT      | nullable                      |
| record_date| DATE      | NOT NULL                      |
| is_deleted | INTEGER   | DEFAULT 0                     |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP     |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP     |

#### audit_log
| Column        | Type      | Constraints                |
|--------------|-----------|---------------------------|
| id           | INTEGER   | PRIMARY KEY               |
| user_id      | INTEGER   | FK → users(id)            |
| action       | TEXT      | NOT NULL                  |
| resource_type| TEXT      | NOT NULL                  |
| resource_id  | INTEGER   |                           |
| details      | TEXT      |                           |
| timestamp    | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP |

---

## Error Handling

### Error Response Format

All errors follow a consistent JSON format:

```json
{
  "error": "ErrorType",
  "message": "Human-readable description of what went wrong",
  "details": {}
}
```

The `details` field is optional and only included when there's additional context (like validation error specifics).

### HTTP Status Codes

| Code | Meaning                | When it's used                          |
|------|------------------------|-----------------------------------------|
| 200  | OK                     | Successful GET or PUT requests          |
| 201  | Created                | Successful POST (resource created)      |
| 400  | Bad Request            | Invalid input / validation errors       |
| 401  | Unauthorized           | Missing or invalid authentication       |
| 403  | Forbidden              | User doesn't have required permissions  |
| 404  | Not Found              | Resource doesn't exist                  |
| 405  | Method Not Allowed     | Wrong HTTP method for this endpoint     |
| 409  | Conflict               | Duplicate username/email                |
| 500  | Internal Server Error  | Unexpected server-side error            |

### Custom Error Classes

The project defines custom exception classes in `utils/errors.py`:

- `APIError` — Base class for all API errors
- `ValidationError` — Input validation failures (400)
- `NotFoundError` — Resource not found (404)
- `ForbiddenError` — Insufficient permissions (403)
- `UnauthorizedError` — Authentication failures (401)
- `ConflictError` — Duplicate resource conflicts (409)

These are caught by Flask's error handler in `app.py` and converted to proper JSON responses automatically.

---

## Testing with cURL

Here are some test scenarios you can run to verify the API is working correctly.

### Test 1: Login as different roles

```bash
# Viewer login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"viewer_user","password":"viewer123"}'

# Analyst login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst_user","password":"analyst123"}'

# Admin login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_user","password":"admin123"}'
```

### Test 2: Access control — viewer cannot create records

```bash
# This should FAIL with 403
curl -X POST http://localhost:5000/records \
  -H "Authorization: Bearer viewer_user:viewer123" \
  -H "Content-Type: application/json" \
  -d '{"amount":1000,"type":"income","category":"Test","record_date":"2024-01-01"}'
```

Expected response:
```json
{
  "error": "ForbiddenError",
  "message": "Access denied. Required role: admin, analyst. Your role: viewer"
}
```

### Test 3: Analyst creates a record

```bash
# This should SUCCEED with 201
curl -X POST http://localhost:5000/records \
  -H "Authorization: Bearer analyst_user:analyst123" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "type": "income",
    "category": "Salary",
    "description": "Monthly salary",
    "record_date": "2024-01-31"
  }'
```

### Test 4: Dashboard summary

```bash
curl http://localhost:5000/dashboard/summary \
  -H "Authorization: Bearer analyst_user:analyst123"
```

### Test 5: Admin views another user's records

```bash
# Admin CAN see user 1's records — should succeed
curl "http://localhost:5000/records?user_id=1" \
  -H "Authorization: Bearer admin_user:admin123"

# Analyst CANNOT see other's records — should fail with 403
curl "http://localhost:5000/records?user_id=1" \
  -H "Authorization: Bearer analyst_user:analyst123"
```

### Test 6: Invalid authentication

```bash
# No auth header - should get 401
curl http://localhost:5000/records

# Wrong password - should get 401
curl http://localhost:5000/records \
  -H "Authorization: Bearer analyst_user:wrongpassword"
```

### Test 7: Create and delete a user (admin)

```bash
# Create a new user
curl -X POST http://localhost:5000/users \
  -H "Authorization: Bearer admin_user:admin123" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com",
    "password": "test1234",
    "role": "viewer"
  }'

# Delete the user (use the id from the create response)
curl -X DELETE http://localhost:5000/users/4 \
  -H "Authorization: Bearer admin_user:admin123"
```

### Test 8: Update a record

```bash
curl -X PUT http://localhost:5000/records/1 \
  -H "Authorization: Bearer analyst_user:analyst123" \
  -H "Content-Type: application/json" \
  -d '{"amount": 55000, "description": "Revised salary amount"}'
```

### Test 9: Category breakdown with filter

```bash
curl "http://localhost:5000/dashboard/category-breakdown?type=expense" \
  -H "Authorization: Bearer analyst_user:analyst123"
```

### Test 10: Health check (no auth needed)

```bash
curl http://localhost:5000/health
```

---

## Design Decisions

### 1. Soft Deletes for Financial Records

Financial records use soft deletes (setting `is_deleted = 1`) instead of actually removing rows from the database. This is important because:
- Financial data should generally never be permanently deleted for audit purposes
- It allows "undo" functionality if needed in the future
- The audit trail remains intact

Users are hard-deleted since they're account data, not financial records.

### 2. Plaintext Passwords

Yes, I know this is not secure. The passwords are stored as plaintext in the database. In a real production system, you'd use `bcrypt` or `argon2` for password hashing. But since the assignment spec called for no additional packages beyond Flask and Werkzeug, and this is a demo system, I went with plaintext to keep things simple.

If I were to improve this, I'd use `werkzeug.security.generate_password_hash()` and `check_password_hash()` which are already available in Werkzeug.

### 3. Bearer Token Format

The `username:password` format for Bearer tokens is simplified for demo purposes. A production system would use JWT tokens with expiration, refresh tokens, and proper session management.

### 4. SQLite Row Factory

I set `conn.row_factory = sqlite3.Row` in the database connection so we can access columns by name (`row['username']`) instead of by index (`row[0]`). This makes the code much more readable.

### 5. Blueprint Organization

Each group of related endpoints is in its own Blueprint file. This keeps things organized and makes it easy to add new endpoint groups in the future. For example, if we needed to add a "budgets" feature, we'd just create `routes/budget_routes.py` and register the blueprint.

### 6. Decorator-Based Auth

Authentication and authorization are implemented as Python decorators (`@authenticate_user`, `@require_role`). This is cleaner than putting auth checks at the beginning of every route function, and it follows the DRY (Don't Repeat Yourself) principle.

### 7. Dynamic Query Building

The model layer builds SQL queries dynamically based on which filters are provided. While this means we're constructing SQL strings at runtime, we always use parameterized queries (`?` placeholders) to prevent SQL injection.

### 8. Audit Logging

Every write operation (create, update, delete) is logged to the `audit_log` table. The logging is wrapped in a try-except so that if logging fails for some reason, it doesn't break the actual operation.

---

## Assumptions

1. **Single-user deployment**: This is designed to run on a single machine. No special handling for concurrent requests or race conditions.

2. **Demo authentication**: Passwords are plaintext and tokens are `username:password`. Not suitable for production.

3. **UTC timestamps**: All timestamps use SQLite's `CURRENT_TIMESTAMP` which is in UTC.

4. **Date format**: All dates are expected in `YYYY-MM-DD` format.

5. **Currency agnostic**: The system doesn't handle currency types. All amounts are just numbers.

6. **No file uploads**: No support for attaching receipts or documents to records.

7. **No email notifications**: No email verification or password reset functionality.

8. **Sample data**: The database comes pre-loaded with sample records for testing. Delete `finance.db` and restart to get a fresh database.

---

## Future Improvements

If I had more time, here's what I'd add:

- **JWT Authentication**: Proper token-based auth with expiration and refresh
- **Password Hashing**: Using bcrypt or Werkzeug's security utilities
- **Rate Limiting**: Prevent API abuse
- **Export Functionality**: CSV/PDF export for financial reports
- **Budget Tracking**: Set budgets per category and track spending
- **Search**: Full-text search across records
- **Unit Tests**: Comprehensive test suite with pytest
- **API Versioning**: URL prefix like `/api/v1/`
- **Swagger Documentation**: Interactive API docs

---

## License

This project was built as part of a backend development assignment. Feel free to use it as a reference or starting point for your own projects.

---

*Built with Flask and SQLite. No unnecessary complexity.*
