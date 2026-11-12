from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.extensions import db
from app.models import User
from app.utils.validators import validate_user_registration, validate_user_login
from app.utils.responses import success_response, error_response
from app.auth.utils import generate_tokens

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_api = Api(auth_bp)


class RegisterResource(Resource):
    """Resource for user registration."""

    def post(self):
        data = request.get_json(silent=True) or {}
        validation = validate_user_registration(data)
        if not validation['valid']:
            return error_response(validation['errors'], 400)

        # Check existing user
        if User.query.filter_by(username=data['username']).first():
            return error_response({'username': ['Username is already taken']}, 400)

        if User.query.filter_by(email=data['email']).first():
            return error_response({'email': ['Email is already registered']}, 400)

        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        tokens = generate_tokens(user)
        return success_response({
            'message': 'User registered successfully',
            'user': user.to_dict(),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }, 201)


class LoginResource(Resource):
    """Resource for user login."""

    def post(self):
        data = request.get_json(silent=True) or {}
        validation = validate_user_login(data)
        if not validation['valid']:
            return error_response(validation['errors'], 400)

        identifier = data.get('username') or data.get('email')
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if not user or not user.check_password(data.get('password')):
            return error_response('Invalid username/email or password', 401)

        tokens = generate_tokens(user)
        return success_response({
            'message': 'Login successful',
            'user': user.to_dict(),
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token']
        }, 200)


class RefreshTokenResource(Resource):
    """Resource to refresh an access token using a refresh token."""

    @jwt_required(refresh=True)
    def post(self):
        current_identity = get_jwt_identity()
        user = db.session.get(User, int(current_identity))
        if not user:
            return error_response('User not found', 404)

        tokens = generate_tokens(user)
        return success_response({
            'access_token': tokens['access_token']
        }, 200)


class PasswordResetRequestResource(Resource):
    """Resource to initiate a password reset."""

    def post(self):
        data = request.get_json(silent=True) or {}
        email = data.get('email')
        if not email:
            return error_response({'email': ['Email is required']}, 400)

        user = User.query.filter_by(email=email).first()
        if not user:
            # Return success to prevent email enumeration
            return success_response({
                'message': 'If the email is registered, a password reset token has been generated'
            }, 200)

        token = user.generate_reset_token()
        db.session.commit()

        return success_response({
            'message': 'Password reset token generated successfully',
            'reset_token': token
        }, 200)


class PasswordResetResource(Resource):
    """Resource to reset password using a reset token."""

    def post(self):
        data = request.get_json(silent=True) or {}
        token = data.get('token')
        new_password = data.get('new_password')

        errors = {}
        if not token:
            errors['token'] = ['Reset token is required']
        if not new_password or len(new_password) < 8:
            errors['new_password'] = ['New password must be at least 8 characters long']

        if errors:
            return error_response(errors, 400)

        user = User.query.filter_by(reset_token=token).first()
        if not user or not user.verify_reset_token(token):
            return error_response('Invalid or expired reset token', 400)

        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()

        return success_response({
            'message': 'Password has been reset successfully'
        }, 200)


class MeResource(Resource):
    """Resource to get profile of currently authenticated user."""

    @jwt_required()
    def get(self):
        current_identity = get_jwt_identity()
        user = db.session.get(User, int(current_identity))
        if not user:
            return error_response('User not found', 404)
        return success_response({'user': user.to_dict()}, 200)


class LogoutResource(Resource):
    """Resource to logout user."""

    @jwt_required()
    def post(self):
        return success_response({
            'message': 'Successfully logged out'
        }, 200)


auth_api.add_resource(RegisterResource, '/register')
auth_api.add_resource(LoginResource, '/login')
auth_api.add_resource(RefreshTokenResource, '/refresh')
auth_api.add_resource(LogoutResource, '/logout')
auth_api.add_resource(PasswordResetRequestResource, '/reset-password-request', '/forgot-password')
auth_api.add_resource(PasswordResetResource, '/reset-password')
auth_api.add_resource(MeResource, '/me')
