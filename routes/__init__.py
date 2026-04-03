"""
Routes package - contains all the API endpoint blueprints.
Each file handles a different group of endpoints.

Blueprints:
    auth_bp      - login and profile endpoints (/auth)
    user_bp      - user management endpoints (/users)
    record_bp    - financial records CRUD (/records)
    dashboard_bp - analytics and summaries (/dashboard)
"""

from .auth_routes import auth_bp
from .user_routes import user_bp
from .record_routes import record_bp
from .dashboard_routes import dashboard_bp
