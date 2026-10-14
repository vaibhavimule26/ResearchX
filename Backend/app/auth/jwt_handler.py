from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database.mongodb import users_collection

SECRET_KEY = "researchx_secret_key"
ALGORITHM = "HS256"

security = HTTPBearer(auto_error=False)


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication token missing"
        )
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or Expired Token"
        )


def get_user_from_token(token: str) -> Optional[dict]:
    if not token or not isinstance(token, str):
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        user = users_collection.find_one({"email": email})
        if not user:
            return None
        user_id = str(user.get("user_id") or user.get("_id"))
        return {
            "user_id": user_id,
            "email": user["email"],
            "name": user.get("name", ""),
        }
    except Exception:
        return None


def get_current_authenticated_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> dict:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Please log in."
        )
    user = get_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid, expired, or revoked token. Please log in again."
        )
    return user


def get_optional_user(request: Optional[Request]) -> Optional[dict]:
    if not request:
        return None
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    return get_user_from_token(token)