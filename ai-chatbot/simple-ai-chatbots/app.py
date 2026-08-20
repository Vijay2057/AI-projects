from dotenv import load_dotenv
from fastapi import FastAPI
from google import genai
from pydantic import BaseModel


# In the environment, the SDK can pick up the API key automatically
# if we give with GEMINI_API_KEY.
# for that we need to load envs into python environment using load_dotenv().
load_dotenv()

app = FastAPI()

# Creates your Gemini client
client = genai.Client()


class ChatRequest(BaseModel):
    message: str

chat_history = []


@app.post("/api/chat")
def chat(request: ChatRequest):
    # Add request to history
    chat_history.append({"role": "user",
                         "parts": [
            {
                "text": request.message
            }
        ]})

    print("chat_history: ", chat_history)
    print("==========================================")
    # Hitting model with query
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=chat_history
    )
    # Add response to history
    chat_history.append({"role": "assistant",
                         "parts": [
                             {
                                "text": response.text
                             }]})
    return {"response" : response.text}

