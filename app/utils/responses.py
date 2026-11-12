def success_response(data=None, status_code=200):
    """
    Generate a standardized success response dictionary and status code.
    Format:
    {
        "status": "success",
        "data": { ... }
    }
    """
    if data is None:
        payload = {}
    elif isinstance(data, dict) and 'status' in data and 'data' in data:
        return data, status_code
    else:
        payload = data

    response_body = {
        "status": "success",
        "data": payload
    }
    return response_body, status_code


def error_response(message_or_errors, status_code=400, errors=None):
    """
    Generate a standardized error response dictionary and status code.
    Supports:
      - error_response('Task not found', 404)
      - error_response({'title': ['Title is required']}, 400)
      - error_response('Validation failed', 400, errors={'title': [...]})
    """
    if isinstance(message_or_errors, dict):
        response_body = {
            "status": "error",
            "message": "Validation failed",
            "errors": message_or_errors
        }
    else:
        response_body = {
            "status": "error",
            "message": str(message_or_errors)
        }
        if errors:
            response_body["errors"] = errors

    return response_body, status_code
