"""GraphQL request context.

- `user`: decoded JWT claims (or None if unauthenticated)
- `loaders`: per-request DataLoader instances to batch DB lookups
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request
from strawberry.fastapi import BaseContext
from app.core.security import decode_access_token
from app.loaders import create_loaders


@dataclass
class GraphQLContext(BaseContext):
    def __init__(self, request: Any, user: Any, loaders: Any):
        super().__init__() # Initialize the base class
        self.request = request
        self.user = user
        self.loaders = loaders


async def get_context(request: Request) -> GraphQLContext:
    """Build a fresh context for each incoming GraphQL request."""
    token = request.headers.get("authorization")

    user: dict[str, Any] | None = None
    if token:
        if token.lower().startswith("bearer "):
            token = token[7:]
        user = decode_access_token(token)

    return GraphQLContext(
        request=request,
        user=user,
        loaders=create_loaders(),
    )
