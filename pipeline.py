import os, uuid, re
from langchain_community.document_loaders import BSHTMLLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

# --- Setup ---
print("Loading embedding model...")
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
splitter = SemanticChunker(
    embeddings,
    breakpoint_threshold_type="percentile"
)
client = QdrantClient(host="localhost", port=6333)
client.recreate_collection(
    collection_name="financial_docs",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)
print("Qdrant collection created!")

# --- Cleaning function ---
def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'Page \d+ of \d+', '', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

# --- Main ingest function ---
def ingest_file(file_path: str, company: str, year: int):
    print(f"\nProcessing {company} {year}...")
    loader = BSHTMLLoader(file_path, open_encoding="utf-8")
    pages = loader.load()
    raw_text = " ".join(p.page_content for p in pages)
    clean = clean_text(raw_text)
    print(f"  -> Text length: {len(clean)} characters")
    chunks = splitter.create_documents([clean])
    print(f"  -> {len(chunks)} semantic chunks created")
    points = []
    for chunk in chunks:
        vector = embeddings.embed_query(chunk.page_content)
        points.append(PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "text": chunk.page_content,
                "company_name": company,
                "document_year": year,
            }
        ))
    client.upsert("financial_docs", points=points)
    print(f"  -> Inserted {len(points)} vectors into Qdrant!")

# --- Run for all 5 documents ---
documents = [
    ("data/raw/Apple_2023.html",     "Apple",     2023),
    ("data/raw/Tesla_2023.html",     "Tesla",     2023),
    ("data/raw/Microsoft_2023.html", "Microsoft", 2023),
    ("data/raw/Amazon_2023.html",    "Amazon",    2023),
    ("data/raw/Google_2023.html",    "Google",    2023),
]

for path, company, year in documents:
    ingest_file(path, company, year)

print("\n✅ All documents ingested successfully!")
print("Your vector database is ready.")