import uuid, re
from langchain_community.document_loaders import BSHTMLLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
splitter = SemanticChunker(embeddings, breakpoint_threshold_type="percentile")
client = QdrantClient(host="localhost", port=6333)

loader = BSHTMLLoader("data/raw/Tesla_2023.html", open_encoding="utf-8")
pages = loader.load()
raw_text = " ".join(p.page_content for p in pages)
clean = re.sub(r'\s+', ' ', raw_text).strip()
print(f"Tesla text length: {len(clean)} characters")
chunks = splitter.create_documents([clean])
print(f"Tesla chunks: {len(chunks)}")
points = [PointStruct(
    id=str(uuid.uuid4()),
    vector=embeddings.embed_query(c.page_content),
    payload={"text": c.page_content, "company_name": "Tesla", "document_year": 2023}
) for c in chunks]
client.upsert("financial_docs", points=points)
print(f"Inserted {len(points)} Tesla vectors!")
