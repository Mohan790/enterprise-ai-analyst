import uuid, re
from langchain_community.document_loaders import BSHTMLLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
client = QdrantClient(host="localhost", port=6333)

documents = [
    ("data/raw/Tesla_2023.html",   "Tesla",   2023),
    ("data/raw/Meta_2023.html",    "Meta",    2023),
    ("data/raw/Nvidia_2023.html",  "Nvidia",  2023),
    ("data/raw/Samsung_2023.html", "Samsung", 2023),
]

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

for path, company, year in documents:
    print(f"\nProcessing {company}...")
    loader = BSHTMLLoader(path, open_encoding="utf-8")
    pages = loader.load()
    raw = clean_text(" ".join(p.page_content for p in pages))
    print(f"  -> {len(raw)} characters")
    chunks = splitter.create_documents([raw])
    print(f"  -> {len(chunks)} chunks")
    points = [PointStruct(
        id=str(uuid.uuid4()),
        vector=embeddings.embed_query(c.page_content),
        payload={"text": c.page_content, "company_name": company, "document_year": year}
    ) for c in chunks]
    client.upsert("financial_docs", points=points)
    print(f"  -> Inserted {len(points)} vectors!")

print("\nAll done! Checking total...")
info = client.get_collection("financial_docs")
print(f"Total vectors in Qdrant: {info.points_count}")
