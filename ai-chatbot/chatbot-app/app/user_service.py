from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models import User
from app.hash import hash_password

class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_user(self, user):
        new_user = User(user_name=user.username, password=hash_password(user.password))
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

    async def get_user_id(self, username: str):
        stmt = select(User.id).where(User.user_name == username)
        result = await self.db.execute(stmt)
        user_obj = result.scalar_one_or_none()
        if not user_obj:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )
        return user_obj

