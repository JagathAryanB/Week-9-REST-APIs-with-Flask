import re
from datetime import datetime
from email_validator import validate_email, EmailNotValidError


VALID_STATUSES = ['pending', 'in_progress', 'completed']
VALID_PRIORITIES = ['low', 'medium', 'high']


def validate_task_data(data, update=False):
    """
    Validates task payload for creation and updates.
    Returns:
      dict: {'valid': bool, 'errors': dict[str, list[str]]}
    """
    errors = {}

    if not isinstance(data, dict):
        return {
            'valid': False,
            'errors': {'general': ['Request body must be a valid JSON object']}
        }

    # Validate Title
    if not update or 'title' in data:
        title = data.get('title')
        title_errors = []
        if title is None or str(title).strip() == '':
            title_errors.append("Title is required")
        else:
            if not isinstance(title, str):
                title_errors.append("Title must be a string")
            else:
                stripped = title.strip()
                if len(stripped) < 3:
                    title_errors.append("Title must be at least 3 characters")
                if len(stripped) > 100:
                    title_errors.append("Title cannot exceed 100 characters")
        if title_errors:
            errors['title'] = title_errors

    # Validate Status
    if 'status' in data:
        status = data.get('status')
        if status not in VALID_STATUSES:
            errors['status'] = [f"Status must be one of: {', '.join(VALID_STATUSES)}"]

    # Validate Priority
    if 'priority' in data:
        priority = data.get('priority')
        if priority not in VALID_PRIORITIES:
            errors['priority'] = [f"Priority must be one of: {', '.join(VALID_PRIORITIES)}"]

    # Validate Due Date
    if 'due_date' in data and data.get('due_date') is not None:
        due_date_str = data.get('due_date')
        if isinstance(due_date_str, str):
            parsed = False
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
                try:
                    datetime.strptime(due_date_str, fmt)
                    parsed = True
                    break
                except ValueError:
                    continue
            if not parsed:
                try:
                    datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                    parsed = True
                except (ValueError, TypeError):
                    pass
            if not parsed:
                errors['due_date'] = ["Due date must be in valid ISO format (e.g. YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)"]
        else:
            errors['due_date'] = ["Due date must be a string in ISO format or null"]

    # Validate Description
    if 'description' in data and data.get('description') is not None:
        if not isinstance(data.get('description'), str):
            errors['description'] = ["Description must be a string"]

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def validate_user_registration(data):
    """
    Validates user registration payload.
    """
    errors = {}

    if not isinstance(data, dict):
        return {
            'valid': False,
            'errors': {'general': ['Request body must be a valid JSON object']}
        }

    # Username validation
    username = data.get('username')
    username_errors = []
    if not username or str(username).strip() == '':
        username_errors.append("Username is required")
    else:
        if not isinstance(username, str):
            username_errors.append("Username must be a string")
        else:
            u = username.strip()
            if len(u) < 3 or len(u) > 50:
                username_errors.append("Username must be between 3 and 50 characters")
            if not re.match(r'^[a-zA-Z0-9_.-]+$', u):
                username_errors.append("Username can only contain letters, numbers, underscores, dashes, and periods")
    if username_errors:
        errors['username'] = username_errors

    # Email validation
    email = data.get('email')
    email_errors = []
    if not email or str(email).strip() == '':
        email_errors.append("Email is required")
    else:
        try:
            validate_email(email, check_deliverability=False)
        except EmailNotValidError as e:
            email_errors.append(str(e))
    if email_errors:
        errors['email'] = email_errors

    # Password validation
    password = data.get('password')
    password_errors = []
    if not password:
        password_errors.append("Password is required")
    else:
        if len(password) < 8:
            password_errors.append("Password must be at least 8 characters long")
    if password_errors:
        errors['password'] = password_errors

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def validate_user_login(data):
    """
    Validates login payload.
    """
    errors = {}

    if not isinstance(data, dict):
        return {
            'valid': False,
            'errors': {'general': ['Request body must be a valid JSON object']}
        }

    identifier = data.get('username') or data.get('email')
    if not identifier:
        errors['username'] = ["Username or email is required"]

    if not data.get('password'):
        errors['password'] = ["Password is required"]

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def validate_comment_data(data):
    """
    Validates task comment payload.
    """
    errors = {}
    if not isinstance(data, dict):
        return {
            'valid': False,
            'errors': {'general': ['Request body must be a valid JSON object']}
        }

    content = data.get('content')
    if not content or str(content).strip() == '':
        errors['content'] = ["Comment content is required"]
    elif len(str(content).strip()) > 1000:
        errors['content'] = ["Comment content cannot exceed 1000 characters"]

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

