from langchain_community.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from typing import List

class DocumentProcessor:
    def __init__(self, config):
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            separators=["\n# ", "\n## ", "\n### ", "\n- ", "\n", " "]
        )
    
    def load_and_split(self, url: str) -> List[Document]:
        """Загрузка и разделение документа"""
        loader = UnstructuredURLLoader(urls=[url])
        documents = loader.load()
        
        if not documents:
            raise ValueError("Документы не загружены. Проверьте URL или файл.")
            
        return self.text_splitter.split_documents(documents)