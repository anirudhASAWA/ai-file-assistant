#!/usr/bin/env python3
"""
Simple AI Document Search - Working Version
"""

import sys
sys.path.append('src')
from src.document_extractor import DocumentExtractor
from src.content_indexer import ContentIndexer

def main():
    print("🚀 Local AI Document Search")
    print("=" * 40)
    
    # Load documents
    print("📚 Loading documents...")
    extractor = DocumentExtractor()
    documents = extractor.process_directory("data/documents")
    
    if not documents:
        print("❌ No documents found!")
        return
    
    # Create AI index
    print("\n🧠 Creating AI search index...")
    indexer = ContentIndexer()
    indexer.index_documents(documents)
    
    print("\n🎉 Setup complete! Now you can search...")
    print("💡 Try queries like:")
    print("   - 'financial results'")
    print("   - 'customer feedback'")
    print("   - 'market analysis'")
    print("   - 'team meeting notes'")
    print("\nType 'quit' to exit.\n")
    
    # Interactive search loop
    while True:
        query = input("🔍 Search query: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        if not query:
            continue
        
        # Search
        results = indexer.search(query, top_k=3)
        
        if not results:
            print("❌ No results found\n")
            continue
        
        print(f"\n📊 Results for '{query}':")
        print("-" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"\n{i}. 📄 {result['filename']}")
            print(f"   🎯 Relevance: {result['similarity_score']:.3f}")
            print(f"   📝 Preview: {result['content'][:150]}...")
            print(f"   📏 {result['word_count']} words")
        
        print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
