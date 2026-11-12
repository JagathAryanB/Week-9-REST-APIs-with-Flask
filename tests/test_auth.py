import pytest
from app import create_app, db
from app.models import User


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_user_registration_success(client):
    payload = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    response = client.post('/api/auth/register', json=payload)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['data']['message'] == 'User registered successfully'
    assert json_data['data']['user']['username'] == 'john_doe'
    assert json_data['data']['user']['email'] == 'john@example.com'
    assert 'access_token' in json_data['data']
    assert 'refresh_token' in json_data['data']


def test_user_registration_validation_errors(client):
    payload = {
        "username": "ab",  # too short
        "email": "invalid-email",
        "password": "short"  # < 8 chars
    }
    response = client.post('/api/auth/register', json=payload)
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert json_data['message'] == 'Validation failed'
    assert 'username' in json_data['errors']
    assert 'email' in json_data['errors']
    assert 'password' in json_data['errors']


def test_user_registration_duplicate_username_and_email(client):
    payload = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    client.post('/api/auth/register', json=payload)

    # Duplicate username
    dup_username_payload = {
        "username": "john_doe",
        "email": "other@example.com",
        "password": "SecurePass123"
    }
    resp1 = client.post('/api/auth/register', json=dup_username_payload)
    assert resp1.status_code == 400
    assert 'username' in resp1.get_json()['errors']

    # Duplicate email
    dup_email_payload = {
        "username": "different_user",
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    resp2 = client.post('/api/auth/register', json=dup_email_payload)
    assert resp2.status_code == 400
    assert 'email' in resp2.get_json()['errors']


def test_user_login_success(client):
    reg_payload = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    client.post('/api/auth/register', json=reg_payload)

    login_payload = {
        "username": "john_doe",
        "password": "SecurePass123"
    }
    response = client.post('/api/auth/login', json=login_payload)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['data']['message'] == 'Login successful'
    assert 'access_token' in json_data['data']
    assert 'refresh_token' in json_data['data']


def test_user_login_invalid_credentials(client):
    login_payload = {
        "username": "non_existent",
        "password": "WrongPassword123"
    }
    response = client.post('/api/auth/login', json=login_payload)
    assert response.status_code == 401
    json_data = response.get_json()
    assert json_data['status'] == 'error'


def test_refresh_token(client):
    reg_payload = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    reg_res = client.post('/api/auth/register', json=reg_payload)
    refresh_token = reg_res.get_json()['data']['refresh_token']

    # Use refresh token to get new access token
    headers = {"Authorization": f"Bearer {refresh_token}"}
    response = client.post('/api/auth/refresh', headers=headers)
    assert response.status_code == 200
    assert 'access_token' in response.get_json()['data']


def test_password_reset_flow(client):
    reg_payload = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    client.post('/api/auth/register', json=reg_payload)

    # Request reset token
    req_res = client.post('/api/auth/reset-password-request', json={"email": "john@example.com"})
    assert req_res.status_code == 200
    reset_token = req_res.get_json()['data']['reset_token']

    # Reset password
    reset_res = client.post('/api/auth/reset-password', json={
        "token": reset_token,
        "new_password": "NewSecurePassword456"
    })
    assert reset_res.status_code == 200

    # Login with old password should fail
    fail_login = client.post('/api/auth/login', json={
        "username": "john_doe",
        "password": "SecurePass123"
    })
    assert fail_login.status_code == 401

    # Login with new password should succeed
    succ_login = client.post('/api/auth/login', json={
        "username": "john_doe",
        "password": "NewSecurePassword456"
    })
    assert succ_login.status_code == 200


def test_protected_me_endpoint(client):
    # Without token
    res1 = client.get('/api/auth/me')
    assert res1.status_code == 401
    assert res1.get_json()['status'] == 'error'
    assert res1.get_json()['message'] == 'Missing or invalid token'

    # With token
    reg_payload = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123"
    }
    reg_res = client.post('/api/auth/register', json=reg_payload)
    token = reg_res.get_json()['data']['access_token']

    res2 = client.get('/api/auth/me', headers={"Authorization": f"Bearer {token}"})
    assert res2.status_code == 200
    assert res2.get_json()['data']['user']['username'] == 'john_doe'

    # Test logout
    logout_res = client.post('/api/auth/logout', headers={"Authorization": f"Bearer {token}"})
    assert logout_res.status_code == 200
    assert logout_res.get_json()['data']['message'] == 'Successfully logged out'

