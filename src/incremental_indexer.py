"""
Incremental Indexing System
Only processes new/modified files for maximum efficiency
"""

import os
import json
import pickle
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime
import numpy as np
import faiss
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class FileRecord:
    """Record of a file's indexing state"""
    file_path: str
    filename: str
    size_bytes: int
    modified_time: float
    content_hash: str
    indexed_time: float
    embedding_index: int  # Position in FAISS index
    content_preview: str  # First 200 chars
    category: str
    word_count: int

class IncrementalIndexer:
    """Manages incremental document indexing with change detection"""
    
    def __init__(self, index_dir: str = "../data/index"):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # File tracking
        self.file_records: Dict[str, FileRecord] = {}
        self.file_records_path = self.index_dir / "file_records.json"
        
        # AI components
        print("🧠 Loading AI embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        
        # FAISS index
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        self.index_path = self.index_dir / "incremental_index.faiss"
        
        # Document storage
        self.documents = []
        self.documents_path = self.index_dir / "documents.pkl"
        
        # Load existing data
        self.load_existing_data()
        
        print(f"✅ Incremental Indexer ready!")
        print(f"   Tracked files: {len(self.file_records)}")
        print(f"   Indexed documents: {len(self.documents)}")
    
    def load_existing_data(self):
        """Load existing file records and index"""
        try:
            # Load file records
            if self.file_records_path.exists():
                with open(self.file_records_path, 'r') as f:
                    records_data = json.load(f)
                    self.file_records = {
                        path: FileRecord(**record_data) 
                        for path, record_data in records_data.items()
                    }
                print(f"📂 Loaded {len(self.file_records)} file records")
            
            # Load FAISS index
            if self.index_path.exists():
                self.index = faiss.read_index(str(self.index_path))
                print(f"📂 Loaded FAISS index with {self.index.ntotal} vectors")
            
            # Load documents
            if self.documents_path.exists():
                with open(self.documents_path, 'rb') as f:
                    self.documents = pickle.load(f)
                print(f"📂 Loaded {len(self.documents)} document records")
                
        except Exception as e:
            print(f"⚠️ Error loading existing data: {e}")
            print("   Starting with fresh index")
    
    def save_data(self):
        """Save file records and index to disk"""
        try:
            # Save file records
            records_data = {
                path: asdict(record) 
                for path, record in self.file_records.items()
            }
            with open(self.file_records_path, 'w') as f:
                json.dump(records_data, f, indent=2)
            
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save documents
            with open(self.documents_path, 'wb') as f:
                pickle.dump(self.documents, f)
            
            print(f"💾 Saved index data to {self.index_dir}")
            
        except Exception as e:
            print(f"❌ Error saving data: {e}")
    
    def calculate_file_hash(self, file_path: Path, sample_size: int = 8192) -> str:
        """Calculate hash of file content (using sample for large files)"""
        try:
            hasher = hashlib.md5()
            
            with open(file_path, 'rb') as f:
                # For large files, sample from beginning, middle, and end
                file_size = file_path.stat().st_size
                
                if file_size <= sample_size:
                    hasher.update(f.read())
                else:
                    # Beginning
                    hasher.update(f.read(sample_size // 3))
                    
                    # Middle
                    f.seek(file_size // 2)
                    hasher.update(f.read(sample_size // 3))
                    
                    # End
                    f.seek(max(0, file_size - sample_size // 3))
                    hasher.update(f.read(sample_size // 3))
            
            return hasher.hexdigest()
        except Exception as e:
            return f"error_{str(e)[:10]}"
    
    def needs_reindexing(self, file_path: Path) -> bool:
        """Check if file needs to be reindexed"""
        file_str = str(file_path)
        
        # New file
        if file_str not in self.file_records:
            return True
        
        record = self.file_records[file_str]
        
        try:
            stat = file_path.stat()
            
            # Check modification time
            if stat.st_mtime > record.modified_time:
                return True
            
            # Check file size
            if stat.st_size != record.size_bytes:
                return True
            
            # For critical files, check content hash
            current_hash = self.calculate_file_hash(file_path)
            if current_hash != record.content_hash:
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking {file_path}: {e}")
            return True  # Err on side of reindexing
    
    def create_embedding(self, text: str) -> np.ndarray:
        """Create embedding for text content"""
        try:
            embedding = self.embedding_model.encode([text])[0]
            return embedding.astype('float32')
        except Exception as e:
            print(f"❌ Error creating embedding: {e}")
            return None
    
    def index_single_file(self, file_path: Path, extractor) -> bool:
        """Index a single file"""
        try:
            # Extract content
            content_data = extractor.extract_content(str(file_path))
            if not content_data:
                return False
            
            content = content_data['content']
            
            # Create embedding
            embedding = self.create_embedding(content)
            if embedding is None:
                return False
            
            # Remove old record if exists
            file_str = str(file_path)
            if file_str in self.file_records:
                old_record = self.file_records[file_str]
                # Remove from FAISS index (mark as deleted)
                # Note: FAISS doesn't support deletion, so we'll track deleted indices separately
                print(f"  🔄 Updating existing file: {file_path.name}")
            else:
                print(f"  ➕ Adding new file: {file_path.name}")
            
            # Add to FAISS index
            embedding_reshaped = embedding.reshape(1, -1)
            self.index.add(embedding_reshaped)
            embedding_index = self.index.ntotal - 1
            
            # Create file record
            stat = file_path.stat()
            content_hash = self.calculate_file_hash(file_path)
            
            record = FileRecord(
                file_path=file_str,
                filename=file_path.name,
                size_bytes=stat.st_size,
                modified_time=stat.st_mtime,
                content_hash=content_hash,
                indexed_time=datetime.now().timestamp(),
                embedding_index=embedding_index,
                content_preview=content[:200],
                category=content_data.get('category', 'unknown'),
                word_count=content_data.get('word_count', 0)
            )
            
            self.file_records[file_str] = record
            
            # Store document data
            doc_data = content_data.copy()
            doc_data['embedding_index'] = embedding_index
            doc_data['indexed_time'] = record.indexed_time
            
            # Update or append to documents list
            # Find and replace if exists, otherwise append
            found_index = None
            for i, doc in enumerate(self.documents):
                if doc['file_path'] == file_str:
                    found_index = i
                    break
            
            if found_index is not None:
                self.documents[found_index] = doc_data
            else:
                self.documents.append(doc_data)
            
            return True
            
        except Exception as e:
            print(f"❌ Error indexing {file_path}: {e}")
            return False
    
    def incremental_index(self, files: List[Path], extractor, 
                         max_workers: int = 4, save_frequency: int = 10) -> Dict:
        """Perform incremental indexing of files"""
        
        print(f"🚀 Starting incremental indexing of {len(files)} files...")
        
        # Filter files that need reindexing
        files_to_process = []
        for file_path in files:
            if self.needs_reindexing(file_path):
                files_to_process.append(file_path)
        
        print(f"📊 Files analysis:")
        print(f"   Total files: {len(files)}")
        print(f"   Need processing: {len(files_to_process)}")
        print(f"   Already indexed: {len(files) - len(files_to_process)}")
        
        if not files_to_process:
            print("✅ All files are up to date!")
            return {
                'total_files': len(files),
                'processed': 0,
                'skipped': len(files),
                'errors': 0,
                'duration': 0
            }
        
        # Process files
        start_time = datetime.now()
        processed = 0
        errors = 0
        
        # Use thread pool for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.index_single_file, file_path, extractor): file_path
                for file_path in files_to_process
            }
            
            # Process completed tasks
            for i, future in enumerate(as_completed(future_to_file)):
                file_path = future_to_file[future]
                
                try:
                    success = future.result()
                    if success:
                        processed += 1
                    else:
                        errors += 1
                except Exception as e:
                    print(f"❌ Error processing {file_path}: {e}")
                    errors += 1
                
                # Progress update
                if (i + 1) % 10 == 0:
                    progress = (i + 1) / len(files_to_process) * 100
                    print(f"  📊 Progress: {progress:.1f}% ({i + 1}/{len(files_to_process)})")
                
                # Periodic save
                if (i + 1) % save_frequency == 0:
                    self.save_data()
                    print(f"  💾 Saved checkpoint at {i + 1} files")
        
        # Final save
        self.save_data()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Results summary
        results = {
            'total_files': len(files),
            'processed': processed,
            'skipped': len(files) - len(files_to_process),
            'errors': errors,
            'duration': duration
        }
        
        print(f"\n✅ Incremental indexing complete!")
        print(f"   ⏱️  Duration: {duration:.1f} seconds")
        print(f"   📄 Files processed: {processed}")
        print(f"   ⏭️  Files skipped: {results['skipped']}")
        print(f"   ❌ Errors: {errors}")
        
        if duration > 0:
            print(f"   🚀 Speed: {processed / duration:.1f} files/second")
        
        return results
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """Search indexed documents"""
        if not self.documents:
            print("⚠️ No documents indexed yet!")
            return []
        
        try:
            print(f"🔍 Searching for: '{query}'")
            
            # Create query embedding
            query_embedding = self.create_embedding(query)
            if query_embedding is None:
                return []
            
            # Search FAISS index
            query_reshaped = query_embedding.reshape(1, -1)
            scores, indices = self.index.search(
                query_reshaped, 
                min(top_k, self.index.ntotal)
            )
            
            # Prepare results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < len(self.documents):
                    result = self.documents[idx].copy()
                    result['similarity_score'] = float(score)
                    
                    # Add file record info if available
                    file_path = result['file_path']
                    if file_path in self.file_records:
                        record = self.file_records[file_path]
                        result['last_indexed'] = datetime.fromtimestamp(record.indexed_time).strftime("%Y-%m-%d %H:%M")
                        result['category'] = record.category
                    
                    results.append(result)
            
            print(f"✅ Found {len(results)} relevant documents")
            return results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def get_index_statistics(self) -> Dict:
        """Get statistics about the current index"""
        total_size = sum(record.size_bytes for record in self.file_records.values())
        
        # Group by category
        categories = {}
        for record in self.file_records.values():
            cat = record.category
            categories[cat] = categories.get(cat, 0) + 1
        
        # Recent activity
        week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)
        recent_files = sum(1 for record in self.file_records.values() 
                          if record.indexed_time > week_ago)
        
        return {
            'total_files': len(self.file_records),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'categories': categories,
            'recent_files_7_days': recent_files,
            'index_size': self.index.ntotal if hasattr(self, 'index') else 0,
            'index_directory': str(self.index_dir)
        }
    
    def cleanup_deleted_files(self) -> int:
        """Remove records for files that no longer exist"""
        deleted_count = 0
        files_to_remove = []
        
        for file_path, record in self.file_records.items():
            if not Path(file_path).exists():
                files_to_remove.append(file_path)
        
        for file_path in files_to_remove:
            del self.file_records[file_path]
            deleted_count += 1
        
        # Also clean up documents list
        self.documents = [
            doc for doc in self.documents 
            if Path(doc['file_path']).exists()
        ]
        
        if deleted_count > 0:
            self.save_data()
            print(f"🧹 Cleaned up {deleted_count} deleted files")
        
        return deleted_count

# Test the incremental indexer
if __name__ == "__main__":
    from document_extractor import EnhancedDocumentExtractor
    from filesystem_scanner import FilesystemScanner, ScanConfig
    
    print("🧪 Testing Incremental Indexer...")
    
    # Create components
    indexer = IncrementalIndexer()
    extractor = EnhancedDocumentExtractor()
    
    # Scan for files (limited for testing)
    config = ScanConfig(
        include_dirs=["../data/documents"],
        max_file_size_mb=5,
        parallel_processing=False
    )
    scanner = FilesystemScanner(config)
    files = scanner.scan_system()
    
    # Perform incremental indexing
    results = indexer.incremental_index(files, extractor, max_workers=2)
    
    # Show statistics
    stats = indexer.get_index_statistics()
    print(f"\n📊 Index Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test search
    if indexer.documents:
        test_queries = ["financial", "customer", "performance"]
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            results = indexer.search(query, top_k=3)
            
            for i, result in enumerate(results, 1):
                score = result.get('similarity_score', 0)
                filename = result.get('filename', 'unknown')
                print(f"   {i}. {filename} (score: {score:.3f})")