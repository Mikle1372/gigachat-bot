from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

class VectorStoreManager:
    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        
    def create_store(self, documents) -> FAISS:
        """Создание FAISS хранилища"""
        return FAISS.from_documents(documents, self.embedding_model)