from fastapi import FastAPI,APIRouter,Depends,HTTPException,status,Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.user import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from backend.services.user_service import get_user_by_email, get_user_by_username
from backend.services.auth_service import hash_password, verify_password, create_access_token
from backend.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.user import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from backend.services.user_service import get_user_by_email, get_user_by_username,search_user_by_username
from backend.services.auth_service import hash_password, verify_password, create_access_token
from backend.models.user import User
from backend.dependencies import get_current_user
router=APIRouter(prefix="",responses=list[UserResponse])

@router.post("/search",response_model=list[UserResponse])
async def search_username( q: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)) :
    user=await search_user_by_username(db,q,current_user.id)
    if user is None:
        raise HTTPException(status_code=400,detail="User not found")
    return user

@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user