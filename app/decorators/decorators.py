from functools import wraps
from flask import current_app, redirect, url_for
from flask_login import current_user
from ..models import Module, RoleAccess
from flask import abort

# def login_required(role=["ANY"]):
#     def wrapper(fn):
#         @wraps(fn)
#         def decorated_view(*args, **kwargs):
#             if not current_user.is_authenticated:
#                 return current_app.login_manager.unauthorized()
#             user_role = current_user.get_role()
#             if ( (user_role not in role) and (role != ["ANY"])):
#                 return current_app.login_manager.unauthorized()      
#             return fn(*args, **kwargs)
#         return decorated_view
#     return wrapper

def requires_module_access(module_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Retrieve the current user's role ID
            if current_user.is_authenticated:
                role_id = current_user.RoleId

                # Retrieve the module ID for the given module name
                module_id = Module.query.filter_by(Name=module_name).first().ModuleId

                # Check if the role has access to the module
                if not RoleAccess.query.filter_by(RoleId=role_id, ModuleId=module_id).first():
                    abort(403)  # Forbidden

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_excluded(role):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_user.is_authenticated and current_user.get_role() in role:  # Check for authentication and role
                return redirect(url_for('programs.programs'))  # Forbidden for these roles
            return func(*args, **kwargs)
        return wrapper
    return decorator