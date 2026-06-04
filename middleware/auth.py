"""
Session-based Authentication Middleware
RBAC role hierarchy and route protection for hardened API access
"""

from functools import wraps
from flask import session, jsonify, request, g


def require_auth(required_role: str = "viewer"):
    """
    Decorator to protect routes with session-based auth and RBAC.
    Usage: @app.route("/admin-only") @require_auth("admin")
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user session exists
            if "user" not in session:
                return jsonify({
                    "error": "Authentication required",
                    "guidance": "Please log in at /login to access this dashboard resource."
                }), 401
            
            user_role = session["user"].get("role", "viewer")
            
            # RBAC Hierarchy: viewer (1) < admin (2) < superadmin (3)
            roles = {"viewer": 1, "admin": 2, "superadmin": 3}
            if roles.get(user_role, 0) < roles.get(required_role, 0):
                return jsonify({
                    "error": "Access denied",
                    "guidance": f"This action requires '{required_role}' privileges. Your current role is '{user_role}'."
                }), 403
            
            # Attach user info to Flask g for use within the route handler
            g.user = session["user"]
            g.role = user_role
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def is_authenticated():
    """Check if user is authenticated in the current session"""
    return "user" in session


def get_current_user():
    """Get the current user from session"""
    return session.get("user")


def get_current_role():
    """Get the current user's role"""
    return session.get("user", {}).get("role", "viewer")
