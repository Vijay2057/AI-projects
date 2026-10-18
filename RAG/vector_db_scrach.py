from google import genai
from dotenv import load_dotenv
import numpy as np


load_dotenv()
client = genai.Client()
documents = [
    "FastAPI is a modern Python framework for building APIs.",
    "PostgreSQL is a relational database used to store structured data.",
    "RAG retrieves relevant information and provides it to an LLM.",
    "React is a JavaScript library used to build user interfaces.",
    "Python is a popular programming language used in web development."
]


def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    # print("embed result : ", result)
    return result.embeddings[0].values


# function to check distance between 2 vectors using numpy
def cosine_similarity(vector_a, vector_b):
    a = np.array(vector_a)
    b = np.array(vector_b)

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )


document_vectors = []

# create each document as embedding
for document in documents:
    vector = get_embedding(document)
    document_vectors.append((document, vector))

query = "Which Python framework can I use to build APIs?"
query_vector = get_embedding(query)

result = []
for chunk ,vector in document_vectors:
    score = cosine_similarity(query_vector, vector)
    result.append((score, chunk))


result.sort(reverse=True)   #python sort tuples lexicograpically (1st ele, if equal 2nd ele, etc..)
print(result[0][1])