from functools import wraps
from flask import current_app, redirect, url_for
from flask_login import current_user

def login_required(role=["ANY"]):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                return current_app.login_manager.unauthorized()
            user_role = current_user.get_role()
            if ( (user_role not in role) and (role != ["ANY"])):
                return current_app.login_manager.unauthorized()      
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

def role_excluded(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated and current_user.get_role() in role:  # Check for authentication and role
                return redirect(url_for('programs.programs'))  # Forbidden for these roles
            return func(*args, **kwargs)
        return wrapper
    return decorator