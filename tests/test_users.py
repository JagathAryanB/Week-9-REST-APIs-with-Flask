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


def test_user_endpoints_and_permissions(client):
    # Register regular user
    u1_res = client.post('/api/auth/register', json={
        "username": "regular_user",
        "email": "regular@example.com",
        "password": "Password123"
    })
    u1_token = u1_res.get_json()['data']['access_token']
    u1_id = u1_res.get_json()['data']['user']['id']

    # Register admin user
    u2_res = client.post('/api/auth/register', json={
        "username": "admin_user",
        "email": "admin@example.com",
        "password": "Password123",
        "role": "admin"
    })
    admin_token = u2_res.get_json()['data']['access_token']
    admin_id = u2_res.get_json()['data']['user']['id']

    # List users
    res_list = client.get('/api/users', headers={"Authorization": f"Bearer {u1_token}"})
    assert res_list.status_code == 200
    assert len(res_list.get_json()['data']['users']) == 2

    # Get single user
    res_get = client.get(f'/api/users/{u1_id}', headers={"Authorization": f"Bearer {u1_token}"})
    assert res_get.status_code == 200
    assert res_get.get_json()['data']['user']['username'] == "regular_user"

    # Update own profile
    res_update = client.put(f'/api/users/{u1_id}', json={
        "email": "updated_regular@example.com"
    }, headers={"Authorization": f"Bearer {u1_token}"})
    assert res_update.status_code == 200
    assert res_update.get_json()['data']['user']['email'] == "updated_regular@example.com"

    # Regular user attempting to change another user's profile -> 403
    res_forbidden = client.put(f'/api/users/{admin_id}', json={
        "email": "hacked@example.com"
    }, headers={"Authorization": f"Bearer {u1_token}"})
    assert res_forbidden.status_code == 403

    # Regular user attempting to delete another user -> 403
    res_del_forbidden = client.delete(f'/api/users/{admin_id}', headers={"Authorization": f"Bearer {u1_token}"})
    assert res_del_forbidden.status_code == 403

    # Admin deleting regular user -> 200
    res_admin_del = client.delete(f'/api/users/{u1_id}', headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin_del.status_code == 200
    assert res_admin_del.get_json()['data']['message'] == 'User deleted successfully'

