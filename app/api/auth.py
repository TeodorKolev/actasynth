"""Cognito JWT authentication dependency"""

import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings
from app.observability.logger import get_logger

logger = get_logger(__name__)
security = HTTPBearer()

_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    """Fetch Cognito public keys (cached in memory for Lambda container lifetime)"""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    url = (
        f"https://cognito-idp.{settings.cognito_region}.amazonaws.com"
        f"/{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=5)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache


async def verify_cognito_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate a Cognito JWT bearer token.

    In development (COGNITO_USER_POOL_ID not set), auth is skipped and a
    dummy payload is returned so local dev works without Cognito configured.
    """
    if not settings.cognito_user_pool_id:
        logger.warning("cognito_auth_disabled", reason="COGNITO_USER_POOL_ID not set")
        return {"sub": "dev-user", "dev_mode": True}

    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.cognito_client_id,
        )
        return payload
    except JWTError as e:
        logger.warning("cognito_token_invalid", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except Exception as e:
        logger.error("cognito_auth_error", error=str(e))
        raise HTTPException(status_code=401, detail="Authentication failed")
