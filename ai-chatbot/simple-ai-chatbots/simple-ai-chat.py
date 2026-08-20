from dotenv import load_dotenv
from google import genai


# In the environment, the SDK can pick up the API key automatically
# if we give with GEMINI_API_KEY.
# for that we need to load envs into python environment using load_dotenv().
load_dotenv()

# Creates your Gemini client
client = genai.Client()

# Hitting model with query
response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents="What is Python?"
)

print(response.text)

