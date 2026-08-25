from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.user import User
import uuid

async def get_user_by_email(db:AsyncSession,email:str)->User | None:
    user= await db.execute(select(User).where(User.email == email))
    return user.scalar_one_or_none()

async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()

async def get_user_by_id(db: AsyncSession, user_id) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def search_user_by_username(db:AsyncSession,username:str,current_id:str)->list[User]:
    result=await db.execute(select(User).where(User.username.ilike(f"%{username}"),User.id != current_id,User.deleted_at == None))
    return result.scalar().all()