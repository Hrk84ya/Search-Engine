"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, status
from app.core.auth import verify_password, create_access_token, DEMO_USERS
from app.models.schemas import TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token", response_model=TokenResponse)
async def login(request: TokenRequest):
    """Obtain a JWT access token."""
    user = DEMO_USERS.get(request.username)
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return TokenResponse(access_token=token)
