# Task Management REST API Documentation

Comprehensive documentation for the Task Management REST API built with Flask, Flask-RESTful, SQLAlchemy, and JWT.

## Table of Contents
1. [Overview & Base URL](#overview--base-url)
2. [Authentication & Authorization](#authentication--authorization)
3. [Error Handling & Status Codes](#error-handling--status-codes)
4. [Rate Limiting](#rate-limiting)
5. [Endpoints](#endpoints)
   - [Authentication Endpoints](#authentication-endpoints)
     - `POST /api/auth/register`
     - `POST /api/auth/login`
     - `POST /api/auth/refresh`
     - `POST /api/auth/reset-password-request`
     - `POST /api/auth/reset-password`
     - `GET /api/auth/me`
   - [Task Endpoints](#task-endpoints)
     - `GET /api/tasks` (with Pagination, Filtering, Sorting & Search)
     - `POST /api/tasks`
     - `GET /api/tasks/{task_id}`
     - `PUT /api/tasks/{task_id}`
     - `DELETE /api/tasks/{task_id}`
     - `POST /api/tasks/{task_id}/assign`
     - `GET /api/tasks/{task_id}/comments`
     - `POST /api/tasks/{task_id}/comments`
   - [User Endpoints](#user-endpoints)
     - `GET /api/users`
     - `GET /api/users/{user_id}`
     - `PUT /api/users/{user_id}`
     - `DELETE /api/users/{user_id}`
6. [Interactive Swagger UI](#interactive-swagger-ui)

---

## Overview & Base URL

- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`
- **Response Format**: All endpoints return standard JSON responses adhering to:
  ```json
  {
    "status": "success",
    "data": { ... }
  }
  ```
  or for error responses:
  ```json
  {
    "status": "error",
    "message": "Error description",
    "errors": { ... } // optional validation errors
  }
  ```

---

## Authentication & Authorization

Protected endpoints require a JWT Bearer token in the `Authorization` HTTP header:
```http
Authorization: Bearer <access_token>
```

Tokens are obtained by logging in (`POST /api/auth/login`) or registering (`POST /api/auth/register`).

---

## Error Handling & Status Codes

| Status Code | Description | Example Condition |
|-------------|-------------|-------------------|
| `200 OK` | Request succeeded | Fetching tasks, profile |
| `201 Created` | Resource created | Registered user, task created |
| `400 Bad Request` | Validation failure or malformed payload | Missing title, invalid email |
| `401 Unauthorized` | Missing, expired, or invalid token | Accessing protected route without token |
| `403 Forbidden` | Access denied | Non-admin attempting to delete another user |
| `404 Not Found` | Resource not found | Task ID does not exist |
| `405 Method Not Allowed` | Invalid HTTP method | Calling POST on a GET-only route |
| `429 Too Many Requests` | Rate limit exceeded | Exceeding request quota |
| `500 Internal Server Error` | Unexpected server error | Uncaught server exception |

---

## Rate Limiting

The API employs rate limiting via `Flask-Limiter` with default limits of:
- `200 requests per day`
- `50 requests per hour`

When the limit is reached, a `429 Too Many Requests` response is returned.

---

## Endpoints

### Authentication Endpoints

#### 1. Register User
`POST /api/auth/register`

Registers a new user account.

**Request Body:**
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
      "role": "user",
      "created_at": "2024-01-25T10:30:00Z",
      "updated_at": "2024-01-25T10:30:00Z"
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni..."
  }
}
```

---

#### 2. User Login
`POST /api/auth/login`

Authenticates a user and issues access and refresh tokens.

**Request Body:**
```json
{
  "username": "john_doe",
  "password": "SecurePass123"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Login successful",
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user",
      "created_at": "2024-01-25T10:30:00Z",
      "updated_at": "2024-01-25T10:30:00Z"
    },
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni..."
  }
}
```

---

#### 3. Refresh Access Token
`POST /api/auth/refresh`

Requires `Authorization: Bearer <refresh_token>`.

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1Ni..."
  }
}
```

---

#### 4. Password Reset Request
`POST /api/auth/reset-password-request`

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Password reset token generated successfully",
    "reset_token": "abc123xyz..."
  }
}
```

---

#### 5. Reset Password
`POST /api/auth/reset-password`

**Request Body:**
```json
{
  "token": "abc123xyz...",
  "new_password": "NewSecurePassword456"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Password has been reset successfully"
  }
}
```

---

#### 6. Get Current User Profile
`GET /api/auth/me`

Requires `Authorization: Bearer <access_token>`.

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "user": {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user",
      "created_at": "2024-01-25T10:30:00Z",
      "updated_at": "2024-01-25T10:30:00Z"
    }
  }
}
```

---

### Task Endpoints

#### 1. Get Paginated Tasks (with Filtering, Sorting & Search)
`GET /api/tasks`

Requires `Authorization: Bearer <access_token>`.

**Query Parameters:**
- `page` *(optional, integer, default: 1)*: Page number.
- `per_page` *(optional, integer, default: 10)*: Items per page.
- `status` *(optional, string)*: Filter by status (`pending`, `in_progress`, `completed`).
- `priority` *(optional, string)*: Filter by priority (`low`, `medium`, `high`).
- `category` *(optional, string)*: Filter by task category.
- `q` or `search` *(optional, string)*: Full-text search across task title and description.
- `sort_by` *(optional, string, default: created_at)*: Sort attribute (`created_at`, `due_date`, `title`, `priority`).
- `sort_order` *(optional, string, default: desc)*: Sort direction (`asc`, `desc`).

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
        "category": "development",
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

---

#### 2. Create Task
`POST /api/tasks`

Requires `Authorization: Bearer <access_token>`.

**Request Body:**
```json
{
  "title": "Complete API project",
  "description": "Finish task management API",
  "status": "in_progress",
  "priority": "high",
  "category": "development",
  "due_date": "2024-02-15",
  "assigned_to_id": 2
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "message": "Task created successfully",
    "task": {
      "id": 1,
      "title": "Complete API project",
      "description": "Finish task management API",
      "status": "in_progress",
      "priority": "high",
      "category": "development",
      "due_date": "2024-02-15",
      "created_at": "2024-01-25T10:30:00Z"
    }
  }
}
```

---

#### 3. Get Single Task
`GET /api/tasks/{task_id}`

Requires `Authorization: Bearer <access_token>`.

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "task": {
      "id": 1,
      "title": "Complete API project",
      "description": "Finish task management API",
      "status": "in_progress",
      "priority": "high",
      "category": "development",
      "due_date": "2024-02-15",
      "created_at": "2024-01-25T10:30:00Z",
      "updated_at": "2024-01-25T10:30:00Z",
      "user_id": 1,
      "assigned_to_id": 2,
      "comments": []
    }
  }
}
```

---

#### 4. Update Task
`PUT /api/tasks/{task_id}` or `PATCH /api/tasks/{task_id}`

Requires `Authorization: Bearer <access_token>`.

**Request Body:**
```json
{
  "title": "Complete API project with documentation",
  "status": "completed",
  "priority": "medium"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Task updated successfully",
    "task": {
      "id": 1,
      "title": "Complete API project with documentation",
      "description": "Finish task management API",
      "status": "completed",
      "priority": "medium",
      "category": "development",
      "due_date": "2024-02-15",
      "updated_at": "2024-01-25T11:00:00Z"
    }
  }
}
```

---

#### 5. Delete Task
`DELETE /api/tasks/{task_id}`

Requires `Authorization: Bearer <access_token>`.

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Task deleted successfully"
  }
}
```

---

#### 6. Assign Task
`POST /api/tasks/{task_id}/assign`

Requires `Authorization: Bearer <access_token>`.

**Request Body:**
```json
{
  "assigned_to_id": 2
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message": "Task assigned successfully",
    "task": { ... }
  }
}
```

---

#### 7. Add & List Task Comments
- `GET /api/tasks/{task_id}/comments`: Lists all comments on the task.
- `POST /api/tasks/{task_id}/comments`: Adds a comment to the task.

**Request Body (POST):**
```json
{
  "content": "This task is prioritized for sprint 1"
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "data": {
    "message": "Comment added successfully",
    "comment": {
      "id": 1,
      "content": "This task is prioritized for sprint 1",
      "task_id": 1,
      "user_id": 1,
      "username": "john_doe",
      "created_at": "2024-01-25T11:15:00Z"
    }
  }
}
```

---

### User Endpoints

#### 1. List Users
`GET /api/users`

Requires `Authorization: Bearer <access_token>`.
Query parameters: `q` or `search` to search users by username or email.

#### 2. Get User Details
`GET /api/users/{user_id}`

#### 3. Update User Profile
`PUT /api/users/{user_id}`

Allows users to update their own profile, or admins to update any user.

#### 4. Delete User (Admin Only)
`DELETE /api/users/{user_id}`

Requires admin role.

---

## Interactive Swagger UI

Open your browser to:
`http://localhost:5000/api/docs`
to explore and test the endpoints directly from the interactive OpenAPI documentation.

