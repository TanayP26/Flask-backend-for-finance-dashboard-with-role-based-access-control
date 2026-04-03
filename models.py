"""
Data models for the finance backend.
Handles all database queries for users, roles, and financial records.
Each model class has static methods that interact with the database.
"""

from database import get_db
from utils.errors import NotFoundError, ConflictError, ValidationError


class Role:
    """Model for user roles (viewer, analyst, admin)"""

    @staticmethod
    def get_all():
        """Get all roles from the database"""
        conn = get_db()
        roles = conn.execute("SELECT * FROM roles").fetchall()
        conn.close()
        return [dict(r) for r in roles]

    @staticmethod
    def get_by_id(role_id):
        """Get a single role by its ID"""
        conn = get_db()
        role = conn.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
        conn.close()
        if not role:
            return None
        return dict(role)

    @staticmethod
    def get_by_name(name):
        """Get a role by its name (viewer/analyst/admin)"""
        conn = get_db()
        role = conn.execute(
            "SELECT * FROM roles WHERE name = ?", (name.lower(),)
        ).fetchone()
        conn.close()
        if not role:
            return None
        return dict(role)


class User:
    """Model for user accounts"""

    @staticmethod
    def get_all():
        """Get all users with their role names"""
        conn = get_db()
        users = conn.execute('''
            SELECT u.id, u.username, u.email, u.role_id, u.status,
                   u.created_at, u.updated_at, r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            ORDER BY u.id
        ''').fetchall()
        conn.close()
        return [dict(u) for u in users]

    @staticmethod
    def get_by_id(user_id):
        """Get a single user by ID (with role info)"""
        conn = get_db()
        user = conn.execute('''
            SELECT u.id, u.username, u.email, u.password_hash,
                   u.role_id, u.status, u.created_at, u.updated_at,
                   r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.id = ?
        ''', (user_id,)).fetchone()
        conn.close()
        if not user:
            return None
        return dict(user)

    @staticmethod
    def get_by_username(username):
        """Find a user by their username"""
        conn = get_db()
        user = conn.execute('''
            SELECT u.id, u.username, u.email, u.password_hash,
                   u.role_id, u.status, u.created_at, u.updated_at,
                   r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = ?
        ''', (username,)).fetchone()
        conn.close()
        if not user:
            return None
        return dict(user)

    @staticmethod
    def create(username, email, password, role_id):
        """
        Create a new user. Checks for duplicate username/email.
        Returns the created user dict.
        """
        conn = get_db()

        # check if username already taken
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            conn.close()
            raise ConflictError(f"Username '{username}' is already taken")

        # check if email already taken
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            conn.close()
            raise ConflictError(f"Email '{email}' is already registered")

        cursor = conn.execute(
            """INSERT INTO users (username, email, password_hash, role_id)
               VALUES (?, ?, ?, ?)""",
            (username, email, password, role_id)
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        return User.get_by_id(new_id)

    @staticmethod
    def update(user_id, **kwargs):
        """
        Update user fields. Only updates the fields that are provided.
        kwargs can include: username, email, password, role_id, status
        """
        user = User.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        conn = get_db()

        # check for duplicate username if being changed
        if 'username' in kwargs and kwargs['username'] != user['username']:
            existing = conn.execute(
                "SELECT id FROM users WHERE username = ? AND id != ?",
                (kwargs['username'], user_id)
            ).fetchone()
            if existing:
                conn.close()
                raise ConflictError(f"Username '{kwargs['username']}' is already taken")

        # check for duplicate email if being changed
        if 'email' in kwargs and kwargs['email'] != user['email']:
            existing = conn.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?",
                (kwargs['email'], user_id)
            ).fetchone()
            if existing:
                conn.close()
                raise ConflictError(f"Email '{kwargs['email']}' is already registered")

        # build the update query dynamically
        update_fields = []
        values = []

        field_mapping = {
            'username': 'username',
            'email': 'email',
            'password': 'password_hash',
            'role_id': 'role_id',
            'status': 'status',
        }

        for key, column in field_mapping.items():
            if key in kwargs:
                update_fields.append(f"{column} = ?")
                values.append(kwargs[key])

        if not update_fields:
            conn.close()
            return user  # nothing to update

        # add updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)

        query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
        conn.close()

        return User.get_by_id(user_id)

    @staticmethod
    def delete(user_id):
        """Delete a user from the database"""
        user = User.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")

        conn = get_db()
        conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def to_safe_dict(user):
        """
        Convert user dict to a safe version (no password).
        Use this when returning user data in API responses.
        """
        if not user:
            return None
        safe = dict(user)
        safe.pop('password_hash', None)
        return safe


class FinancialRecord:
    """Model for financial records (income/expense transactions)"""

    @staticmethod
    def get_by_id(record_id):
        """Get a single record by ID (only non-deleted)"""
        conn = get_db()
        record = conn.execute('''
            SELECT fr.*, u.username as user_name
            FROM financial_records fr
            JOIN users u ON fr.user_id = u.id
            WHERE fr.id = ? AND fr.is_deleted = 0
        ''', (record_id,)).fetchone()
        conn.close()
        if not record:
            return None
        return dict(record)

    @staticmethod
    def get_filtered(user_id=None, record_type=None, category=None,
                     start_date=None, end_date=None, page=1, per_page=20):
        """
        Get records with optional filters.
        Supports filtering by user, type, category, and date range.
        Returns (records_list, total_count).
        """
        conn = get_db()

        # build query with filters
        where_clauses = ["fr.is_deleted = 0"]
        params = []

        if user_id:
            where_clauses.append("fr.user_id = ?")
            params.append(user_id)

        if record_type:
            where_clauses.append("fr.type = ?")
            params.append(record_type)

        if category:
            where_clauses.append("fr.category = ?")
            params.append(category)

        if start_date:
            where_clauses.append("fr.record_date >= ?")
            params.append(start_date)

        if end_date:
            where_clauses.append("fr.record_date <= ?")
            params.append(end_date)

        where_sql = " AND ".join(where_clauses)

        # get total count first
        count_query = f"SELECT COUNT(*) as total FROM financial_records fr WHERE {where_sql}"
        total = conn.execute(count_query, params).fetchone()['total']

        # get paginated records
        offset = (page - 1) * per_page
        data_query = f"""
            SELECT fr.*, u.username as user_name
            FROM financial_records fr
            JOIN users u ON fr.user_id = u.id
            WHERE {where_sql}
            ORDER BY fr.record_date DESC, fr.id DESC
            LIMIT ? OFFSET ?
        """
        records = conn.execute(data_query, params + [per_page, offset]).fetchall()
        conn.close()

        return [dict(r) for r in records], total

    @staticmethod
    def create(user_id, amount, record_type, category,
               description=None, record_date=None):
        """Create a new financial record"""
        conn = get_db()
        cursor = conn.execute(
            """INSERT INTO financial_records
               (user_id, amount, type, category, description, record_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, amount, record_type, category, description, record_date)
        )
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        return FinancialRecord.get_by_id(new_id)

    @staticmethod
    def update(record_id, **kwargs):
        """
        Update a financial record.
        Only updates the fields that are provided in kwargs.
        """
        record = FinancialRecord.get_by_id(record_id)
        if not record:
            raise NotFoundError("Record not found")

        conn = get_db()

        update_fields = []
        values = []

        allowed_fields = {
            'amount': 'amount',
            'type': 'type',
            'category': 'category',
            'description': 'description',
            'record_date': 'record_date',
        }

        for key, column in allowed_fields.items():
            if key in kwargs:
                update_fields.append(f"{column} = ?")
                values.append(kwargs[key])

        if not update_fields:
            conn.close()
            return record

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(record_id)

        query = f"UPDATE financial_records SET {', '.join(update_fields)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
        conn.close()

        return FinancialRecord.get_by_id(record_id)

    @staticmethod
    def soft_delete(record_id):
        """Soft delete a record (set is_deleted = 1)"""
        record = FinancialRecord.get_by_id(record_id)
        if not record:
            raise NotFoundError("Record not found")

        conn = get_db()
        conn.execute(
            "UPDATE financial_records SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (record_id,)
        )
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def get_categories(user_id=None):
        """Get list of all unique categories"""
        conn = get_db()

        if user_id:
            categories = conn.execute(
                """SELECT DISTINCT category FROM financial_records
                   WHERE is_deleted = 0 AND user_id = ?
                   ORDER BY category""",
                (user_id,)
            ).fetchall()
        else:
            categories = conn.execute(
                """SELECT DISTINCT category FROM financial_records
                   WHERE is_deleted = 0 ORDER BY category"""
            ).fetchall()

        conn.close()
        return [row['category'] for row in categories]

    @staticmethod
    def get_summary(user_id=None):
        """
        Get summary statistics for records.
        If user_id is provided, only counts that user's records.
        """
        conn = get_db()

        where = "WHERE is_deleted = 0"
        params = []
        if user_id:
            where += " AND user_id = ?"
            params.append(user_id)

        # total income
        income = conn.execute(
            f"SELECT COALESCE(SUM(amount), 0) as total FROM financial_records {where} AND type = 'income'",
            params
        ).fetchone()['total']

        # total expense
        expense = conn.execute(
            f"SELECT COALESCE(SUM(amount), 0) as total FROM financial_records {where} AND type = 'expense'",
            params
        ).fetchone()['total']

        # record count
        count = conn.execute(
            f"SELECT COUNT(*) as cnt FROM financial_records {where}",
            params
        ).fetchone()['cnt']

        # date range
        dates = conn.execute(
            f"SELECT MIN(record_date) as earliest, MAX(record_date) as latest FROM financial_records {where}",
            params
        ).fetchone()

        conn.close()

        return {
            "total_income": round(income, 2),
            "total_expense": round(expense, 2),
            "net_balance": round(income - expense, 2),
            "total_records": count,
            "earliest_record_date": dates['earliest'],
            "latest_record_date": dates['latest']
        }

    @staticmethod
    def get_category_breakdown(user_id=None, record_type=None):
        """
        Get income/expense breakdown by category.
        """
        conn = get_db()

        where = "WHERE is_deleted = 0"
        params = []
        if user_id:
            where += " AND user_id = ?"
            params.append(user_id)
        if record_type:
            where += " AND type = ?"
            params.append(record_type)

        rows = conn.execute(f'''
            SELECT category,
                   COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as income_total,
                   COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as expense_total
            FROM financial_records
            {where}
            GROUP BY category
            ORDER BY category
        ''', params).fetchall()

        conn.close()

        result = []
        for row in rows:
            result.append({
                "category": row['category'],
                "income_total": round(row['income_total'], 2),
                "expense_total": round(row['expense_total'], 2),
                "net": round(row['income_total'] - row['expense_total'], 2)
            })

        return result

    @staticmethod
    def get_monthly_trend(user_id=None, months=12):
        """
        Get monthly income/expense trend.
        Returns data for the last N months.
        """
        conn = get_db()

        where = "WHERE is_deleted = 0"
        params = []
        if user_id:
            where += " AND user_id = ?"
            params.append(user_id)

        rows = conn.execute(f'''
            SELECT strftime('%Y-%m', record_date) as month,
                   COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as income,
                   COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as expense,
                   COUNT(*) as transaction_count
            FROM financial_records
            {where}
            GROUP BY month
            ORDER BY month DESC
            LIMIT ?
        ''', params + [months]).fetchall()

        conn.close()

        result = []
        for row in rows:
            result.append({
                "month": row['month'],
                "income": round(row['income'], 2),
                "expense": round(row['expense'], 2),
                "net": round(row['income'] - row['expense'], 2),
                "transaction_count": row['transaction_count']
            })

        # reverse so it's in chronological order
        result.reverse()
        return result

    @staticmethod
    def get_recent(user_id=None, limit=10):
        """Get the most recent records"""
        conn = get_db()

        where = "WHERE fr.is_deleted = 0"
        params = []
        if user_id:
            where += " AND fr.user_id = ?"
            params.append(user_id)

        # cap the limit at 100
        if limit > 100:
            limit = 100

        rows = conn.execute(f'''
            SELECT fr.*, u.username as user_name
            FROM financial_records fr
            JOIN users u ON fr.user_id = u.id
            {where}
            ORDER BY fr.record_date DESC, fr.id DESC
            LIMIT ?
        ''', params + [limit]).fetchall()

        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_insights(user_id=None):
        """
        Get analytical insights:
        - highest expense category
        - highest income source
        - average transaction amount
        - most active month
        """
        conn = get_db()

        where = "WHERE is_deleted = 0"
        params = []
        if user_id:
            where += " AND user_id = ?"
            params.append(user_id)

        # highest expense category
        highest_expense = conn.execute(f'''
            SELECT category, SUM(amount) as total
            FROM financial_records
            {where} AND type = 'expense'
            GROUP BY category
            ORDER BY total DESC
            LIMIT 1
        ''', params).fetchone()

        # highest income source
        highest_income = conn.execute(f'''
            SELECT category, SUM(amount) as total
            FROM financial_records
            {where} AND type = 'income'
            GROUP BY category
            ORDER BY total DESC
            LIMIT 1
        ''', params).fetchone()

        # average transaction amount
        avg_amount = conn.execute(f'''
            SELECT AVG(amount) as avg_amt
            FROM financial_records
            {where}
        ''', params).fetchone()

        # most active month
        most_active = conn.execute(f'''
            SELECT strftime('%Y-%m', record_date) as month, COUNT(*) as cnt
            FROM financial_records
            {where}
            GROUP BY month
            ORDER BY cnt DESC
            LIMIT 1
        ''', params).fetchone()

        conn.close()

        return {
            "highest_expense_category": {
                "category": highest_expense['category'] if highest_expense else None,
                "total": round(highest_expense['total'], 2) if highest_expense else 0
            },
            "highest_income_source": {
                "category": highest_income['category'] if highest_income else None,
                "total": round(highest_income['total'], 2) if highest_income else 0
            },
            "average_transaction_amount": round(avg_amount['avg_amt'], 2) if avg_amount and avg_amount['avg_amt'] else 0,
            "most_active_month": {
                "month": most_active['month'] if most_active else None,
                "transaction_count": most_active['cnt'] if most_active else 0
            }
        }
