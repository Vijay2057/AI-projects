import os
import uuid
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient, models


# 1. Configuration
load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]

EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-3.8-flash"

COLLECTION_NAME = "company_policy_chunks"               # in SQL DBs Table name
DOCUMENT_PATH = Path("documents/company_policy.txt")
print("doc path : ", DOCUMENT_PATH)

gemini = genai.Client(api_key=API_KEY)

# Local development server.
qdrant = QdrantClient(url="http://localhost:6333")


# 2. Split the document into chunks
def load_and_chunk_document():
    text = DOCUMENT_PATH.read_text(encoding="utf-8")

    # Important : In Langchain chunk_size=500 measures characters by default, not tokens
    # separators -> tell the splitter where it should try to split.
    # chunk_size=500 -> tells it the target maximum size for each chunk.
    # Small pieces can be merged into larger chunks when they fit.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=80,
        separators=["\n\n", "\n", ". ", "?" ," ", ""],   # Note that these separators are tried in order
    )

    chunks = splitter.split_text(text)

    print(f"Created {len(chunks)} chunks")
    return chunks


# 3. Generate an embedding using Gemini
def get_embedding(text: str) -> list[float]:
    result = gemini.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )

    return result.embeddings[0].values


# 4. Create a Qdrant collection
def create_collection(vector_size: int):
    if qdrant.collection_exists(COLLECTION_NAME):
        info = qdrant.get_collection(COLLECTION_NAME)
        existing_size = info.config.params.vectors.size

        if existing_size != vector_size:
            raise ValueError(
                f"Collection uses {existing_size} dimensions, "
                f"but the embedding model returned {vector_size}. "
                "Use a new collection or migrate its vectors."
            )

        print("Using existing Qdrant collection")
        return

    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )

    print("Qdrant collection created")


# 5. Embed and store all chunks in Qdrant
def ingest_document():
    chunks = load_and_chunk_document()

    if not chunks:
        raise ValueError("The document contains no text.")

    # Determine the vector dimension from the actual model output.
    first_vector = get_embedding(chunks[0])
    create_collection(len(first_vector))

    points = []

    for index, chunk in enumerate(chunks):
        vector = (
            first_vector
            if index == 0
            else get_embedding(chunk)
        )

        # Stable IDs make repeated ingestion of unchanged chunks
        # update the same points instead of duplicating them.
        point_id = str(
            uuid.uuid5(
                uuid.NAMESPACE_URL,
                f"{DOCUMENT_PATH.name}:{index}:{chunk}",
            )
        )

        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "text": chunk,
                    "source": DOCUMENT_PATH.name,
                    "chunk_index": index,
                },
            )
        )

    if points:
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True,
        )

    print(f"Stored {len(points)} chunks in Qdrant")


# 6. Retrieve the most relevant chunks
def retrieve_chunks(question: str, top_k: int = 5):
    query_vector = get_embedding(question)

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    ).points

    return results


# 7. Give retrieved context to Gemini to generate an answer
def ask_question(question: str):
    results = retrieve_chunks(question, top_k=5)

    if not results:
        return "No relevant document chunks were found."

    context_parts = []

    for rank, point in enumerate(results, start=1):
        payload = point.payload or {}
        context_parts.append(
            f"[Source {rank}: {payload.get('source', 'unknown')}, "
            f"chunk {payload.get('chunk_index', '?')}]\n"
            f"{payload.get('text', '')}"
        )

    context = "\n\n".join(context_parts)

    prompt = f"""
    You are a helpful question-answering assistant.
    
    Answer the question using only the supplied context.
    If the context does not contain the answer, say you do not
    have enough information. Do not invent policy details.
    
    Context:
    {context}
    
    Question:
    {question}
    
    Provide a concise answer and mention the relevant source.
    """

    response = gemini.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )

    print("\nRetrieved sources:")
    for rank, point in enumerate(results, start=1):
        payload = point.payload or {}
        print(
            f"{rank}. {payload.get('source')} "
            f"(chunk {payload.get('chunk_index')}), "
            f"score={point.score:.4f}"
        )

    return response.text or "The model returned no text."


# 8. Run the application
if __name__ == "__main__":
    ingest_document()

    while True:
        question = input("\nAsk a question (or type 'exit'): ").strip()

        if question.lower() == "exit":
            break

        if not question:
            continue

        try:
            answer = ask_question(question)
            print("\nAnswer:")
            print(answer)
        except Exception as exc:
            print(f"Request failed: {exc}")