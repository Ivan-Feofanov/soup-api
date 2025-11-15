from ninja import Schema
from pydantic import Field, UUID7


class ErrorResponseSchema(Schema):
    error: str


class UIDSchema(Schema):
    """Base schema with the required uid field for all responses"""

    uid: UUID7 = Field(..., description="Unique identifier")
