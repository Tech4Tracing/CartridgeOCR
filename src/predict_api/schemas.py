from marshmallow import Schema, fields

class BBoxSchema(Schema):
    confidence = fields.Float()
    x = fields.Float()
    y = fields.Float()
    w = fields.Float()
    h = fields.Float()

class HeadstampPredictionSchema(Schema):
    id = fields.Str()
    primer = BBoxSchema()
    casing = BBoxSchema()
    

class HeadstampPredictionListSchema(Schema):
    id = fields.Str()
    predictions = fields.List(fields.Nested(HeadstampPredictionSchema))

class ErrorSchema(Schema):
    status = fields.Int()
    title = fields.Str()
    detail = fields.Str()


class Errors(Schema):
    errors = fields.List(fields.Nested(ErrorSchema))
