from marshmallow import Schema, fields, validate

VALID_STATUSES = ['pending', 'in_progress', 'completed']
VALID_PRIORITIES = ['low', 'medium', 'high']


class TaskSchema(Schema):
    """Schema for serializing and validating Task models."""
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    description = fields.Str(allow_none=True, load_default='')
    status = fields.Str(validate=validate.OneOf(VALID_STATUSES), load_default='pending')
    priority = fields.Str(validate=validate.OneOf(VALID_PRIORITIES), load_default='medium')
    category = fields.Str(validate=validate.Length(max=50), load_default='general')
    due_date = fields.DateTime(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    user_id = fields.Int(dump_only=True)
    assigned_to_id = fields.Int(allow_none=True)


class CommentSchema(Schema):
    """Schema for serializing and validating Comment models."""
    id = fields.Int(dump_only=True)
    content = fields.Str(required=True, validate=validate.Length(min=1, max=1000))
    task_id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    username = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)


task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)
comment_schema = CommentSchema()
comments_schema = CommentSchema(many=True)

