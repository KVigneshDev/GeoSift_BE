"""User feature resolvers — exposes the `me` query.

Mirrors `services/user/user.resolver.js`. The `Query` class here is merged
with the auth `Mutation` and any other features in `app/schema.py`.
"""
from __future__ import annotations

import strawberry
from strawberry.types import Info

from app.context.auth import GraphQLContext
from app.core.errors import AuthError
from app.services.user.service import UserService
from app.services.user.types import UserType


@strawberry.type
class UserQuery:
    @strawberry.field
    async def me(self, info: Info[GraphQLContext, None]) -> UserType:
        ctx = info.context
        if ctx.user is None:
            raise AuthError("Not authenticated")

        user_doc, org_doc = await UserService.get_me(ctx.user["id"])
        return UserType.from_document(user_doc, org_doc)
