from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.schemas.friend_request import SendRequestBody, FriendRequestResponse
from backend.services.friend_service import send_request, respond_request, get_pending_requests
from backend.models.user import User
from backend.models.friend_request import FriendRequest,FriendStatus
import uuid

router = APIRouter(prefix="/friends", tags=["friends"])

@router.post("/request", response_model=FriendRequestResponse, status_code=201)
async def send_friend_request(
    body: SendRequestBody,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await send_request(db,current_user.id,body.receiver_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.patch("/request/{request_id}/accept",response_model=FriendRequestResponse)
async def accept_request(
    request_id:uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await respond_request(db,request_id,current_user.id,FriendStatus.ACCEPTED)
    except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        
@router.patch("/request/{request_id}/decline", response_model=FriendRequestResponse)
async def decline_request(
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        return await respond_request(db, request_id, current_user.id, FriendStatus.REJECTED)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
@router.get("/request/all",response_model=list[FriendRequestResponse])
async def get_all_request(
    db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    try:
        return await get_pending_requests(db,current_user.id)
    except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))