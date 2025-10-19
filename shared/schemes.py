from ninja import Schema


class ErrorResponseSchema(Schema):
    error: str
