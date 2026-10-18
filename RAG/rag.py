from google import genai
from dotenv import load_dotenv
import numpy as np

load_dotenv()

client = genai.Client()

with open("company_policy_doc.txt", "r", encoding="utf-8") as file:
    document = file.read()


def chunk_text(text, chunk_size=200, overlap=50):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks


chunks = chunk_text(document)

def get_embedding(text):
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )
    return result.embeddings[0].values


chunk_embeddings = []

for chunk in chunks:
    vector = get_embedding(chunk)
    chunk_embeddings.append(vector)


chunk_data = []
for index, chunk in enumerate(chunks):
    vector = get_embedding(chunk)
    chunk_data.append({
        "chunk_id": index,
        "content": chunk,
        "embedding": vector
    })


def cosine_similarity(vector_a, vector_b):
    a = np.array(vector_a)
    b = np.array(vector_b)

    return np.dot(a, b) / (
        np.linalg.norm(a) * np.linalg.norm(b)
    )

# query = "How many days early should employee should inform for planned leave?"
# query = "How many days early should employee inform about emergency leave?"
# query = "what is the organization name?"
query = "what is CEO name?"
query_vector = get_embedding(query)

result = []
for chunk in chunk_data:
    score = cosine_similarity(query_vector, chunk["embedding"])
    result.append((score, chunk["content"]))

result.sort(reverse=True)   #python sort tuples lexicograpically (1st ele, if equal 2nd ele, etc..)

# TOP-K = 3, let's take the top 3 matching
final_matching_chunks = [result[0][1], result[1][1], result[2][1]]
prompt = f"""
    You are a helpful question-answering assistant.
    Answer the question using only the supplied context.
    If the context does not contain the answer, say you do not
    have enough information. Do not invent policy details.

    context is {','.join(final_matching_chunks)}

    query is {query}
"""

response = client.models.generate_content(
    model="gemini-3.6-flash",
    contents=prompt
)

print("final response is : ", response.text)




