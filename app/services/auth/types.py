"""Auth feature GraphQL types.
    input RegisterInput { ... }
    type AuthPayload { token: String!  user: User! }
"""
from __future__ import annotations

import strawberry

from app.services.user.types import UserType


@strawberry.input(name="RegisterInput")
class RegisterInput:
    name: str
    email: str
    password: str
    phone: str
    organization: str
    tin: str


@strawberry.type(name="AuthPayload")
class AuthPayload:
    token: str
    user: UserType
