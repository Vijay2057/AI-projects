from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.auth_service import auth_service
from app.chat_services import ChatService
from app.database import get_db
from app.user_service import UserService


app = FastAPI()
router = APIRouter(prefix="/api")
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegistrationRequest(BaseModel):
    username: str
    password: str

class ConversationRequest(BaseModel):
    title: str

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    result: str


@router.post("/register")
async def register(user_details: RegistrationRequest, db: AsyncSession = Depends(get_db)):
    user_service = UserService(db)
    await user_service.create_user(user_details)
    return {"msg": "User created"}


@router.post("/token")
async def create_user(request: dict):
    user_details = request.get("username")
    print("USer details : ", user_details)
    token = await auth_service.generate_access_token(user_details)
    return token


@router.post("/conversations")
async def conversations(request: ConversationRequest,
               current_user: dict = Depends(auth_service.get_current_user),
               db:AsyncSession= Depends(get_db)):
    print("Current user : ", current_user)
    chat_service = ChatService(db)
    response = await chat_service.create_conversation(current_user.get("username"), request.title)
    return response


@router.post("/conversations/{conversation_id}/messages")
async def chat(conversation_id: UUID,
               request: ChatRequest,
               current_user: dict = Depends(auth_service.get_current_user),
               db:AsyncSession= Depends(get_db)):
    chat_service = ChatService(db)
    return StreamingResponse(
        chat_service.chat_message(
            conversation_id,
            request.message,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )




