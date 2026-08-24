from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os
import uuid

SECRET_KEY = os.getenv("SECRET_KEY", "changeme")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password:str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password:str,hash_password:str)->bool:
    return pwd_context.verify(plain_password,hash_password)

def create_access_token(user_id:uuid)->str:
    expire=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data={
        "user_id": str(user_id),
        "exp":expire
    }
    return jwt.encode(data,SECRET_KEY,algorithm=ALGORITHM)

def decode_access_token(token:str)->str:
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
        return payload
    except JWTError:
        return None
    