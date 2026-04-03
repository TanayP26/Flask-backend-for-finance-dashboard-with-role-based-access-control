# Finance Dashboard Backend

A backend system that implements role-based financial data management with layered access control, structured CRUD operations, and SQL-driven analytics. Built with Flask and SQLite, the architecture enforces strict permission boundaries across three user tiers while maintaining clean separation between routing, business logic, and data access.

Designed to demonstrate backend design fundamentals: API structuring, middleware-based authorization, input validation pipelines, and query-level data isolation.

---

## Purpose

Built as a backend engineering assessment submission. The focus is on:

- **Clean API design** — RESTful conventions, consistent response structures, proper HTTP semantics
- **Logical architecture** — Separation of concerns across routes, models, middleware, and utilities
- **Access control correctness** — Role enforcement at multiple layers, not just route-level checks
- **Robustness** — Input validation, custom error hierarchy, audit logging, soft deletes

---

## Features

- **Three-Tier RBAC** — Viewer, Analyst, Admin roles enforced via composable decorators and query-level ownership checks
- **Financial Records CRUD** — Income/expense management with multi-parameter filtering, pagination, and soft deletes
- **Aggregation Analytics** — SQL-driven summary stats, category breakdowns, monthly trends, and behavioral insights
- **Audit Trail** — Every mutation is logged with actor, action, resource type, and timestamp
- **Error Architecture** — Custom exception hierarchy (`ValidationError`, `ForbiddenError`, etc.) mapped to HTTP status codes

---

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Framework | Flask 2.3.3 | Lightweight, no opinionated structure — full control over architecture |
| Database | SQLite3 | Zero-config, single-file persistence, sufficient for assessment scope |
| Language | Python 3.7+ | Clean syntax, strong standard library for date/regex validation |
| Auth | Bearer Token | Stateless, simple to test, avoids JWT complexity for demo scope |

**Total dependencies:** `Flask`, `Werkzeug`. No ORM, no external services.

---

## System Design

### Project Structure

```
app.py              → Application factory, error handlers, blueprint registration
middleware.py        → @authenticate_user, @require_role — composable auth decorators
models.py            → Data access layer (parameterized SQL, no ORM)
database.py          → Connection management, schema initialization, data seeding
routes/              → Domain-grouped endpoint handlers (auth, users, records, dashboard)
utils/               → Input validation functions + custom exception classes
```

### Request Lifecycle

```
Client Request
  │
  ├─ Flask Router ─── Blueprint matching by URL prefix
  │
  ├─ @authenticate_user ─── Extract Bearer token → validate credentials → inject user into g.current_user
  │
  ├─ @require_role ─── Check user.role_name against allowed roles → 403 if denied
  │
  ├─ Input Validation ─── Sanitize and validate all fields via utils/ → 400 on failure
  │
  ├─ Model Layer ─── Execute parameterized SQL → ownership filtering for non-admins
  │
  └─ JSON Response ─── Consistent structure with appropriate HTTP status code
```

### Access Control Enforcement

Authorization operates at **three distinct layers**:

1. **Route level** — `@require_role('admin', 'analyst')` blocks unauthorized roles before the handler executes
2. **Ownership level** — Non-admin users are filtered to their own records at the SQL query layer, preventing horizontal privilege escalation
3. **Operation level** — Specific actions (user management, cross-user record creation) are gated by role checks within the handler logic

```
Viewer   → Read own data only. No write access.
Analyst  → Full CRUD on own records. Analytics access. No user management.
Admin    → Unrestricted. Cross-user operations. User CRUD.
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| POST | `/auth/login` | Validate credentials, return token | Public |
| GET | `/auth/me` | Current user profile | Authenticated |

### Users
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/users` | List all users | Admin, Analyst |
| GET | `/users/<id>` | User details | Authenticated |
| POST | `/users` | Create user | Admin |
| PUT | `/users/<id>` | Update user | Admin |
| DELETE | `/users/<id>` | Delete user | Admin |

### Financial Records
| Method | Endpoint | Description | Access |
|--------|----------|-------------|--------|
| GET | `/records` | List records (filterable, paginated) | Authenticated (scoped) |
| GET | `/records/<id>` | Single record | Owner / Admin |
| POST | `/records` | Create record | Analyst, Admin |
| PUT | `/records/<id>` | Update record | Owner / Admin |
| DELETE | `/records/<id>` | Soft delete | Owner / Admin |
| GET | `/records/categories` | Distinct category list | Authenticated |

**Filters:** `type`, `category`, `start_date`, `end_date`, `user_id` (admin only), `page`, `per_page`

### Dashboard Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary` | Total income, expense, net balance, record count, date range |
| GET | `/dashboard/category-breakdown` | Per-category income/expense split with net calculation |
| GET | `/dashboard/monthly-trend` | Month-over-month income, expense, net, transaction count |
| GET | `/dashboard/recent-activity` | Most recent records (configurable limit, max 100) |
| GET | `/dashboard/insights` | Highest expense/income categories, averages, most active period |

All dashboard endpoints are user-scoped. Admins can append `?user_id=<id>` for cross-user views.

---

## Data Model

**users** — `id`, `username` (unique), `email` (unique), `password_hash`, `role_id` → roles, `status` (active/inactive), `created_at`, `updated_at`

**financial_records** — `id`, `user_id` → users, `amount` (real), `type` (income/expense), `category`, `description`, `record_date`, `is_deleted` (soft delete), `created_at`, `updated_at`

**roles** — Three predefined: `viewer`, `analyst`, `admin` with descriptions

**audit_log** — `user_id`, `action`, `resource_type`, `resource_id`, `details`, `timestamp`

Foreign keys are enforced via `PRAGMA foreign_keys = ON`.

---

## Setup

```bash
cd finance-backend
python -m venv venv && venv\Scripts\activate    # Windows
pip install -r requirements.txt
python app.py
```

Runs at `http://localhost:5000`. Database initializes automatically with schema, roles, demo users, and sample records.

To reset: delete `finance.db` and restart.

---

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Viewer | `viewer_user` | `viewer123` |
| Analyst | `analyst_user` | `analyst123` |
| Admin | `admin_user` | `admin123` |

```bash
# Authenticate
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_user","password":"admin123"}'

# Query dashboard
curl http://localhost:5000/dashboard/summary \
  -H "Authorization: Bearer admin_user:admin123"
```

---

## Design Decisions

| Decision | Rationale | Tradeoff |
|----------|-----------|----------|
| **Flask over Django** | No ORM or admin panel needed. Flask allows full control over project structure without framework opinions. | Less built-in tooling, but cleaner for a focused API project. |
| **Raw SQL over ORM** | Aggregation queries (GROUP BY, CASE WHEN, strftime) are cleaner in raw SQL. Avoids ORM abstraction leaks. | Manual query construction, but parameterized queries prevent injection. |
| **Decorator-based auth** | `@authenticate_user` and `@require_role` are composable — any route gets auth by adding a decorator. No repeated boilerplate. | Tightly coupled to Flask's `g` context. Acceptable for this scope. |
| **Soft deletes** | Financial records should never be permanently destroyed. The `is_deleted` flag preserves audit integrity while hiding records from queries. | Requires filtering `is_deleted = 0` in every record query. |
| **Plaintext passwords** | Scoped to demo. The architecture supports swapping in `werkzeug.security.generate_password_hash` with zero structural changes. | Not production-safe. Documented explicitly. |
| **Audit log isolation** | Logging is wrapped in try/except — a logging failure must never cascade into a failed business operation. | Silent logging failures. Acceptable for non-critical audit trail. |

---

## Future Improvements

- **JWT Authentication** — Token expiration, refresh flow, and stateless session management to replace demo Bearer tokens
- **Scalable RBAC Middleware** — Permission-based access control (e.g., `can:create_record`) instead of role-name matching, enabling granular policy definitions
- **Cursor-Based Pagination** — Replace offset pagination with cursor tokens for consistent performance on growing datasets
- **Time-Series Analytics** — Rolling averages, year-over-year comparisons, and anomaly detection on spending patterns
- **Automated Test Suite** — Unit tests for validation and models, integration tests for endpoint behavior, role-based access matrix testing with `pytest`
- **API Versioning** — URL-prefixed versioning (`/api/v1/`) to support backward-compatible evolution
