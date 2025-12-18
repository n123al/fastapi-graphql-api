from typing import Optional

import strawberry
from strawberry.types import Info

from app.core.exceptions import AuthenticationError, ValidationError
from app.data.repositories import UserRepository
from app.graphql.types.types import AccessTokenPayload, AuthPayload, LoginInput
from app.services.auth import AuthenticationService


class AuthMutations:
    def __init__(self) -> None:
        self._auth_service = AuthenticationService(UserRepository())

    async def login(self, info: Info, input: LoginInput) -> AuthPayload:
        # Let exceptions propagate so FastAPI exception handlers catch them
        user = await self._auth_service.authenticate_user(
            input.identifier, input.password
        )
        tokens = await self._auth_service.generate_tokens(user)
        return AuthPayload(
            accessToken=tokens["access_token"],
            refreshToken=tokens["refresh_token"],
            tokenType=tokens["token_type"],
            expiresIn=tokens["expires_in"],
        )

    async def refresh_token(self, info: Info, refreshToken: str) -> AccessTokenPayload:
        # Let AuthenticationError propagate so FastAPI returns 401
        data = await self._auth_service.refresh_access_token(refreshToken)
        return AccessTokenPayload(
            accessToken=data["access_token"],
            tokenType=data["token_type"],
            expiresIn=data["expires_in"],
        )
