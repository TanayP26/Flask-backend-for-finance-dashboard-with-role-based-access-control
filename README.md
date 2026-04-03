# Finance Dashboard Backend

A RESTful API for managing financial records with role-based access control, built using Flask and SQLite. Implements layered authorization (Admin / Analyst / Viewer), full CRUD with soft deletes, and aggregation-based analytics — structured around clean separation of concerns.

---

## Features

- **Role-Based Access Control** — Three-tier permission system enforced via composable decorators at the route level
- **Financial Records CRUD** — Create, read, update, soft-delete with multi-parameter filtering and pagination
- **Dashboard Analytics** — Summary stats, category breakdowns, monthly trends, recent activity, and insights
- **Audit Trail** — All write operations are logged with user, action, and timestamp
- **Consistent Error Handling** — Custom exception hierarchy mapped to proper HTTP status codes

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Flask 2.3.3 |
| Database  | SQLite3 |
| Language  | Python 3.7+ |
| Auth      | Bearer Token |

Zero external services. Two dependencies: `Flask`, `Werkzeug`.

---

## Architecture

```
app.py              → App factory, error handlers, blueprint registration
middleware.py        → @authenticate_user, @require_role decorators
models.py            → Data access layer (raw SQL, no ORM)
database.py          → Connection management, schema init, seeding
routes/              → Endpoint handlers grouped by domain
utils/               → Input validation + custom error classes
```

**Request lifecycle:**
```
Request → Blueprint Router → Auth Middleware → Role Check → Validation → Model Query → Response
```

**Access control** is decorator-driven — `@authenticate_user` extracts credentials and injects the user into request context, `@require_role` gates by role. Record ownership is enforced at the query level, not just the route level.

```
Viewer   → Read own data only
Analyst  → Full CRUD on own records + analytics
Admin    → Unrestricted access + user management
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate, receive token |
| GET | `/auth/me` | Current user profile |

### Users (Admin only for writes)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users` | List users |
| POST / PUT / DELETE | `/users/<id>` | Create, update, delete user |

### Records
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/records` | List with filters: `type`, `category`, `start_date`, `end_date`, `page` |
| POST | `/records` | Create record (Analyst/Admin) |
| PUT / DELETE | `/records/<id>` | Update / soft-delete (Owner/Admin) |
| GET | `/records/categories` | Unique category list |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/summary` | Income, expense, net balance |
| GET | `/dashboard/category-breakdown` | Per-category split |
| GET | `/dashboard/monthly-trend` | Month-over-month trend |
| GET | `/dashboard/recent-activity` | Recent transactions |
| GET | `/dashboard/insights` | Top categories, averages |

Admins can append `?user_id=<id>` to view any user's data.

---

## Data Model

**Users** — `id`, `username` (unique), `email` (unique), `password_hash`, `role_id` → roles, `status` (active/inactive), timestamps

**Financial Records** — `id`, `user_id` → users, `amount`, `type` (income/expense), `category`, `description`, `record_date`, `is_deleted` (soft delete flag), timestamps

**Supporting:** `roles` (3 predefined), `audit_log` (tracks all mutations)

---

## Setup

```bash
cd finance-backend
python -m venv venv && venv\Scripts\activate    # Windows
pip install -r requirements.txt
python app.py
```

Server runs at `http://localhost:5000`. Database auto-creates on first run.  
Reset: delete `finance.db` and restart.

---

## Demo Credentials

| Role | Username | Password |
|------|----------|----------|
| Viewer | `viewer_user` | `viewer123` |
| Analyst | `analyst_user` | `analyst123` |
| Admin | `admin_user` | `admin123` |

```bash
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin_user","password":"admin123"}'
```

---

## Design Decisions

| Decision | Why |
|----------|-----|
| Plaintext passwords | Demo scope. Production: `werkzeug.security.generate_password_hash` |
| Bearer `user:pass` tokens | Avoids JWT complexity. Stateless, easy to test |
| Raw SQL, no ORM | Full control over aggregation queries. Minimal dependencies |
| Soft deletes on records | Financial data should never be permanently destroyed |
| Decorator-based auth | Keeps route handlers clean and auth logic reusable |
| Audit log in try/except | Logging failures must never break primary operations |

---

## Future Improvements

- JWT auth with token expiration and refresh
- Password hashing with bcrypt
- Rate limiting and API versioning (`/api/v1/`)
- Cursor-based pagination for large datasets
- Automated test suite with pytest
