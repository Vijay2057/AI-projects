from sqlalchemy.ext.asyncio import AsyncSession


class DbService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, query):
        pass

    async def get_conversation_history(self):
        result = await self.db.execute