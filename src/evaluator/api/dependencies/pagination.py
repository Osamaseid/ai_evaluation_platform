"""Pagination query parameters dependency."""

from dataclasses import dataclass
from fastapi import Query


@dataclass
class PaginationParams:
    """Standardized limit/offset pagination parameters."""

    limit: int = 20
    offset: int = 0


def get_pagination(
    limit: int = Query(default=20, ge=1, le=100, description="Page item limit (max 100)"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
) -> PaginationParams:
    """Extract and validate pagination query parameters."""
    return PaginationParams(limit=limit, offset=offset)

