from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.friend_request import FriendRequest,FriendStatus
from sqlalchemy import select, or_, and_
import uuid


async def send_request(db:AsyncSession,sender_id:uuid.UUID,receiver_id: uuid.UUID)->FriendRequest:
    existing_user=await db.execute(
        select(FriendRequest).where(
            or_(
                and_(FriendRequest.sender_id == sender_id,FriendRequest.receiver_id == receiver_id),
                and_(
                    FriendRequest.sender_id == receiver_id ,FriendRequest.receiver_id == sender_id
                ),
                and_(
                    FriendRequest.status == "accepted"
                )
            )
        )
        
            
    )
    if existing_user.scalar_one_or_none():
        raise ValueError("Friend requests is already exists")
    if db.execute(
        select(FriendRequest).where(
                    or_(
                        and_(FriendRequest.sender_id == sender_id,FriendRequest.receiver_id == receiver_id),
                        and_(
                            FriendRequest.sender_id == receiver_id ,FriendRequest.receiver_id == sender_id
                        ),
                        and_(
                            FriendRequest.status == "rejected"
                        )
                    )
                )
    ):
        raise ValueError("Friend requests rejected")
    
    req=FriendRequest(sender_id=sender_id,receiver_id=receiver_id,status=FriendStatus.PENDING)
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


async def respond_request(db:AsyncSession,request_id:uuid.UUID,received_id:uuid.UUID,action:FriendStatus)->FriendRequest:
    result=await db.execute(
        select(FriendRequest).where(
            FriendRequest.id == request_id,
            FriendRequest.receiver_id == request_id,
            FriendRequest.status == FriendStatus.PENDING
        )
    )
    req=result.scalar_one_or_none()
    if not req:
        raise ValueError("Request not found or already accepted")
    req.status=FriendStatus.ACCEPTED  if action == FriendStatus.ACCEPTED else FriendStatus.REJECTED
    await db.commit()
    await db.refresh(req)
    return req

async def get_pending_requests(db:AsyncSession,user_id:uuid.UUID)->list[FriendRequest]:
    result=await db.execute(
        select(FriendRequest).where(
            FriendRequest.receiver_id == user_id,
            FriendRequest.status == FriendStatus.PENDING
        )
    )
    return result.scalars().all()