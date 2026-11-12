from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from email_validator import validate_email, EmailNotValidError
from app.utils.extensions import db
from app.models import User
from app.utils.responses import success_response, error_response

users_bp = Blueprint('users', __name__, url_prefix='/api/users')
users_api = Api(users_bp)


class UserListResource(Resource):
    """Resource for listing users (e.g. for task assignment or admin directory)."""

    @jwt_required()
    def get(self):
        search = request.args.get('search') or request.args.get('q')
        query = User.query

        if search:
            pattern = f"%{search}%"
            query = query.filter((User.username.ilike(pattern)) | (User.email.ilike(pattern)))

        users = query.order_by(User.username.asc()).all()
        return success_response({
            'users': [u.to_dict() for u in users]
        })


class UserResource(Resource):
    """Resource for fetching and updating individual users."""

    @jwt_required()
    def get(self, user_id):
        user = db.session.get(User, user_id)
        if not user:
            return error_response('User not found', 404)
        return success_response({'user': user.to_dict()})

    @jwt_required()
    def put(self, user_id):
        current_user_id = int(get_jwt_identity())
        current_user = db.session.get(User, current_user_id)

        # Allow user to update their own profile, or an admin
        if current_user_id != user_id and (not current_user or current_user.role != 'admin'):
            return error_response('Forbidden: Cannot update other users', 403)

        target_user = db.session.get(User, user_id)
        if not target_user:
            return error_response('User not found', 404)

        data = request.get_json(silent=True) or {}
        errors = {}

        if 'email' in data:
            new_email = data['email']
            try:
                validate_email(new_email, check_deliverability=False)
                existing = User.query.filter(User.email == new_email, User.id != user_id).first()
                if existing:
                    errors['email'] = ['Email is already in use by another account']
                else:
                    target_user.email = new_email
            except EmailNotValidError as e:
                errors['email'] = [str(e)]

        if 'username' in data:
            new_username = data['username'].strip()
            if len(new_username) < 3 or len(new_username) > 50:
                errors['username'] = ['Username must be between 3 and 50 characters']
            else:
                existing = User.query.filter(User.username == new_username, User.id != user_id).first()
                if existing:
                    errors['username'] = ['Username is already taken']
                else:
                    target_user.username = new_username

        if 'role' in data:
            # Only admin can change roles
            if current_user and current_user.role == 'admin':
                if data['role'] in ['user', 'admin']:
                    target_user.role = data['role']
                else:
                    errors['role'] = ["Role must be 'user' or 'admin'"]
            else:
                errors['role'] = ['Only admins can update user role']

        if 'password' in data:
            new_pass = data['password']
            if len(new_pass) < 8:
                errors['password'] = ['Password must be at least 8 characters long']
            else:
                target_user.set_password(new_pass)

        if errors:
            return error_response(errors, 400)

        db.session.commit()
        return success_response({
            'message': 'User profile updated successfully',
            'user': target_user.to_dict()
        })

    @jwt_required()
    def delete(self, user_id):
        current_user_id = int(get_jwt_identity())
        current_user = db.session.get(User, current_user_id)

        if not current_user or current_user.role != 'admin':
            return error_response('Forbidden: Only admins can delete users', 403)

        target_user = db.session.get(User, user_id)
        if not target_user:
            return error_response('User not found', 404)

        db.session.delete(target_user)
        db.session.commit()
        return success_response({'message': 'User deleted successfully'})


users_api.add_resource(UserListResource, '')
users_api.add_resource(UserResource, '/<int:user_id>')
