from dotenv import load_dotenv
from google import genai

# In the environment, the SDK can pick up the API key automatically
# if we give with GEMINI_API_KEY.
# for that we need to load envs into python environment using load_dotenv().
load_dotenv()

class LLMService:
    def __init__(self):
        self.client = genai.Client()

    async def generate(self, chat):
        # Hitting model with query
        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=chat
        )
        return response.text

    async def generate_stream(self, chat):
        response = await self.client.aio.models.generate_content_stream(
            model="gemini-3.6-flash",
            contents=chat
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text