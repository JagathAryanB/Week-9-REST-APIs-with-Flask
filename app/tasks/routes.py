from datetime import datetime, timezone
from flask import Blueprint, request
from flask_restful import Api, Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.extensions import db
from app.models import Task, User, Comment
from app.utils.validators import validate_task_data, validate_comment_data
from app.utils.responses import success_response, error_response

tasks_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')
tasks_api = Api(tasks_bp)


def parse_date(date_str):
    """Helper to parse date string into datetime object."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    except (ValueError, TypeError):
        return None


class TaskListResource(Resource):
    """Resource for listing and creating tasks"""

    @jwt_required()
    def get(self):
        """Get list of tasks with pagination and filtering"""
        current_user_id = int(get_jwt_identity())

        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        status = request.args.get('status')
        priority = request.args.get('priority')
        category = request.args.get('category')
        search_query = request.args.get('search') or request.args.get('q')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        # Build query - user can view tasks they own or tasks assigned to them
        query = Task.query.filter(
            (Task.user_id == current_user_id) | (Task.assigned_to_id == current_user_id)
        )

        # Apply filters
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        if category:
            query = query.filter(Task.category == category)
        if search_query:
            pattern = f"%{search_query}%"
            query = query.filter(
                (Task.title.ilike(pattern)) | (Task.description.ilike(pattern))
            )

        # Apply sorting
        if hasattr(Task, sort_by):
            column = getattr(Task, sort_by)
            if sort_order == 'desc':
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
        else:
            query = query.order_by(Task.created_at.desc())

        # Paginate results
        paginated_tasks = query.paginate(page=page, per_page=per_page, error_out=False)

        # Prepare response
        tasks_data = [{
            'id': task.id,
            'title': task.title,
            'description': task.description or '',
            'status': task.status,
            'priority': task.priority,
            'category': task.category,
            'due_date': task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
            'created_at': task.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if task.created_at else None,
            'updated_at': task.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if task.updated_at else None
        } for task in paginated_tasks.items]

        return success_response({
            'tasks': tasks_data,
            'pagination': {
                'page': paginated_tasks.page,
                'per_page': paginated_tasks.per_page,
                'total_pages': paginated_tasks.pages,
                'total_items': paginated_tasks.total,
                'has_next': paginated_tasks.has_next,
                'has_prev': paginated_tasks.has_prev
            }
        })

    @jwt_required()
    def post(self):
        """Create a new task"""
        current_user_id = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}

        # Validate input data
        validation_result = validate_task_data(data)
        if not validation_result['valid']:
            return error_response(validation_result['errors'], 400)

        # Parse due_date if provided
        due_date = parse_date(data.get('due_date')) if data.get('due_date') else None

        # Verify assigned user if provided
        assigned_to_id = data.get('assigned_to_id')
        if assigned_to_id is not None:
            assignee = db.session.get(User, assigned_to_id)
            if not assignee:
                return error_response({'assigned_to_id': ['Assigned user does not exist']}, 400)

        # Create new task
        task = Task(
            title=data['title'].strip(),
            description=data.get('description', ''),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium'),
            category=data.get('category', 'general'),
            due_date=due_date,
            user_id=current_user_id,
            assigned_to_id=assigned_to_id
        )

        db.session.add(task)
        db.session.commit()

        return success_response({
            'message': 'Task created successfully',
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'category': task.category,
                'due_date': task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
                'created_at': task.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if task.created_at else None
            }
        }, 201)


class TaskResource(Resource):
    """Resource for single task operations"""

    @jwt_required()
    def get(self, task_id):
        """Get a specific task"""
        current_user_id = int(get_jwt_identity())

        task = Task.query.filter(
            (Task.id == task_id) &
            ((Task.user_id == current_user_id) | (Task.assigned_to_id == current_user_id))
        ).first()

        if not task:
            return error_response('Task not found', 404)

        return success_response({
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'category': task.category,
                'due_date': task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
                'created_at': task.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if task.created_at else None,
                'updated_at': task.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if task.updated_at else None,
                'user_id': task.user_id,
                'assigned_to_id': task.assigned_to_id,
                'comments': [c.to_dict() for c in task.comments.all()]
            }
        })

    @jwt_required()
    def put(self, task_id):
        """Update a task"""
        return self._update_task(task_id)

    @jwt_required()
    def patch(self, task_id):
        """Partially update a task"""
        return self._update_task(task_id)

    def _update_task(self, task_id):
        current_user_id = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}

        task = Task.query.filter(
            (Task.id == task_id) &
            ((Task.user_id == current_user_id) | (Task.assigned_to_id == current_user_id))
        ).first()

        if not task:
            return error_response('Task not found', 404)

        # Validate update data
        validation_result = validate_task_data(data, update=True)
        if not validation_result['valid']:
            return error_response(validation_result['errors'], 400)

        # Update task fields
        if 'title' in data:
            task.title = data['title'].strip()
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
        if 'priority' in data:
            task.priority = data['priority']
        if 'category' in data:
            task.category = data['category']
        if 'due_date' in data:
            task.due_date = parse_date(data['due_date']) if data['due_date'] else None
        if 'assigned_to_id' in data:
            assignee_id = data['assigned_to_id']
            if assignee_id is not None:
                if not User.query.get(assignee_id):
                    return error_response({'assigned_to_id': ['User does not exist']}, 400)
            task.assigned_to_id = assignee_id

        db.session.commit()

        return success_response({
            'message': 'Task updated successfully',
            'task': {
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'category': task.category,
                'due_date': task.due_date.strftime("%Y-%m-%d") if task.due_date else None,
                'updated_at': task.updated_at.strftime("%Y-%m-%dT%H:%M:%SZ") if task.updated_at else None
            }
        })

    @jwt_required()
    def delete(self, task_id):
        """Delete a task"""
        current_user_id = int(get_jwt_identity())

        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()

        if not task:
            return error_response('Task not found', 404)

        db.session.delete(task)
        db.session.commit()

        return success_response({'message': 'Task deleted successfully'})


class TaskAssignResource(Resource):
    """Resource for assigning tasks to users (Advanced Feature)."""

    @jwt_required()
    def post(self, task_id):
        current_user_id = int(get_jwt_identity())
        task = Task.query.filter_by(id=task_id, user_id=current_user_id).first()
        if not task:
            return error_response('Task not found or you are not authorized to assign it', 404)

        data = request.get_json(silent=True) or {}
        assigned_to_id = data.get('assigned_to_id')

        if assigned_to_id is not None:
            assignee = db.session.get(User, assigned_to_id)
            if not assignee:
                return error_response({'assigned_to_id': ['Assignee user does not exist']}, 400)

        task.assigned_to_id = assigned_to_id
        db.session.commit()

        return success_response({
            'message': 'Task assigned successfully',
            'task': task.to_dict()
        })


class TaskCommentResource(Resource):
    """Resource for task comments (Advanced Feature)."""

    @jwt_required()
    def get(self, task_id):
        current_user_id = int(get_jwt_identity())
        task = Task.query.filter(
            (Task.id == task_id) &
            ((Task.user_id == current_user_id) | (Task.assigned_to_id == current_user_id))
        ).first()

        if not task:
            return error_response('Task not found', 404)

        comments = [c.to_dict() for c in task.comments.order_by(Comment.created_at.asc())]
        return success_response({'comments': comments})

    @jwt_required()
    def post(self, task_id):
        current_user_id = int(get_jwt_identity())
        task = Task.query.filter(
            (Task.id == task_id) &
            ((Task.user_id == current_user_id) | (Task.assigned_to_id == current_user_id))
        ).first()

        if not task:
            return error_response('Task not found', 404)

        data = request.get_json(silent=True) or {}
        validation = validate_comment_data(data)
        if not validation['valid']:
            return error_response(validation['errors'], 400)

        comment = Comment(
            content=data['content'].strip(),
            task_id=task.id,
            user_id=current_user_id
        )
        db.session.add(comment)
        db.session.commit()

        return success_response({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }, 201)


class TaskSearchResource(Resource):
    """Resource to search tasks across fields."""

    @jwt_required()
    def get(self):
        current_user_id = int(get_jwt_identity())
        search_query = request.args.get('search') or request.args.get('q') or ''
        status = request.args.get('status')
        priority = request.args.get('priority')
        category = request.args.get('category')

        query = Task.query.filter(
            (Task.user_id == current_user_id) | (Task.assigned_to_id == current_user_id)
        )
        if search_query:
            pattern = f"%{search_query}%"
            query = query.filter((Task.title.ilike(pattern)) | (Task.description.ilike(pattern)))
        if status:
            query = query.filter(Task.status == status)
        if priority:
            query = query.filter(Task.priority == priority)
        if category:
            query = query.filter(Task.category == category)

        tasks = query.order_by(Task.created_at.desc()).all()
        return success_response({
            'tasks': [t.to_dict() for t in tasks],
            'total_matches': len(tasks)
        })


tasks_api.add_resource(TaskListResource, '')
tasks_api.add_resource(TaskSearchResource, '/search')
tasks_api.add_resource(TaskResource, '/<int:task_id>')
tasks_api.add_resource(TaskAssignResource, '/<int:task_id>/assign')
tasks_api.add_resource(TaskCommentResource, '/<int:task_id>/comments')
