import uuid
from langchain_ollama import OllamaEmbeddings
import chromadb



class SemanticMemory:
    def __init__(self, collection_name="agent_memory"):
        self.embedder = OllamaEmbeddings(model="all-minilm")
        self.client = chromadb.PersistentClient(path="./memory_db")

        self.collection = self.client.get_or_create_collection(
        name=collection_name)
        
    def embed(self, text: str):
        return self.embedder.embed_query(text)

    def add(self, text: str, metadata: dict = None):
        embedding = self.embed(text)
        self.collection.add(
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata or {}],
            ids=[str(uuid.uuid4())]
        )

    def search(self, query: str, top_k=5):
        if len(self.collection.get()["ids"]) == 0:
            return []

        embedding = self.embed(query)

        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )

        return results.get("documents", [[]])[0]