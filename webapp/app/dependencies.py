from fastapi import Cookie, Header
from typing import Optional


def get_token(token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)) -> Optional[str]:
    if token:
        return token
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1]
    return None
