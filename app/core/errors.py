"""Application-level GraphQL errors.
Strawberry surfaces any exception raised inside a resolver as a GraphQL error;
we attach a machine-readable `code` via the `extensions` field so clients can
branch on error type just like with Apollo Server.
"""
from __future__ import annotations

from typing import Any

from graphql import GraphQLError


class AppError(GraphQLError):
    """Base application error with an error code and optional metadata."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_SERVER_ERROR",
        meta: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            extensions={"code": code, "meta": meta or {}},
        )


class AuthError(AppError):
    def __init__(self, message: str = "Not authenticated") -> None:
        super().__init__(message, code="UNAUTHENTICATED")


class ValidationError(AppError):
    def __init__(self, message: str, meta: dict[str, Any] | None = None) -> None:
        super().__init__(message, code="BAD_USER_INPUT", meta=meta)
