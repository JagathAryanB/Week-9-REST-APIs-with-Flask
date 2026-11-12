import os
import logging

os.environ.setdefault('DISABLE_SQLALCHEMY_CEXT', '1')
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, send_from_directory
from werkzeug.exceptions import HTTPException

from config import config
from app.utils.extensions import db, jwt, migrate, cors, limiter
from app.utils.responses import error_response, success_response


def create_app(config_name=None):
    """
    Application factory for the Task Management REST API.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config.get('CORS_ORIGINS', '*')}})
    limiter.init_app(app)

    # Register Blueprints
    from app.auth.routes import auth_bp
    from app.tasks.routes import tasks_bp
    from app.users.routes import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(users_bp)

    # JWT Error Callbacks matching Problem Statement specifications
    @jwt.unauthorized_loader
    def unauthorized_callback(reason):
        return error_response("Missing or invalid token", 401)

    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return error_response("Missing or invalid token", 401)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return error_response("Token has expired", 401)

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return error_response("Token has been revoked", 401)

    # Custom HTTP Error Handlers
    @app.errorhandler(400)
    def bad_request_error(e):
        return error_response(getattr(e, 'description', 'Bad Request'), 400)

    @app.errorhandler(401)
    def unauthorized_error(e):
        return error_response("Missing or invalid token", 401)

    @app.errorhandler(403)
    def forbidden_error(e):
        return error_response(getattr(e, 'description', 'Forbidden'), 403)

    @app.errorhandler(404)
    def not_found_error(e):
        return error_response(getattr(e, 'description', 'Resource not found'), 404)

    @app.errorhandler(405)
    def method_not_allowed_error(e):
        return error_response("Method Not Allowed", 405)

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return error_response(f"Rate limit exceeded: {e.description}", 429)

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal server error: {str(e)}")
        return error_response("Internal Server Error", 500)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(e):
        if isinstance(e, HTTPException):
            return error_response(e.description, e.code)
        app.logger.exception("An unhandled exception occurred")
        return error_response("Internal Server Error", 500)

    # Root route and API health check
    @app.route('/')
    def root():
        return success_response({
            'message': 'Welcome to Task Management REST API',
            'version': 'v1',
            'endpoints': {
                'auth': '/api/auth',
                'tasks': '/api/tasks',
                'users': '/api/users',
                'docs': '/api/docs'
            }
        })

    # Serve Swagger UI / OpenAPI docs
    docs_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'docs')

    @app.route('/api/docs')
    def api_docs():
        swagger_html = """
        <!DOCTYPE html>
        <html>
        <head>
          <title>Task Management API Docs</title>
          <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css" />
          <style>body { margin: 0; padding: 0; }</style>
        </head>
        <body>
          <div id="swagger-ui"></div>
          <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
          <script>
            window.onload = function() {
              SwaggerUIBundle({
                url: "/docs/swagger.yaml",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                  SwaggerUIBundle.presets.apis,
                  SwaggerUIBundle.SwaggerUIStandalonePreset
                ]
              });
            };
          </script>
        </body>
        </html>
        """
        return swagger_html

    @app.route('/docs/swagger.yaml')
    def serve_swagger_yaml():
        return send_from_directory(docs_dir, 'swagger.yaml')

    # Configure Logging
    if not app.debug and not app.testing:
        logs_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'task_api.log'),
            maxBytes=1024000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Task Management REST API startup')

    return app

