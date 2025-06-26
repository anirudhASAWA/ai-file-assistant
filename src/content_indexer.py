"""
Content Indexer with AI Embeddings
Creates searchable AI index of document content
"""

import numpy as np
import faiss
import pickle
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import List, Dict
import warnings

warnings.filterwarnings('ignore')

class ContentIndexer:
    """Creates AI-powered searchable index of documents"""
    
    def __init__(self):
        print("🧠 Loading AI embedding model...")
        
        # Load the AI model that understands text meaning
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384  # Size of AI embeddings
        
        # Initialize FAISS (Facebook AI Similarity Search)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.documents = []
        
        print("✅ AI model loaded and ready!")
    
    def create_embedding(self, text: str):
        """Convert text into AI embedding (meaning representation)"""
        try:
            # The AI model converts text to numbers that represent meaning
            embedding = self.embedding_model.encode([text])[0]
            return embedding
        except Exception as e:
            print(f"❌ Error creating embedding: {e}")
            return None
    
    def index_documents(self, documents_data: List[Dict]):
        """Process and index all documents with AI"""
        print(f"🚀 Creating AI index for {len(documents_data)} documents...")
        
        for i, doc_data in enumerate(documents_data):
            try:
                print(f"  🔄 Processing: {doc_data['filename']}")
                
                # Create AI embedding of the document content
                content = doc_data['content']
                embedding = self.create_embedding(content)
                
                if embedding is not None:
                    # Add to search index
                    embedding_reshaped = embedding.reshape(1, -1)
                    self.index.add(embedding_reshaped.astype('float32'))
                    
                    # Store document info
                    doc_data['embedding'] = embedding
                    self.documents.append(doc_data)
                    
                    print(f"    ✅ Indexed successfully")
                else:
                    print(f"    ❌ Failed to create embedding")
                    
            except Exception as e:
                print(f"❌ Error processing {doc_data['filename']}: {e}")
        
        print(f"🎉 Successfully indexed {len(self.documents)} documents!")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for documents using AI similarity"""
        if not self.documents:
            print("⚠️ No documents indexed yet!")
            return []
        
        try:
            print(f"🔍 Searching for: '{query}'")
            
            # Convert query to AI embedding
            query_embedding = self.create_embedding(query)
            if query_embedding is None:
                return []
            
            # Search for similar documents
            query_reshaped = query_embedding.reshape(1, -1)
            scores, indices = self.index.search(
                query_reshaped.astype('float32'), 
                min(top_k, len(self.documents))
            )
            
            # Prepare results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    result = self.documents[idx].copy()
                    result['similarity_score'] = float(score)
                    results.append(result)
            
            print(f"✅ Found {len(results)} relevant documents")
            return results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []

# Test the indexer
if __name__ == "__main__":
    from document_extractor import DocumentExtractor
    
    print("🧪 Testing AI Content Indexer...")
    
    # Load documents
    extractor = DocumentExtractor()
    docs = extractor.process_directory("../../data/documents")
    
    # Create AI index
    indexer = ContentIndexer()
    indexer.index_documents(docs)
    
    # Test search
    test_queries = [
        "financial performance",
        "customer satisfaction"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
        results = indexer.search(query, top_k=2)
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['filename']} (score: {result['similarity_score']:.3f})")

    def save_index(self, index_path: str):
        """Save the AI index to disk"""
        index_path = Path(index_path)
        index_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(index_path / "ai_index.faiss"))
            
            # Save documents (without embeddings to save space)
            docs_to_save = []
            for doc in self.documents:
                doc_copy = doc.copy()
                if 'embedding' in doc_copy:
                    del doc_copy['embedding']  # Remove large embedding data
                docs_to_save.append(doc_copy)
            
            with open(index_path / "documents.pkl", 'wb') as f:
                pickle.dump(docs_to_save, f)
            
            print(f"💾 AI index saved to {index_path}")
        except Exception as e:
            print(f"❌ Error saving index: {e}")
    
    def load_index(self, index_path: str) -> bool:
        """Load existing AI index"""
        index_path = Path(index_path)
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_path / "ai_index.faiss"))
            
            # Load documents
            with open(index_path / "documents.pkl", 'rb') as f:
                self.documents = pickle.load(f)
            
            print(f"📂 Loaded AI index: {len(self.documents)} documents")
            return True
        except Exception as e:
            print(f"❌ Error loading index: {e}")
            return False

    def save_index(self, index_path: str):
        """Save the AI index to disk"""
        index_path = Path(index_path)
        index_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save FAISS index
            faiss.write_index(self.index, str(index_path / "ai_index.faiss"))
            
            # Save documents (without embeddings to save space)
            docs_to_save = []
            for doc in self.documents:
                doc_copy = doc.copy()
                if 'embedding' in doc_copy:
                    del doc_copy['embedding']  # Remove large embedding data
                docs_to_save.append(doc_copy)
            
            with open(index_path / "documents.pkl", 'wb') as f:
                pickle.dump(docs_to_save, f)
            
            print(f"💾 AI index saved to {index_path}")
        except Exception as e:
            print(f"❌ Error saving index: {e}")
    
    def load_index(self, index_path: str) -> bool:
        """Load existing AI index"""
        index_path = Path(index_path)
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(str(index_path / "ai_index.faiss"))
            
            # Load documents
            with open(index_path / "documents.pkl", 'rb') as f:
                self.documents = pickle.load(f)
            
            print(f"📂 Loaded AI index: {len(self.documents)} documents")
            return True
        except Exception as e:
            print(f"❌ Error loading index: {e}")
            return False
