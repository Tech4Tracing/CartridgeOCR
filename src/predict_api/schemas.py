from marshmallow import Schema, fields

# TODO: rework so each primer is associated with its casing
class BBoxSchema(Schema):
    confidence = fields.Float()
    box = fields.List(fields.Float)    

class HeadstampPredictionSchema(Schema):
    image = fields.Str()
    primers = fields.List(fields.Nested(BBoxSchema))
    casings = fields.List(fields.Nested(BBoxSchema))

class ErrorSchema(Schema):
    status = fields.Int()
    title = fields.Str()
    detail = fields.Str()


class Errors(Schema):
    errors = fields.List(fields.Nested(ErrorSchema))
