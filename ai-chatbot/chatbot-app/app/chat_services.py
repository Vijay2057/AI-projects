from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.user_service import UserService
from app.models import Conversation, Message
from app.llm_service import LLMService


load_dotenv()

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
        self.llm_service = LLMService()

    async def create_conversation(self, user, title):
        # Make sure user exit in DB, if not create user
        user_id = await self.user_service.get_user_id(user)
        new_conversation = Conversation(user_id=user_id, title=title)
        self.db.add(new_conversation)
        await self.db.commit()
        await self.db.refresh(new_conversation)
        conversation_id = new_conversation.id
        return {"conversation_id": conversation_id, "message": "New conversation created"}


    async def history_messages(self, conversation_id, limit=20):
        history_messages = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = list(history_messages.scalars())
        messages.reverse()
        return messages

    async def save_message(self, conversation_id, role, message):
        new_message = Message(conversation_id=conversation_id, role=role, content=message)
        self.db.add(new_message)
        await self.db.commit()

    async def chat_message(self, conversation_id, query):
        history_messages = await self.history_messages(conversation_id)

        # Convert history messages into llm format
        chat_history = []
        for message in history_messages:
            chat_history.append({"role": message.role, "parts": [{"text": message.content}]})

        # add current question
        chat_history.append({"role": "user", "parts": [{"text": query}]})

        # add response message to message table
        await self.save_message(conversation_id, "user", query)

        full_response = []
        async for chunk in self.llm_service.generate_stream(chat_history):
            full_response.append(chunk)

            yield chunk

        assistant_response = "".join(full_response)

        # add response message to message table
        await self.save_message(conversation_id, "assistant", assistant_response)

