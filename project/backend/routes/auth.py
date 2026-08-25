from fastapi import FastAPI,APIRouter,Depends,HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.user import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from backend.services.user_service import get_user_by_email, get_user_by_username
from backend.services.auth_service import hash_password, verify_password, create_access_token
from backend.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.schemas.user import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from backend.services.user_service import get_user_by_email, get_user_by_username
from backend.services.auth_service import hash_password, verify_password, create_access_token
from backend.models.user import User

router=APIRouter(prefix="/auth",tags=["Auth"])

@router.post("/register",response_model=UserResponse)
async def register(body:RegisterRequest,db:AsyncSession=Depends(get_db)):
    if await get_user_by_email(db,body.email):
        raise HTTPException(status_code=400,detail="User email already exists")
    if await get_user_by_username(db,body.username):
        raise HTTPException(status_code=400,detail="User username already exists")
    user=User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    token=create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


