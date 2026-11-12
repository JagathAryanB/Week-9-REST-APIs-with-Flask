from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from app.models import User


def generate_tokens(user):
    """
    Generate access and refresh tokens for a user.
    Uses user.id as the JWT identity (string).
    """
    identity = str(user.id)
    additional_claims = {
        'username': user.username,
        'email': user.email,
        'role': user.role
    }
    access_token = create_access_token(identity=identity, additional_claims=additional_claims)
    refresh_token = create_refresh_token(identity=identity)
    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def get_current_user():
    """
    Retrieve the User instance corresponding to current JWT identity.
    """
    identity = get_jwt_identity()
    if not identity:
        return None
    try:
        user_id = int(identity)
        return User.query.get(user_id)
    except (ValueError, TypeError):
        return None

