from flask import abort
from flask_login import current_user
from .models import Permission
from functools import wraps

def permission_required(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args,**kwargs):
            if not current_user.can(permission):
                abort(403)
            return func(*args,**kwargs)
        return wrapper
    return decorator

def admin_required(func):
    return permission_required(Permission.ADMINISTER)(func)
            
