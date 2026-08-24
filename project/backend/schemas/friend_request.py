from pydantic import BaseModel
import uuid
from datetime import datetime

class SendRequestBody(BaseModel):
    receiver_id: uuid.UUID

class FriendRequestResponse(BaseModel):
    id: uuid.UUID
    sender_id: uuid.UUID
    receiver_id: uuid.UUID
    status: str
    created_at: datetime
    model_config = {"from_attributes": True}
