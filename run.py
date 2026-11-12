import os
import sys

# Disable C extensions so Windows Application Control policies never block .pyd/.dll files
os.environ.setdefault('DISABLE_SQLALCHEMY_CEXT', '1')

from app import create_app, db
from app.models import User, Task, Comment

config_name = os.environ.get('FLASK_CONFIG', 'development')
app = create_app(config_name)


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Task': Task, 'Comment': Comment}


@app.cli.command("init-db")
def init_db():
    """Initialize database tables."""
    with app.app_context():
        db.create_all()
        print("Database initialized successfully.")


@app.cli.command("seed-db")
def seed_db():
    """Seed database with demo data."""
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="john_doe").first():
            user = User(username="john_doe", email="john@example.com", role="user")
            user.set_password("SecurePass123")
            db.session.add(user)
            db.session.commit()

            admin = User(username="admin_user", email="admin@example.com", role="admin")
            admin.set_password("AdminSecurePass123")
            db.session.add(admin)
            db.session.commit()

            task = Task(
                title="Complete API project",
                description="Finish task management API",
                status="in_progress",
                priority="high",
                category="development",
                user_id=user.id
            )
            db.session.add(task)
            db.session.commit()
            print("Database seeded with sample user and tasks.")
        else:
            print("Database already contains seed data.")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    if len(sys.argv) > 1 and sys.argv[1] in ['init-db', 'seed-db', 'routes', 'shell']:
        app.cli()
    else:
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=app.config.get('DEBUG', True))
