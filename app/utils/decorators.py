from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from app.utils.responses import error_response


def paginate(default_page=1, default_per_page=10, max_per_page=100):
    """
    Decorator to parse and validate pagination query parameters.
    Injects 'page' and 'per_page' into kwargs if needed.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                page = int(request.args.get('page', default_page))
                if page < 1:
                    page = default_page
            except (ValueError, TypeError):
                page = default_page

            try:
                per_page = int(request.args.get('per_page', default_per_page))
                if per_page < 1:
                    per_page = default_per_page
                elif per_page > max_per_page:
                    per_page = max_per_page
            except (ValueError, TypeError):
                per_page = default_per_page

            kwargs['page'] = page
            kwargs['per_page'] = per_page
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(*allowed_roles):
    """
    Decorator to restrict access based on user role (e.g. 'admin', 'user').
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            from app.models import User
            user = User.query.get(current_user_id)
            if not user or (allowed_roles and user.role not in allowed_roles):
                return error_response('Forbidden: You do not have permission for this resource', 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

