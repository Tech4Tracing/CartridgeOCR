from marshmallow import Schema, fields


class DemoParameter(Schema):
    gist_id = fields.Int()


class CollectionCreateSchema(Schema):
    name = fields.Str()


class CollectionDisplaySchema(Schema):
    id = fields.Str()
    created_at = fields.Str()
    name = fields.Str()

    def dump(self, *args, **kwargs):
        result = super().dump(*args, **kwargs)
        if result.get("created_at"):
            if isinstance(result["created_at"], str) and result["created_at"].endswith(" +00:00"):
                # strip that space
                result["created_at"] = result["created_at"].rstrip(" +00:00") + "Z"
        return result


class CollectionsListSchema(Schema):
    total = fields.Int()
    collections = fields.List(fields.Nested(CollectionDisplaySchema))


class ImageDisplaySchema(Schema):
    id = fields.Str()
    created_at = fields.Str()
    collection_id = fields.Str()
    mimetype = fields.Str()
    size = fields.Int()
    extra_data = fields.Dict()


class ImageListSchema(Schema):
    total = fields.Int()
    images = fields.List(fields.Nested(ImageDisplaySchema))


class AnnotationDisplaySchema(Schema):
    id = fields.Str()
    created_at = fields.Str()
    image_id = fields.Str()
    geometry = fields.Str()
    annotation = fields.Str()
    metadata_ = fields.Str()


class AnnotationListSchema(Schema):
    total = fields.Int()
    annotations = fields.List(fields.Nested(AnnotationDisplaySchema))


class UserDisplaySchema(Schema):
    id = fields.Str()
    provider_id = fields.Str()

    name = fields.Str()
    email = fields.Str()
    profile_pic = fields.Str()
    is_active = fields.Boolean()
    is_superuser = fields.Boolean()


class UserCreateSchema(Schema):
    name = fields.Str()
    email = fields.Str()
    is_active = fields.Boolean()
    is_superuser = fields.Boolean()


class UserListSchema(Schema):
    total = fields.Int()
    objects = fields.List(fields.Nested(UserDisplaySchema))


class ErrorSchema(Schema):
    status = fields.Int()
    title = fields.Str()
    detail = fields.Str()


class Errors(Schema):
    errors = fields.List(fields.Nested(ErrorSchema))
