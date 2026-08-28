import asyncio
import uuid
from typing import Literal

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import AsyncSessionLocal
from backend.models.chat import (
    ConversationMember,
    Message,Conversation
)
from backend.realtime import manager
from backend.services.auth_service import decode_access_token
from backend.services.user_service import get_user_by_id
from backend.models.friend_request import FriendRequest,FriendStatus

router = APIRouter(tags=["websocket"])

class AuthenticationEvent(BaseModel):
    type: Literal["auth"]
    token: str = Field(min_length=1)
    
class SendMessageEvent(BaseModel):
    type: Literal["message.send"]
    receiver_id: uuid.UUID
    client_message_id: uuid.UUID
    content: str = Field(
        min_length=1,
        max_length=4000,
    )
    
from sqlalchemy import select, or_, and_

async def authenticate_websocket(
    websocket:WebSocket,
    db:AsyncSession
)->uuid.UUID | None:
    try:
        raw_event=await asyncio.wait_for(
            websocket.receive_json(),
            timeout=10
        )
        authenticate=AuthenticationEvent.model_validate(
            raw_event
        )
        user_id = decode_access_token(authenticate.token)
        if user_id is None:
            return None
        user=await get_user_by_id(
            db,user_id
        )
        if not user:
            return None
        return user.id
            
    
    except (
        ValidationError,
        asyncio.TimeoutError,
        ValueError,
        TypeError,
        WebSocketDisconnect,
    ):
        return None

async def get_or_create_direct_message(
    db:AsyncSession,
    sender_id: uuid.UUID,
    receiver_id: uuid.UUID,
)->Conversation:
    friendship= await db.scalar(
         select(FriendRequest).where(
                    or_(
                        and_(FriendRequest.sender_id == sender_id,FriendRequest.receiver_id == receiver_id),
                        and_(
                            FriendRequest.sender_id == receiver_id ,FriendRequest.receiver_id == sender_id
                        ),
                        and_(
                            FriendRequest.status == FriendStatus.ACCEPTED,
                        )
                    )
                )
    )
    if  friendship is None:
        raise PermissionError(
           "You can only message accepted friends"
        )
        
    sorted_user_ids = sorted(
        [str(sender_id), str(receiver_id)]
    )
    direct_key = f"{sorted_user_ids[0]}:{sorted_user_ids[1]}"
    conversation=await db.scalar(
        select(Conversation).where(
            Conversation.direct_key  == direct_key
        )
    )
    if conversation is not None:
        return conversation
    
    conversation=Conversation(direct_key=direct_key)
    db.add(conversation)
    await db.flush()
    db.add_all(
        [
             ConversationMember(
                conversation_id=conversation.id,
                user_id=sender_id,
            ),
            ConversationMember(
                conversation_id=conversation.id,
                user_id=receiver_id,
            ),
        ]
    )
    db.flush()
    return conversation
        

async def save_message(
    db:AsyncSession,
    sender_id:uuid.UUID,
    event:SendMessageEvent
):
   
    content=event.content.strip()
    
    if not content:
        raise ValueError("Message connot be empty")
    conversation=await get_or_create_direct_message(
        db,sender_id=sender_id,
        receiver_id=event.receiver_id
    )
    message_id=uuid.uuid4()
    insert_statement = (
        insert(Message)
        .values(
            id=message_id,
            conversation_id=conversation.id,
            sender_id=sender_id,
            client_message_id=event.client_message_id,
            content=content,
        )
        .on_conflict_do_nothing(
            constraint="uq_message_sender_client_id"
        )
        .returning(Message.id)
    )
    result=await db.execute(insert_statement)
    create_message_id=result.scalar_one_or_none()
    
    if create_message_id is None:
        existing_message=await db.scalar(
            select(Message).where(
                Message.sender_id == sender_id,
                Message.client_message_id
                == event.client_message_id,
            )
        )
        
        await db.rollback()
        return existing_message,[] ,False

    message=await db.scalar(
        select(Message).where(
            Message.id == create_message_id
        )
    )
    members_result=await db.execute(
        select(ConversationMember).where(
            ConversationMember.conversation_id == conversation.id
        )
        
    )
    recipient_ids = list(
        members_result.scalars().all()
    )

    await db.commit()
    await db.refresh(message)

    return message, recipient_ids, True
    

@router.websocket("/ws")
async def websocket_chat(
    websocket:WebSocket
)->None:
    await websocket.accept()
    async with AsyncSessionLocal() as db:
        user_id = await authenticate_websocket(
            websocket=websocket,
            db=db,
        )

    if user_id is None:
        await websocket.close(
            code=1008,
            reason="Authentication failed",
        )
        return

    await manager.connect(
        user_id=user_id,
        websocket=websocket,
    )

    await websocket.send_json(
        {
            "type": "auth.success",
            "user_id": str(user_id),
        }
    )

    try:
        while True:
            raw_event = await websocket.receive_json()

            try:
                event = SendMessageEvent.model_validate(
                    raw_event
                )

                async with AsyncSessionLocal() as db:
                    (
                        message,
                        recipient_ids,
                        created,
                    ) = await save_message(
                        db=db,
                        sender_id=user_id,
                        event=event,
                    )

                if not created:
                    await websocket.send_json(
                        {
                            "type": "message.ack",
                            "message_id": (
                                str(message.id)
                                if message
                                else None
                            ),
                            "client_message_id": str(
                                event.client_message_id
                            ),
                            "duplicate": True,
                        }
                    )
                    continue

                outgoing_event = {
                    "type": "message.created",
                    "message": {
                        "id": str(message.id),
                        "conversation_id": str(
                            message.conversation_id
                        ),
                        "sender_id": str(
                            message.sender_id
                        ),
                        "client_message_id": str(
                            message.client_message_id
                        ),
                        "content": message.content,
                        "created_at": (
                            message.created_at.isoformat()
                        ),
                    },
                }

                await manager.send_to_users(
                    user_ids=recipient_ids,
                    event=outgoing_event,
                )

            except ValidationError as error:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "INVALID_EVENT",
                        "detail": str(error),
                    }
                )

            except PermissionError as error:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "FORBIDDEN",
                        "detail": str(error),
                    }
                )

            except ValueError as error:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "INVALID_MESSAGE",
                        "detail": str(error),
                    }
                )

            except Exception:
                await websocket.send_json(
                    {
                        "type": "error",
                        "code": "SERVER_ERROR",
                        "detail": "Could not process the message",
                    }
                )

    except WebSocketDisconnect:
        pass

    finally:
        await manager.disconnect(
            user_id=user_id,
            websocket=websocket,
        )
