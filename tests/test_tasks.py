import pytest
from app import create_app, db
from app.models import User, Task


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


@pytest.fixture
def auth_headers(client):
    reg_payload = {
        "username": "task_owner",
        "email": "owner@example.com",
        "password": "Password123"
    }
    res = client.post('/api/auth/register', json=reg_payload)
    token = res.get_json()['data']['access_token']
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user(client):
    reg_payload = {
        "username": "second_user",
        "email": "second@example.com",
        "password": "Password123"
    }
    res = client.post('/api/auth/register', json=reg_payload)
    return res.get_json()['data']


def test_create_task_success(client, auth_headers):
    payload = {
        "title": "Complete API project",
        "description": "Finish task management API",
        "status": "in_progress",
        "priority": "high",
        "category": "development",
        "due_date": "2024-02-15"
    }
    response = client.post('/api/tasks', json=payload, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['data']['message'] == 'Task created successfully'
    task = json_data['data']['task']
    assert task['title'] == 'Complete API project'
    assert task['status'] == 'in_progress'
    assert task['priority'] == 'high'
    assert task['due_date'] == '2024-02-15'


def test_create_task_validation_error(client, auth_headers):
    payload = {
        "title": "ab",  # too short
        "status": "not_a_valid_status",
        "priority": "ultra_high"
    }
    response = client.post('/api/tasks', json=payload, headers=auth_headers)
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert json_data['message'] == 'Validation failed'
    assert 'title' in json_data['errors']
    assert 'status' in json_data['errors']
    assert 'priority' in json_data['errors']


def test_get_tasks_with_pagination(client, auth_headers):
    # Create 15 tasks
    for i in range(1, 16):
        client.post('/api/tasks', json={
            "title": f"Task Number {i:02d}",
            "description": f"Description for task {i}",
            "priority": "medium",
            "status": "pending"
        }, headers=auth_headers)

    # Page 1 (per_page=10)
    res_p1 = client.get('/api/tasks?page=1&per_page=10', headers=auth_headers)
    assert res_p1.status_code == 200
    data_p1 = res_p1.get_json()['data']
    assert len(data_p1['tasks']) == 10
    pagination = data_p1['pagination']
    assert pagination['page'] == 1
    assert pagination['per_page'] == 10
    assert pagination['total_items'] == 15
    assert pagination['total_pages'] == 2
    assert pagination['has_next'] is True
    assert pagination['has_prev'] is False

    # Page 2
    res_p2 = client.get('/api/tasks?page=2&per_page=10', headers=auth_headers)
    assert res_p2.status_code == 200
    data_p2 = res_p2.get_json()['data']
    assert len(data_p2['tasks']) == 5
    assert data_p2['pagination']['has_next'] is False
    assert data_p2['pagination']['has_prev'] is True


def test_get_tasks_filtering_and_searching(client, auth_headers):
    client.post('/api/tasks', json={
        "title": "Write documentation",
        "description": "Write API markdown docs",
        "status": "completed",
        "priority": "low",
        "category": "docs"
    }, headers=auth_headers)

    client.post('/api/tasks', json={
        "title": "Build authentication",
        "description": "Implement JWT endpoints",
        "status": "in_progress",
        "priority": "high",
        "category": "backend"
    }, headers=auth_headers)

    client.post('/api/tasks', json={
        "title": "Database migrations",
        "description": "Set up Alembic migrations",
        "status": "pending",
        "priority": "high",
        "category": "backend"
    }, headers=auth_headers)

    # Filter by status
    res_status = client.get('/api/tasks?status=completed', headers=auth_headers)
    assert len(res_status.get_json()['data']['tasks']) == 1
    assert res_status.get_json()['data']['tasks'][0]['title'] == "Write documentation"

    # Filter by priority
    res_priority = client.get('/api/tasks?priority=high', headers=auth_headers)
    assert len(res_priority.get_json()['data']['tasks']) == 2

    # Filter by category
    res_category = client.get('/api/tasks?category=docs', headers=auth_headers)
    assert len(res_category.get_json()['data']['tasks']) == 1

    # Search keyword
    res_search = client.get('/api/tasks?q=JWT', headers=auth_headers)
    assert len(res_search.get_json()['data']['tasks']) == 1
    assert res_search.get_json()['data']['tasks'][0]['title'] == "Build authentication"

    # Search dedicated endpoint
    res_search2 = client.get('/api/tasks/search?search=migrations', headers=auth_headers)
    assert res_search2.status_code == 200
    assert len(res_search2.get_json()['data']['tasks']) == 1
    assert res_search2.get_json()['data']['tasks'][0]['title'] == "Database migrations"


def test_get_single_task_and_not_found(client, auth_headers):
    create_res = client.post('/api/tasks', json={
        "title": "Single Task Verification",
        "description": "Testing single task endpoint"
    }, headers=auth_headers)
    task_id = create_res.get_json()['data']['task']['id']

    # Get single task
    res = client.get(f'/api/tasks/{task_id}', headers=auth_headers)
    assert res.status_code == 200
    assert res.get_json()['data']['task']['title'] == "Single Task Verification"

    # 404 for non-existent task
    res_404 = client.get('/api/tasks/99999', headers=auth_headers)
    assert res_404.status_code == 404
    assert res_404.get_json()['status'] == 'error'
    assert res_404.get_json()['message'] == 'Task not found'


def test_update_task(client, auth_headers):
    create_res = client.post('/api/tasks', json={
        "title": "Original Title",
        "description": "Original Description",
        "status": "pending",
        "priority": "low"
    }, headers=auth_headers)
    task_id = create_res.get_json()['data']['task']['id']

    # Update task
    update_payload = {
        "title": "Updated Title",
        "status": "completed",
        "priority": "high"
    }
    res_put = client.put(f'/api/tasks/{task_id}', json=update_payload, headers=auth_headers)
    assert res_put.status_code == 200
    task_data = res_put.get_json()['data']['task']
    assert task_data['title'] == "Updated Title"
    assert task_data['status'] == "completed"
    assert task_data['priority'] == "high"


def test_delete_task(client, auth_headers):
    create_res = client.post('/api/tasks', json={
        "title": "Task to delete",
        "description": "Will be deleted"
    }, headers=auth_headers)
    task_id = create_res.get_json()['data']['task']['id']

    # Delete task
    res_del = client.delete(f'/api/tasks/{task_id}', headers=auth_headers)
    assert res_del.status_code == 200
    assert res_del.get_json()['data']['message'] == 'Task deleted successfully'

    # Verify 404 after deletion
    res_verify = client.get(f'/api/tasks/{task_id}', headers=auth_headers)
    assert res_verify.status_code == 404


def test_task_assignment_and_comments(client, auth_headers, second_user):
    create_res = client.post('/api/tasks', json={
        "title": "Team Task Assignment",
        "description": "Assign to second user"
    }, headers=auth_headers)
    task_id = create_res.get_json()['data']['task']['id']

    # Assign to second user
    assign_res = client.post(f'/api/tasks/{task_id}/assign', json={
        "assigned_to_id": second_user['user']['id']
    }, headers=auth_headers)
    assert assign_res.status_code == 200
    assert assign_res.get_json()['data']['task']['assigned_to_id'] == second_user['user']['id']

    # Add comment to task
    comment_res = client.post(f'/api/tasks/{task_id}/comments', json={
        "content": "This task is prioritized for sprint 1"
    }, headers=auth_headers)
    assert comment_res.status_code == 201
    assert comment_res.get_json()['data']['comment']['content'] == "This task is prioritized for sprint 1"

    # Fetch comments
    list_comments = client.get(f'/api/tasks/{task_id}/comments', headers=auth_headers)
    assert list_comments.status_code == 200
    assert len(list_comments.get_json()['data']['comments']) == 1

