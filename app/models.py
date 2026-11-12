from datetime import datetime, timezone, timedelta
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    created_tasks = db.relationship(
        'Task',
        foreign_keys='Task.user_id',
        backref=db.backref('creator', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    assigned_tasks = db.relationship(
        'Task',
        foreign_keys='Task.assigned_to_id',
        backref=db.backref('assigned_user', lazy='joined'),
        lazy='dynamic'
    )
    comments = db.relationship(
        'Comment',
        backref=db.backref('author', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        token = secrets.token_urlsafe(32)
        self.reset_token = token
        # Expires in 1 hour
        self.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        return token

    def verify_reset_token(self, token):
        if not self.reset_token or self.reset_token != token:
            return False
        if not self.reset_token_expires:
            return False
        now = datetime.now(timezone.utc)
        expires = self.reset_token_expires
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now < expires

    def to_dict(self, include_sensitive=False):
        created_str = self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if self.created_at else None
        updated_str = self.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if self.updated_at else None
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': created_str,
            'updated_at': updated_str
        }
        return data

    def __repr__(self):
        return f"<User {self.username}>"


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, default='', nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    priority = db.Column(db.String(20), default='medium', nullable=False, index=True)
    category = db.Column(db.String(50), default='general', nullable=False, index=True)
    due_date = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)

    # Relationships
    comments = db.relationship(
        'Comment',
        backref='task',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def to_dict(self, include_comments=False):
        due_date_str = None
        if self.due_date:
            due_date_str = self.due_date.strftime("%Y-%m-%d") if self.due_date.hour == 0 and self.due_date.minute == 0 else self.due_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        created_str = self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if self.created_at else None
        updated_str = self.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if self.updated_at else None

        data = {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'status': self.status,
            'priority': self.priority,
            'category': self.category,
            'due_date': due_date_str,
            'created_at': created_str,
            'updated_at': updated_str,
            'user_id': self.user_id,
            'assigned_to_id': self.assigned_to_id
        }

        if include_comments:
            data['comments'] = [c.to_dict() for c in self.comments.order_by(Comment.created_at.asc())]

        return data

    def __repr__(self):
        return f"<Task {self.title}>"


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        created_str = self.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if self.created_at else None
        return {
            'id': self.id,
            'content': self.content,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'username': self.author.username if self.author else None,
            'created_at': created_str
        }

    def __repr__(self):
        return f"<Comment id={self.id} task_id={self.task_id}>"
