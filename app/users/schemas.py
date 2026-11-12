from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    """Schema for serializing User objects."""
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    role = fields.Str(validate=validate.OneOf(['user', 'admin']), load_default='user')
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


user_schema = UserSchema()
users_schema = UserSchema(many=True)

