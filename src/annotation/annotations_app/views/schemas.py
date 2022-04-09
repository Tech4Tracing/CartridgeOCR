from marshmallow import Schema, fields


class DemoParameter(Schema):
    gist_id = fields.Int()


class CollectionCreateSchema(Schema):
    name = fields.Str()


class CollectionDisplaySchema(Schema):
    id = fields.Str()
    # created_at = fields.DateTime()
    name = fields.Str()


class CollectionsListSchema(Schema):
    total = fields.Int()
    collections = fields.List(fields.Nested(CollectionDisplaySchema))


class ImageDisplaySchema(Schema):
    id = fields.Str()
    # created_at = fields.DateTime()
    mimetype = fields.Str()
    size = fields.Int()
    extra_data = fields.Dict()
    collections = fields.List(fields.Str())
    storageKey = fields.Str()


class ImageListSchema(Schema):
    total = fields.Int()
    images = fields.List(fields.Nested(ImageDisplaySchema))


class AnnotationDisplaySchema(Schema):
    anno_id = fields.Str()
    img_id = fields.Str()
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


class UserListSchema(Schema):
    total = fields.Int()
    objects = fields.List(fields.Nested(UserDisplaySchema))


class ErrorSchema(Schema):
    status = fields.Int()
    title = fields.Str()
    detail = fields.Str()


class Errors(Schema):
    errors = fields.List(fields.Nested(ErrorSchema))
