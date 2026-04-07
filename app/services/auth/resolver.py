"""Auth feature resolvers — register and login mutations.
"""
from __future__ import annotations

import strawberry

from app.services.auth.types import AuthPayload, RegisterInput
from app.services.user.service import UserService
from app.services.user.types import UserType


@strawberry.type
class AuthMutation:
    @strawberry.mutation
    async def register(self, input_data: RegisterInput) -> bool:
        await UserService.create_user(
            name=input_data.name,
            email=input_data.email,
            password=input_data.password,
            phone=input_data.phone,
            organization=input_data.organization,
            tin=input_data.tin,
        )
        return True

    @strawberry.mutation
    async def login(self, email: str, password: str) -> AuthPayload:
        token, user_doc, org_doc = await UserService.login_user(email, password)
        return AuthPayload(
            token=token,
            user=UserType.from_document(user_doc, org_doc),
        )
