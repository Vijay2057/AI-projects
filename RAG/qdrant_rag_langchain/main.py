
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models


# 1. Load configuration
load_dotenv()

api_key = os.environ["GEMINI_API_KEY"]
os.environ.setdefault("GOOGLE_API_KEY", api_key)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME", "company_policy_chunks"
)
DOCUMENTS_DIR = Path(os.getenv("DOCUMENTS_DIR", "documents"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "80"))

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL", "gemini-embedding-001"
)
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")


# 2. Initialize the embedding model and Qdrant client
embeddings = GoogleGenerativeAIEmbeddings(
    model=EMBEDDING_MODEL
)
client = QdrantClient(url=QDRANT_URL)


# 3. Load documents and split them into chunks
def load_and_split_documents():
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    documents = []

    # Find all TXT files, including files in subdirectories.
    for path in sorted(DOCUMENTS_DIR.rglob("*.txt")):
        text = path.read_text(encoding="utf-8")

        # Keep the source path so chunks can be traced to a document.
        source = path.relative_to(DOCUMENTS_DIR).as_posix()

        document = Document(
            page_content=text,
            metadata={"source": source},
        )

        documents.extend(splitter.split_documents([document]))

    if not documents:
        raise ValueError(
            f"No .txt documents found in {DOCUMENTS_DIR.resolve()}"
        )

    return documents


# 4. Generate deterministic IDs for each chunk
def get_point_id(document, index):
    source = document.metadata["source"]
    chunk_text = document.page_content

    # Identical source, position, and text produce the same UUID.
    unique_name = f"{source}:{index}:{chunk_text}"

    return str(uuid.uuid5(uuid.NAMESPACE_URL, unique_name))


# 5. Ingest chunks into Qdrant
def ingest_documents():
    documents = load_and_split_documents()

    # Group chunks by source so existing chunks can be replaced
    # when a document is re-ingested.
    sources = {doc.metadata["source"] for doc in documents}

    if client.collection_exists(COLLECTION_NAME):
        vector_store = QdrantVectorStore(
            client=client,
            collection_name=COLLECTION_NAME,
            embedding=embeddings,
        )

        # Remove old chunks for the documents being re-ingested.
        for source in sources:
            client.delete(
                collection_name=COLLECTION_NAME,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="metadata.source",
                                match=models.MatchValue(value=source),
                            )
                        ]
                    )
                ),
                wait=True,
            )

        ids = [
            get_point_id(doc, index)
            for index, doc in enumerate(documents)
        ]
        vector_store.add_documents(documents=documents, ids=ids)

    else:
        # Create the collection and insert its first set of chunks.
        ids = [
            get_point_id(doc, index)
            for index, doc in enumerate(documents)
        ]

        vector_store = QdrantVectorStore.from_documents(
            documents=documents,
            embedding=embeddings,
            ids=ids,
            url=QDRANT_URL,
            collection_name=COLLECTION_NAME,
        )

    print(f"Ingested {len(documents)} chunks into Qdrant.")


# 6. Retrieve relevant chunks for a question
def retrieve_context(question, k=4):
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )

    # LangChain embeds the question and searches Qdrant.
    return vector_store.similarity_search(question, k=k)


# 7. Generate an answer grounded in retrieved context
def answer_question(question):
    retrieved_docs = retrieve_context(question)

    context = "\n\n".join(
        f"Source: {doc.metadata.get('source', 'unknown')}\n"
        f"Content: {doc.page_content}"
        for doc in retrieved_docs
    )

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "Answer the user's question using only the supplied "
            "context. If the answer is not in the context, say "
            "you could not find the answer in the documents."
        ),
        (
            "human",
            "Context:\n{context}\n\nQuestion:\n{question}",
        ),
    ])

    llm = ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        temperature=0,
    )

    chain = prompt | llm | StrOutputParser()

    answer = chain.invoke({
        "context": context,
        "question": question,
    })

    print(f"\nAnswer:\n{answer}")

    print("\nRetrieved sources:")
    for doc in retrieved_docs:
        print(f"- {doc.metadata.get('source', 'unknown')}")


# 8. Run the requested operation
if __name__ == "__main__":
    # python rag_app.py ingest
    # python rag_app.py ask

    if len(sys.argv) < 2:
        print("Usage: python rag_app.py [ingest|ask]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "ingest":
        ingest_documents()

    elif command == "ask":
        question = input("Enter your question: ").strip()

        if question:
            answer_question(question)
        else:
            print("Please enter a question.")

    else:
        print("Unknown command. Use 'ingest' or 'ask'.")
        sys.exit(1)