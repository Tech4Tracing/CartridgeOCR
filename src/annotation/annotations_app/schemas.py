import json
import logging

from marshmallow import Schema, fields, pre_load, post_load, pre_dump


class DemoParameter(Schema):
    gist_id = fields.Int()


class CollectionCreateSchema(Schema):
    name = fields.Str()


class CollectionDisplaySchema(Schema):
    id = fields.Str()
    created_at = fields.Str()
    name = fields.Str()
    images_count = fields.Int()
    annotations_count = fields.Int()

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


class AnnotationDisplaySchema(Schema):
    id = fields.Str()
    created_at = fields.Str()
    image_id = fields.Str()
    geometry = fields.Str()
    annotation = fields.Str()
    metadata_ = fields.Str()

    def dump(self, *args, **kwargs):
        result = super().dump(*args, **kwargs)
        if result.get("metadata_"):
            # new way of returining metadata, keeping backwards compatibility
            try:
                result["metadata"] = json.loads(result["metadata_"])
            except Exception as e:
                logging.exception(e)
                result["metadata"] = {}
        else:
            result["metadata"] = {}
        if result.get("created_at"):
            if isinstance(result["created_at"], str) and result["created_at"].endswith(" +00:00"):
                # strip that space
                result["created_at"] = result["created_at"].rstrip(" +00:00") + "Z"
        return result


class HeadstampPredictionDisplaySchema(Schema):
    id = fields.Str()
    created_at = fields.Str()
    image_id = fields.Str()
    casing_box = fields.Str()
    casing_confidence = fields.Float()
    primer_box = fields.Str()
    primer_confidence = fields.Float()
    
    def dump(self, *args, **kwargs):
        result = super().dump(*args, **kwargs)
        if result.get("created_at"):
            if isinstance(result["created_at"], str) and result["created_at"].endswith(" +00:00"):
                # strip that space
                result["created_at"] = result["created_at"].rstrip(" +00:00") + "Z"
        return result


class ImageDisplaySchema(Schema):
    id = fields.Str()
    created_at = fields.Str()
    collection_id = fields.Str()
    mimetype = fields.Str()
    size = fields.Int()
    extra_data = fields.Str()
    prediction_status = fields.Str()
    # Helpful but noisy
    annotations = fields.List(fields.Nested(AnnotationDisplaySchema))
    predictions = fields.List(fields.Nested(HeadstampPredictionDisplaySchema))

    #@post_load
    #def deserialize_extra_data(self, data):
    #    """This will alter the data passed to ``load()`` before Marshmallow
    #    attempts deserialization.
    #    """
    #    print(f'deserialize_extra_data {dir(data)}')
    #    extra_data = data.extra_data
    #    data.extra_data = json.loads(extra_data)
    #    return data

    def dump(self, *args, **kwargs):
        result = super().dump(*args, **kwargs)
        print('dump', type(result))
        if result.get("extra_data"):
            result["extra_data"] = json.loads(result["extra_data"])
        if result.get("prediction_status"):
            result["prediction_status"] = json.loads(result["prediction_status"])
        return result

    #@pre_dump
    #def serialize_extra_data(self, data, many):
    #    """This will alter the data passed to ``dump()`` before Marshmallow
    #    attempts serialization.
    #    """
    #    print(type(data), type(data.extra_data), data.extra_data)
    #    extra_data = data.extra_data
    #    data.extra_data = json.loads(extra_data)
    #    return data

class ImageListSchema(Schema):
    total = fields.Int()
    images = fields.List(fields.Nested(ImageDisplaySchema))


class AnnotationListSchema(Schema):
    total = fields.Int()
    annotations = fields.List(fields.Nested(AnnotationDisplaySchema))

class HeadstampPredictionListSchema(Schema):
    total = fields.Int()
    predictions = fields.List(fields.Nested(HeadstampPredictionDisplaySchema))

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

