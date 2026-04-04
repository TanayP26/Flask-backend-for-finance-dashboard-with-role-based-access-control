# Finance Dashboard Backend

A role-based financial data management API built with Flask and SQLite. The system supports three user tiers — Admin, Analyst, and Viewer — each with strictly enforced permissions across user management, financial record CRUD, and dashboard analytics.

Designed as a backend engineering assessment to demonstrate clean architecture, layered access control, input validation pipelines, and SQL-driven aggregation — all with zero external ORM dependencies.

---

## Why This Project

Financial dashboards are at the core of every modern enterprise — from fintech platforms and SaaS billing systems to internal accounting tools. Behind every dashboard sits a backend that must solve three non-trivial problems simultaneously:

- **Multi-user data isolation** — Different users must only see what they're authorized to see. A misconfigured query or a missing ownership check can expose sensitive financial data across tenant boundaries.
- **Role-based access control** — Real-world systems rarely have a single user type. Permissions must be enforced consistently across every endpoint, not bolted on as an afterthought.
- **Aggregation at the data layer** — Summary statistics, trend analysis, and category breakdowns must be computed efficiently. Pulling raw rows into application memory and aggregating in Python doesn't scale — the database should do the heavy lifting.

This project addresses all three. It implements a production-style backend architecture with strict RBAC, SQL-driven analytics, and a clean separation between routing, authorization, business logic, and data access — the same patterns used in real financial systems, scaled to a focused scope.

---

## Features

### Authentication & User Management
- Login with username/password, receive a Bearer token for subsequent requests
- Profile endpoint to retrieve current authenticated user details
- Full user CRUD (create, read, update, delete) restricted to Admin role
- Account status management (active/inactive) to deactivate users without deletion
- Duplicate username and email detection with conflict responses

### Financial Records
- Create, read, update, and soft-delete income/expense transactions
- Multi-parameter filtering: type, category, date range, user scope
- Offset-based pagination with configurable page size (max 100 per page)
- Soft deletes preserve audit integrity — records are flagged, never destroyed
- Admin can create records on behalf of other users

### Dashboard & Analytics
- **Summary** — Total income, total expenses, net balance, record count, date range
- **Category Breakdown** — Per-category income/expense split with net calculation
- **Monthly Trend** — Month-over-month income, expense, net, and transaction count
- **Recent Activity** — Configurable list of most recent transactions (max 100)
- **Insights** — Highest expense category, top income source, average transaction amount, most active month

### Access Control
- Three-tier RBAC: Viewer, Analyst, Admin
- Composable decorator-based authorization (`@authenticate_user`, `@require_role`)
- Query-level ownership filtering prevents horizontal privilege escalation
- All mutations logged to an audit trail with actor, action, resource, and timestamp

### Error Handling
- Custom exception hierarchy: `ValidationError`, `NotFoundError`, `ForbiddenError`, `UnauthorizedError`, `ConflictError`
- Each exception maps to a specific HTTP status code (400, 401, 403, 404, 409)
- Global error handlers for 400, 404, 405, and 500 with consistent JSON response structure

---

## Tech Stack

| Layer       | Technology   | Rationale                                                                 |
|-------------|--------------|---------------------------------------------------------------------------|
| **Framework**   | Flask 2.3.3  | Lightweight, no opinionated structure — full control over architecture    |
| **Database**    | SQLite3      | Zero-config, single-file persistence, sufficient for assessment scope    |
| **Language**    | Python 3.7+  | Clean syntax, strong standard library for date/regex validation           |
| **Auth**        | Bearer Token | Stateless `username:password` token — simple to test, avoids JWT complexity for demo scope |

**Dependencies:** `Flask`, `Werkzeug`. No ORM, no external services.

---

## Architecture & Design

### Project Structure

```
finance-backend/
├── app.py               # Application factory, error handlers, blueprint registration
├── database.py          # SQLite connection management, schema init, data seeding
├── middleware.py         # @authenticate_user, @require_role — composable auth decorators
├── models.py            # Data access layer — parameterized SQL queries, no ORM
├── requirements.txt     # Python dependencies
│
├── routes/              # Domain-grouped endpoint handlers
│   ├── __init__.py      # Blueprint exports
│   ├── auth_routes.py   # Login, profile (/auth)
│   ├── user_routes.py   # User CRUD (/users)
│   ├── record_routes.py # Financial records CRUD (/records)
│   └── dashboard_routes.py  # Analytics & summaries (/dashboard)
│
└── utils/               # Input validation + custom exceptions
    ├── __init__.py      # Validation functions (username, email, amount, date, etc.)
    └── errors.py        # Custom exception hierarchy (APIError → ValidationError, etc.)
```

### Separation of Concerns

| Layer          | Responsibility                                                  |
|----------------|-----------------------------------------------------------------|
| **Routes**     | HTTP handling, request parsing, response formatting              |
| **Middleware** | Authentication verification, role-based authorization            |
| **Models**     | Data access — all SQL queries live here, parameterized against injection |
| **Utils**      | Input validation (regex, type checks, range enforcement) and error definitions |
| **Database**   | Connection management, schema DDL, seed data management          |

### Request Lifecycle

```
Client Request
  │
  ├─ Flask Router ─── Blueprint matching by URL prefix (/auth, /users, /records, /dashboard)
  │
  ├─ @authenticate_user ─── Extract Bearer token → validate credentials → inject user into g.current_user
  │
  ├─ @require_role ─── Check g.current_user.role_name against allowed roles → 403 if denied
  │
  ├─ Input Validation ─── Sanitize and validate all fields via utils/ → raise ValidationError (400) on failure
  │
  ├─ Model Layer ─── Execute parameterized SQL → apply ownership filtering for non-admin users
  │
  ├─ Audit Logging ─── Log mutation operations (CREATE, UPDATE, DELETE) to audit_log table
  │
  └─ JSON Response ─── Consistent structure: { data, message } with appropriate HTTP status code
```

---

## API Endpoints

### Authentication (`/auth`)

| Method | Endpoint       | Description                        | Access        |
|--------|----------------|------------------------------------|---------------|
| `POST` | `/auth/login`  | Validate credentials, return token | Public        |
| `GET`  | `/auth/me`     | Get current user profile           | Authenticated |

### User Management (`/users`)

| Method   | Endpoint        | Description       | Access         |
|----------|-----------------|-------------------|----------------|
| `GET`    | `/users`        | List all users    | Admin, Analyst |
| `GET`    | `/users/<id>`   | Get user details  | Authenticated  |
| `POST`   | `/users`        | Create new user   | Admin          |
| `PUT`    | `/users/<id>`   | Update user       | Admin          |
| `DELETE` | `/users/<id>`   | Delete user       | Admin          |

### Financial Records (`/records`)

| Method   | Endpoint              | Description                        | Access                |
|----------|-----------------------|------------------------------------|-----------------------|
| `GET`    | `/records`            | List records (filterable, paginated) | Authenticated (scoped) |
| `GET`    | `/records/<id>`       | Get single record                  | Owner or Admin        |
| `POST`   | `/records`            | Create new record                  | Analyst, Admin        |
| `PUT`    | `/records/<id>`       | Update record                      | Owner or Admin        |
| `DELETE` | `/records/<id>`       | Soft delete record                 | Owner or Admin        |
| `GET`    | `/records/categories` | List distinct categories           | Authenticated (scoped) |

**Available Filters:** `type`, `category`, `start_date`, `end_date`, `user_id` (admin only), `page`, `per_page`

### Dashboard Analytics (`/dashboard`)

| Method | Endpoint                        | Description                                                   |
|--------|---------------------------------|---------------------------------------------------------------|
| `GET`  | `/dashboard/summary`            | Total income, expenses, net balance, record count, date range |
| `GET`  | `/dashboard/category-breakdown` | Per-category income/expense split with net calculation         |
| `GET`  | `/dashboard/monthly-trend`      | Month-over-month income, expense, net, transaction count       |
| `GET`  | `/dashboard/recent-activity`    | Most recent records (configurable limit, max 100)              |
| `GET`  | `/dashboard/insights`           | Top expense/income categories, averages, most active period    |

> All dashboard endpoints are user-scoped. Admins can append `?user_id=<id>` for cross-user views.

### Example API Response

`GET /dashboard/summary` — authenticated as `analyst_user`:

```json
{
  "summary": {
    "total_income": 113000.00,
    "total_expense": 35200.00,
    "net_balance": 77800.00,
    "total_records": 12,
    "earliest_record_date": "2024-01-05",
    "latest_record_date": "2024-03-20"
  }
}
```

`GET /dashboard/insights` — analytical breakdown:

```json
{
  "insights": {
    "highest_expense_category": {
      "category": "Rent",
      "total": 36000.00
    },
    "highest_income_source": {
      "category": "Salary",
      "total": 150000.00
    },
    "average_transaction_amount": 16573.08,
    "most_active_month": {
      "month": "2024-01",
      "transaction_count": 10
    }
  }
}
```

---

## Role-Based Access Control

### Permission Matrix

| Capability                    | Viewer | Analyst | Admin |
|-------------------------------|:------:|:-------:|:-----:|
| View own records              |   ✅   |   ✅    |  ✅   |
| View all records              |   ❌   |   ❌    |  ✅   |
| Create records                |   ❌   |   ✅    |  ✅   |
| Update own records            |   ❌   |   ✅    |  ✅   |
| Delete own records            |   ❌   |   ✅    |  ✅   |
| Access dashboard analytics    |   ✅   |   ✅    |  ✅   |
| List users                    |   ❌   |   ✅    |  ✅   |
| Create / update / delete users|   ❌   |   ❌    |  ✅   |
| View cross-user dashboards    |   ❌   |   ❌    |  ✅   |

### How It Works

Access control is enforced at **three distinct layers**:

1. **Route-level** — `@require_role('admin', 'analyst')` blocks unauthorized roles before the handler executes
2. **Ownership-level** — Non-admin users are filtered to their own records at the SQL query layer, preventing horizontal privilege escalation
3. **Operation-level** — Specific actions (cross-user record creation, user management) are gated by explicit role checks within handler logic

```python
# Example: stacked decorators enforce both authentication and role
@record_bp.route('', methods=['POST'])
@authenticate_user
@require_role('admin', 'analyst')
def create_record():
    ...
```

---

## Dashboard & Aggregation Logic

All analytics are computed directly in SQLite using parameterized SQL queries — no application-level aggregation.

| Endpoint             | SQL Technique                                                           |
|----------------------|-------------------------------------------------------------------------|
| **Summary**          | `SUM()`, `COUNT()`, `MIN()`, `MAX()` across filtered records             |
| **Category Breakdown** | `GROUP BY category` with `CASE WHEN type = 'income'` / `'expense'` split |
| **Monthly Trend**    | `strftime('%Y-%m', record_date)` for grouping, `LIMIT` for recency       |
| **Insights**         | `GROUP BY` + `ORDER BY total DESC LIMIT 1` to find top categories        |

All aggregation endpoints respect user scoping — non-admin users see only their own data. Results are rounded to 2 decimal places.

---

## Data Modeling

### Schema

```
┌──────────────────────────────┐
│  roles                       │
├──────────────────────────────┤
│  id          INTEGER PK      │
│  name        TEXT UNIQUE      │
│  description TEXT             │
└──────────┬───────────────────┘
           │
           │ role_id (FK)
           ▼
┌──────────────────────────────┐     ┌──────────────────────────────┐
│  users                       │     │  audit_log                   │
├──────────────────────────────┤     ├──────────────────────────────┤
│  id          INTEGER PK      │◄────│  user_id    INTEGER FK       │
│  username    TEXT UNIQUE      │     │  id         INTEGER PK       │
│  email       TEXT UNIQUE      │     │  action     TEXT              │
│  password_hash TEXT           │     │  resource_type TEXT           │
│  role_id     INTEGER FK       │     │  resource_id INTEGER         │
│  status      TEXT (active/    │     │  details    TEXT              │
│              inactive)        │     │  timestamp  TIMESTAMP         │
│  created_at  TIMESTAMP        │     └──────────────────────────────┘
│  updated_at  TIMESTAMP        │
└──────────┬───────────────────┘
           │
           │ user_id (FK)
           ▼
┌──────────────────────────────┐
│  financial_records           │
├──────────────────────────────┤
│  id          INTEGER PK      │
│  user_id     INTEGER FK       │
│  amount      REAL             │
│  type        TEXT (income/    │
│              expense)         │
│  category    TEXT              │
│  description TEXT              │
│  record_date DATE              │
│  is_deleted  INTEGER (0/1)    │
│  created_at  TIMESTAMP        │
│  updated_at  TIMESTAMP        │
└──────────────────────────────┘
```

- **Foreign keys** enforced via `PRAGMA foreign_keys = ON`
- **Soft deletes** on financial records (`is_deleted` flag) — records are never physically removed
- **CHECK constraints** on `status` (active/inactive) and `type` (income/expense)

---

## Validation & Error Handling

### Input Validation

Every user-supplied field is validated before reaching the database:

| Field        | Rules                                                    |
|--------------|----------------------------------------------------------|
| `username`   | 3–50 chars, alphanumeric + underscores/hyphens only      |
| `email`      | Regex pattern validation, max 120 chars, normalized to lowercase |
| `password`   | 6–128 chars                                               |
| `amount`     | Positive float, max 999,999,999.99, rounded to 2 decimals |
| `type`       | Must be `income` or `expense`                             |
| `category`   | 2–50 chars                                                |
| `record_date`| Must match `YYYY-MM-DD` format                            |
| `role`       | Must be `viewer`, `analyst`, or `admin`                   |
| `pagination` | Page ≥ 1, per_page between 1–100                          |

### HTTP Status Codes

| Code | Error Class        | Trigger                              |
|------|--------------------|--------------------------------------|
| 400  | `ValidationError`  | Invalid input, malformed request     |
| 401  | `UnauthorizedError`| Missing or invalid credentials       |
| 403  | `ForbiddenError`   | Insufficient role/permissions        |
| 404  | `NotFoundError`    | Resource does not exist              |
| 405  | —                  | Wrong HTTP method for endpoint       |
| 409  | `ConflictError`    | Duplicate username or email          |
| 500  | —                  | Unexpected server error              |

All error responses follow a consistent JSON structure:

```json
{
  "error": "ValidationError",
  "message": "Amount must be greater than zero",
  "details": null
}
```

---

## Security Considerations

This project implements multiple defense layers appropriate for a backend assessment. Key measures:

| Measure                         | Implementation                                                                                    |
|---------------------------------|---------------------------------------------------------------------------------------------------|
| **SQL Injection Prevention**    | All database queries use parameterized placeholders (`?`). No string interpolation of user input into SQL. |
| **Multi-Layer Authorization**   | Access is enforced at three levels: route decorators, query-level ownership filtering, and in-handler operation checks. A single bypass does not compromise the system. |
| **Ownership Isolation**         | Non-admin users are scoped to their own data at the SQL `WHERE` clause level — not at the application layer. This prevents horizontal privilege escalation even if a route-level check is misconfigured. |
| **Soft Deletes**                | Financial records are never physically removed. The `is_deleted` flag preserves data integrity and supports audit requirements. |
| **Audit Trail**                 | Every CREATE, UPDATE, and DELETE operation is logged with actor ID, action type, resource reference, and timestamp. Logging failures are isolated — they never cascade into failed business operations. |
| **Input Sanitization**          | All user-supplied fields pass through dedicated validation functions with type checks, length constraints, regex patterns, and range enforcement before reaching any query. |
| **Account Deactivation**        | Users can be set to `inactive` status without deletion, immediately revoking their ability to authenticate. |

**On plaintext passwords:** Password storage in this project uses plaintext comparison — this is a deliberate scoping decision for demo purposes. The architecture stores passwords in a dedicated `password_hash` column and authenticates through a single comparison point in middleware. Replacing this with `werkzeug.security.generate_password_hash` / `check_password_hash` requires changing exactly two lines of code — zero structural refactoring. This is documented as a known limitation, not an oversight.

---

## Scalability Considerations

While this project uses SQLite and runs as a single-process Flask server — appropriate for an assessment — the architecture is designed to scale with minimal refactoring:

| Dimension               | Current State                     | Migration Path                                                                 |
|--------------------------|-----------------------------------|--------------------------------------------------------------------------------|
| **Database**             | SQLite (single-file)              | Replace `get_db()` connection factory with a PostgreSQL/MySQL connection pool (e.g., `psycopg2` + connection pooling). All queries use standard SQL — no SQLite-specific syntax beyond `strftime`. |
| **Application Structure** | Modular blueprints + models      | Each blueprint is a self-contained domain module. Can be extracted into independent microservices with their own database and deployed behind an API gateway. |
| **Dashboard Performance** | Direct SQL aggregation on every request | Add a caching layer (e.g., Redis) in front of analytics endpoints. Summary and trend data change infrequently relative to read frequency — ideal candidates for time-based cache invalidation. |
| **Pagination**           | Offset-based (`LIMIT` / `OFFSET`)  | Migrate to cursor-based pagination for consistent performance on large datasets. The current `page`/`per_page` interface can remain backward-compatible by accepting cursor tokens as an alternative parameter. |
| **Authentication**       | Stateless Bearer token (demo)     | Swap to JWT with token expiration, refresh tokens, and revocation lists. The `@authenticate_user` decorator is the single integration point — all routes inherit the upgrade automatically. |

---

## How This Project Meets Assignment Requirements

| Requirement                | Implementation                                                        |
|----------------------------|-----------------------------------------------------------------------|
| **User & Role Management** | Full CRUD on users with three predefined roles (Viewer, Analyst, Admin). Role assignment at creation. Status toggling for account deactivation. |
| **Financial Records**      | Income/expense CRUD with amount, type, category, description, date. Soft deletes. Multi-parameter filtering and pagination. |
| **Dashboard APIs**         | Five analytics endpoints: summary stats, category breakdown, monthly trends, recent activity, behavioral insights — all SQL-driven. |
| **Access Control**         | Three-layer RBAC: decorator-based route gating, ownership filtering at query level, and operation-level checks in handler logic. |
| **Validation**             | Dedicated validation module with per-field rules. Custom exception hierarchy mapped to HTTP status codes. |
| **Data Persistence**       | SQLite with schema auto-initialization, foreign key enforcement, and seed data for immediate demo readiness. |

---

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/TanayP26/Flask-backend-for-finance-dashboard-with-role-based-access-control.git
cd Flask-backend-for-finance-dashboard-with-role-based-access-control

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the server
python app.py
```

The server starts at `http://localhost:5000`. On first run, the database initializes automatically with:
- Schema creation (roles, users, financial_records, audit_log)
- Three predefined roles
- Three demo user accounts
- 26 sample financial records

**To reset the database:** delete `finance.db` and restart the server.

### Demo Credentials

| Role    | Username       | Password     |
|---------|----------------|--------------|
| Viewer  | `viewer_user`  | `viewer123`  |
| Analyst | `analyst_user` | `analyst123` |
| Admin   | `admin_user`   | `admin123`   |

### Quick Test

```bash
# Login as admin
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_user","password":"admin123"}'

# Get dashboard summary
curl http://localhost:5000/dashboard/summary \
  -H "Authorization: Bearer admin_user:admin123"

# Create a new record as analyst
curl -X POST http://localhost:5000/records \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer analyst_user:analyst123" \
  -d '{"amount":15000,"type":"income","category":"Freelance","description":"Contract work","record_date":"2024-04-01"}'
```

---

## Assumptions & Design Decisions

| Decision                      | Rationale                                                                                      | Tradeoff                                                          |
|-------------------------------|------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| **Flask over Django**         | No ORM or admin panel needed. Flask allows full architectural control without framework opinions. | Less built-in tooling, but cleaner for a focused API project.     |
| **Raw SQL over ORM**          | Aggregation queries (`GROUP BY`, `CASE WHEN`, `strftime`) are cleaner in raw SQL. Avoids ORM abstraction leaks. | Manual query construction — mitigated by parameterized queries.   |
| **SQLite over PostgreSQL**    | Zero-config, single-file persistence. No external database setup required for reviewers.        | No concurrent write support — acceptable for single-server demo.  |
| **Decorator-based auth**      | `@authenticate_user` and `@require_role` are composable — any route gets auth by stacking decorators. | Tightly coupled to Flask's `g` context. Acceptable at this scope. |
| **Soft deletes for records**  | Financial data should never be permanently destroyed. `is_deleted` flag preserves audit integrity. | Requires `is_deleted = 0` filtering in every record query.        |
| **Plaintext password storage** | An intentional scoping decision for demonstration purposes. The `password_hash` column and single-point authentication in middleware are designed for drop-in replacement with `werkzeug.security` hashing — zero structural changes required. | Not production-safe. Explicitly documented as a known boundary of the demo scope. |
| **Audit log isolation**       | Logging wrapped in `try/except` — a logging failure must never cascade into a failed business operation. | Silent logging failures. Acceptable for a non-critical audit trail. |

---

## Possible Improvements

- **JWT Authentication** — Token expiration, refresh flow, and stateless session management to replace demo Bearer tokens
- **Password Hashing** — Integrate `werkzeug.security` for bcrypt-based password storage (two-line change)
- **Cursor-Based Pagination** — Replace offset pagination with cursor tokens for consistent performance on growing datasets
- **Granular RBAC** — Permission-based access control (`can:create_record`, `can:manage_users`) instead of role-name matching
- **API Versioning** — URL-prefixed versioning (`/api/v1/`) for backward-compatible evolution
- **Docker** — Containerized deployment with `Dockerfile` and `docker-compose.yml`
- **Automated Tests** — Unit tests for validators and models, integration tests for endpoints, role-based access matrix verification with `pytest`
- **Caching Layer** — Redis-backed caching for dashboard analytics to reduce redundant aggregation queries
- **Time-Series Analytics** — Rolling averages, year-over-year comparisons, and anomaly detection on spending patterns
- **Rate Limiting** — Throttle API requests per user/role to prevent abuse and ensure fair resource usage

---

## Author

**Tanay Prasad**
Built as part of a Backend Developer Intern assessment — April 2026.

---

## License

This project is submitted as part of an internship assignment and is not licensed for production use.
