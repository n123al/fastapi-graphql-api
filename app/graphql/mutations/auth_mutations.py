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

    @strawberry.mutation
    async def login(self, info: Info, input: LoginInput) -> AuthPayload:
        try:
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
        except (AuthenticationError, ValidationError) as e:
            raise Exception(str(e))

    @strawberry.mutation(name="refreshToken")  # type: ignore[misc]
    async def refresh_token(self, info: Info, refreshToken: str) -> AccessTokenPayload:
        try:
            data = await self._auth_service.refresh_access_token(refreshToken)
            return AccessTokenPayload(
                accessToken=data["access_token"],
                tokenType=data["token_type"],
                expiresIn=data["expires_in"],
            )
        except AuthenticationError as e:
            raise Exception(str(e))
