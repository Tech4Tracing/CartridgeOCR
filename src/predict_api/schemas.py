from marshmallow import Schema, fields

class BBoxSchema(Schema):
    confidence = fields.Float()
    box = fields.List(fields.Float)    


class DetectionSchema(Schema):
    primer = fields.Nested(BBoxSchema)
    casing = fields.Nested(BBoxSchema)

"""
{
    'inference_version': <inference version>,
    'image': <optional base 64 encoded output image>,
    'detections': <list of detections, each with schema:
        {'casing': {'box':<rectangle>, 'confidence': <float>},
            'primer': {'box': <rectangle>, 'confidence': <float>}}>
}
"""
class HeadstampPredictionSchema(Schema):
    inference_version = fields.Str()
    image = fields.Str(allow_none=True)
    detections = fields.List(fields.Nested(DetectionSchema))
    
class ErrorSchema(Schema):
    status = fields.Int()
    title = fields.Str()
    detail = fields.Str()


class Errors(Schema):
    errors = fields.List(fields.Nested(ErrorSchema))
