"""Generic pagination schema for list responses."""

from typing import Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard pagination wrapper for list results."""

    items: list[T]
    total: int = Field(..., ge=0, description="Total count of available matching items")
    limit: int = Field(..., gt=0, description="Maximum number of items per page")
    offset: int = Field(..., ge=0, description="Number of items skipped")

