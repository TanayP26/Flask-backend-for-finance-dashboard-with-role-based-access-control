"""
Finance Backend - Main Application
====================================
A Flask-based backend for managing financial records with
role-based access control. Built as part of a backend
development assignment.

Author: Tanay Prasad
Date: April 2026

Run this file to start the server:
    python app.py
"""

import sys
import os

# add project root to python path so imports work properly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify

from database import init_db
from utils.errors import APIError

# import blueprints
from routes import auth_bp, user_bp, record_bp, dashboard_bp


def create_app():
    """
    Create and configure the Flask application.
    This is a factory function so we can create multiple
    app instances for testing if needed..
    """
    app = Flask(__name__)

    # basic config
    app.config['JSON_SORT_KEYS'] = False  # keep json key order as-is

    # ---- Register Blueprints ----
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(record_bp)
    app.register_blueprint(dashboard_bp)

    # ---- Error Handlers ----

    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle our custom API errors"""
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors"""
        return jsonify({
            "error": "Bad Request",
            "message": "The request was invalid or malformed"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors for routes that don't exist"""
        return jsonify({
            "error": "Not Found",
            "message": "The requested URL was not found on this server"
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle wrong HTTP method errors"""
        return jsonify({
            "error": "Method Not Allowed",
            "message": "This HTTP method is not allowed for this endpoint"
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        """Handle unexpected server errors"""
        return jsonify({
            "error": "Internal Server Error",
            "message": "Something went wrong on our end. Please try again later."
        }), 500

    # ---- Root Route ----

    @app.route('/')
    def index():
        """
        Root endpoint - shows basic API info.
        Useful for checking if the server is running.
        """
        return jsonify({
            "name": "Finance Dashboard Backend API",
            "version": "1.0.0",
            "description": "Backend API for managing financial records with role-based access control",
            "endpoints": {
                "auth": {
                    "POST /auth/login": "Login with username and password",
                    "GET /auth/me": "Get current user profile"
                },
                "users": {
                    "GET /users": "List all users (admin/analyst)",
                    "GET /users/<id>": "Get user details",
                    "POST /users": "Create user (admin)",
                    "PUT /users/<id>": "Update user (admin)",
                    "DELETE /users/<id>": "Delete user (admin)"
                },
                "records": {
                    "GET /records": "List records (with filters)",
                    "GET /records/<id>": "Get single record",
                    "POST /records": "Create record (analyst/admin)",
                    "PUT /records/<id>": "Update record",
                    "DELETE /records/<id>": "Soft delete record",
                    "GET /records/categories": "List all categories"
                },
                "dashboard": {
                    "GET /dashboard/summary": "Financial summary stats",
                    "GET /dashboard/category-breakdown": "Breakdown by category",
                    "GET /dashboard/monthly-trend": "Monthly income/expense trend",
                    "GET /dashboard/recent-activity": "Recent transactions",
                    "GET /dashboard/insights": "Analytical insights"
                }
            },
            "demo_credentials": {
                "viewer": "viewer_user / viewer123",
                "analyst": "analyst_user / analyst123",
                "admin": "admin_user / admin123"
            }
        }), 200

    @app.route('/health')
    def health_check():
        """Simple health check endpoint"""
        return jsonify({
            "status": "healthy",
            "message": "Server is running fine!"
        }), 200

    return app


# ---- Main Entry Point ----

if __name__ == '__main__':
    print("=" * 50)
    print("  Finance Dashboard Backend")
    print("  Starting up...")
    print("=" * 50)

    # initialize the database (creates tables and demo data)
    init_db()

    # create and run the app
    app = create_app()

    print("\n[+] Server is ready!")
    print("[+] Running at: http://localhost:5000")
    print("[+] Press Ctrl+C to stop\n")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
