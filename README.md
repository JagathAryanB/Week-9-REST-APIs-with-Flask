# Task Management REST API (Week 9 - REST APIs with Flask)

A complete, production-ready RESTful API for a Task Management System built with **Flask**, **Flask-RESTful**, **SQLAlchemy**, and **Flask-JWT-Extended**.

---

## 🚀 Features

- **Authentication System**:
  - Secure registration and login with password hashing (`Werkzeug security`).
  - JWT Authentication (Access + Refresh tokens) with `@jwt_required()`.
  - Token refresh and secure password reset workflows.
  - Role-based authorization (`user`, `admin`).
- **Task Management CRUD**:
  - Create, read, update (PUT/PATCH), and delete tasks.
  - Pagination (custom `page` and `per_page` controls).
  - Filtering by `status`, `priority`, and `category`.
  - Full-text search across `title` and `description` via query string `q`.
  - Sorting by any model field (`created_at`, `due_date`, `title`, etc.) in `asc` or `desc` order.
  - Task assignment to team members.
  - Task commenting system.
- **Robust Error Handling & Security**:
  - Standardized JSON responses for both success and error states.
  - Input validation with detailed field-level error messages.
  - Rate limiting via `Flask-Limiter` to protect endpoints.
  - Cross-Origin Resource Sharing (`CORS`) enabled.
  - Error logging with rotating file handler.
- **API Documentation & Testing**:
  - Interactive Swagger / OpenAPI documentation hosted at `/api/docs`.
  - Complete OpenAPI 3.0 specification (`docs/swagger.yaml`).
  - Comprehensive Markdown reference (`docs/api.md`).
  - Full Postman collection (`docs/postman_collection.json`).
  - Automated test suite with `pytest`.

---

## 📁 Project Structure

```
├── app/
│   ├── __init__.py              # Application factory, error handlers, swagger route
│   ├── models.py                # Database models (User, Task, Comment)
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py            # Register, Login, Refresh, Password Reset, Me
│   │   └── utils.py             # JWT token generation, auth helpers
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── routes.py            # Task CRUD, pagination, filtering, assign, comments
│   │   └── schemas.py           # Marshmallow serialization schemas
│   ├── users/
│   │   ├── __init__.py
│   │   ├── routes.py            # User directory, profile updates, admin deletion
│   │   └── schemas.py           # User schemas
│   └── utils/
│       ├── validators.py        # Request payload validators
│       ├── decorators.py        # Pagination and role decorators
│       ├── responses.py         # Standardized JSON response utilities
│       └── extensions.py        # SQLAlchemy, JWT, Limiter, CORS, Migrate
├── tests/
│   ├── test_auth.py             # Tests for registration, login, refresh, reset
│   ├── test_tasks.py            # Tests for task CRUD, pagination, filters, search
│   └── test_users.py            # Tests for user profile & role permissions
├── docs/
│   ├── api.md                   # Full Markdown API documentation
│   ├── postman_collection.json  # Postman v2.1 collection
│   └── swagger.yaml             # OpenAPI 3.0 specification
├── config.py                    # Environment and app configuration
├── requirements.txt             # Project dependencies
├── run.py                       # CLI entry point and server startup
├── .env.example                 # Sample environment variables
├── .gitignore                   # Git ignore file
└── README.md                    # Project documentation
```

---

## ⚙️ Installation & Setup

### 1. Clone repository & setup virtual environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration values:
- `FLASK_CONFIG`: `development`, `testing`, or `production`
- `SECRET_KEY`: Application secret key
- `JWT_SECRET_KEY`: Key used for signing JWT tokens
- `DEV_DATABASE_URL`: `sqlite:///task_management_dev.db`

### 4. Initialize Database
Initialize tables with the built-in CLI:
```bash
python run.py init-db
```
Seed demo user and sample tasks:
```bash
python run.py seed-db
```
*Default Seed Credentials:*
- User: `john_doe` / `SecurePass123`
- Admin: `admin_user` / `AdminSecurePass123`

---

## 🏃 Running the Application

Start the development server:
```bash
python run.py
```
The server starts at `http://localhost:5000`.

---

## 📖 Interactive Documentation

Once the server is running, navigate to:
```
http://localhost:5000/api/docs
```
to access the interactive Swagger UI.

---

## 🧪 Running Unit Tests

Run the full automated test suite using `pytest`:
```bash
python -m pytest -v
```

---

## 📬 Sample API Endpoints & Responses

### 1. User Registration
`POST /api/auth/register`
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123"
}
```
**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "message": "User registered successfully",
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "created_at": "2024-01-25T10:30:00Z"
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni..."
  }
}
```

### 2. Task Listing with Pagination and Filters
`GET /api/tasks?page=1&per_page=10&status=in_progress&priority=high`
```http
Authorization: Bearer <access_token>
```
**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "tasks": [
      {
        "id": 1,
        "title": "Complete API project",
        "description": "Finish task management API",
        "status": "in_progress",
        "priority": "high",
        "due_date": "2024-02-15",
        "created_at": "2024-01-25T10:30:00Z",
        "updated_at": "2024-01-25T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "per_page": 10,
      "total_pages": 5,
      "total_items": 48,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

### 3. Error Responses
**400 Bad Request (Validation failure):**
```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": {
    "title": ["Title is required", "Title must be at least 3 characters"],
    "priority": ["Priority must be one of: low, medium, high"]
  }
}
```
**401 Unauthorized:**
```json
{
  "status": "error",
  "message": "Missing or invalid token"
}
```
**404 Not Found:**
```json
{
  "status": "error",
  "message": "Task not found"
}
```

