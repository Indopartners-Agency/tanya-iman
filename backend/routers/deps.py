from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from models import User
from services.auth import InvalidTokenError, Principal, verify_token
from services.users import ensure_user
from storage import Storage, get_storage


def storage_dep() -> Storage:
    return get_storage()


StorageDep = Annotated[Storage, Depends(storage_dep)]


async def principal_dep(
    authorization: Annotated[str | None, Header()] = None,
) -> Principal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return await verify_token(authorization[7:].strip())
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


PrincipalDep = Annotated[Principal, Depends(principal_dep)]


async def current_user_dep(principal: PrincipalDep, storage: StorageDep) -> User:
    return await ensure_user(storage, principal.uid, principal.auth_method)


CurrentUser = Annotated[User, Depends(current_user_dep)]
