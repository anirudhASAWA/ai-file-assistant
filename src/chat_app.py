"""
Enhanced AI File Assistant Chat Interface
Full-featured web interface with system-wide search capabilities
"""

import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional

# Import our modules
from document_extractor import EnhancedDocumentExtractor
from filesystem_scanner import FilesystemScanner, ScanConfig
from incremental_indexer import IncrementalIndexer
from agentic_search_engine import AgenticSearchEngine

# Page configuration
st.set_page_config(
    page_title="AI File Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
}
.search-result {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #1f77b4;
}
.confidence-high { border-left-color: #28a745 !important; }
.confidence-medium { border-left-color: #ffc107 !important; }
.confidence-low { border-left-color: #dc3545 !important; }
.suggestion-box {
    background-color: #e3f2fd;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
    
    if 'indexer' not in st.session_state:
        st.session_state.indexer = None
    
    if 'search_engine' not in st.session_state:
        st.session_state.search_engine = None
    
    if 'extractor' not in st.session_state:
        st.session_state.extractor = None
    
    if 'scanner' not in st.session_state:
        st.session_state.scanner = None
    
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    
    if 'last_scan_time' not in st.session_state:
        st.session_state.last_scan_time = None
    
    if 'current_results' not in st.session_state:
        st.session_state.current_results = []

@st.cache_resource
def load_components():
    """Load and cache all AI components"""
    try:
        with st.spinner("🤖 Loading AI components..."):
            # Create components
            extractor = EnhancedDocumentExtractor()
            indexer = IncrementalIndexer()
            search_engine = AgenticSearchEngine(indexer)
            
            # Default scanner config
            config = ScanConfig(
                include_dirs=[
                    "~/Documents", "~/Desktop", "~/Downloads",
                    "~/Code", "~/Projects", "~/Work"
                ],
                max_file_size_mb=50,
                parallel_processing=True,
                max_workers=4
            )
            scanner = FilesystemScanner(config)
            
            return extractor, indexer, search_engine, scanner
    except Exception as e:
        st.error(f"Error loading components: {e}")
        return None, None, None, None

def setup_sidebar():
    """Setup the sidebar with controls and information"""
    st.sidebar.title("🤖 AI File Assistant")
    
    # System status
    st.sidebar.subheader("📊 System Status")
    
    if st.session_state.indexer:
        stats = st.session_state.indexer.get_index_statistics()
        st.sidebar.metric("Indexed Files", stats['total_files'])
        st.sidebar.metric("Total Size", f"{stats['total_size_mb']} MB")
        st.sidebar.metric("Recent Files (7d)", stats['recent_files_7_days'])
        
        # Categories breakdown
        if stats['categories']:
            st.sidebar.subheader("📁 File Categories")
            for category, count in stats['categories'].items():
                st.sidebar.text(f"{category}: {count}")
    
    # Indexing controls
    st.sidebar.subheader("⚙️ Index Management")
    
    # Scan directories
    if st.sidebar.button("🔍 Scan System Files", type="primary"):
        perform_system_scan()
    
    # Quick scan for recent files
    if st.sidebar.button("⚡ Quick Scan (Recent Only)"):
        perform_quick_scan()
    
    # Manual directory input
    st.sidebar.subheader("📂 Custom Directory")
    custom_dir = st.sidebar.text_input("Directory path:", placeholder="~/Documents")
    if st.sidebar.button("📁 Scan Directory"):
        if custom_dir:
            scan_custom_directory(custom_dir)
    
    # Advanced settings
    with st.sidebar.expander("🔧 Advanced Settings"):
        max_file_size = st.slider("Max file size (MB)", 1, 100, 50)
        parallel_processing = st.checkbox("Parallel processing", True)
        max_workers = st.slider("Worker threads", 1, 8, 4)
        
        if st.button("Update Settings"):
            update_scanner_config(max_file_size, parallel_processing, max_workers)
    
    # Index info
    st.sidebar.subheader("ℹ️ Last Scan")
    if st.session_state.last_scan_time:
        time_ago = datetime.now() - st.session_state.last_scan_time
        st.sidebar.text(f"{time_ago.seconds // 60} minutes ago")
    else:
        st.sidebar.text("Never")
    
    # Cleanup
    if st.sidebar.button("🧹 Cleanup Deleted Files"):
        cleanup_index()

def perform_system_scan():
    """Perform full system scan"""
    try:
        with st.spinner("🔍 Scanning system for files..."):
            # Progress placeholder
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(file_count, current_dir):
                status_text.text(f"Found {file_count} files... scanning {current_dir.name}")
            
            # Scan files
            files = st.session_state.scanner.scan_system(progress_callback=progress_callback)
            progress_bar.progress(50)
            
            # Incremental indexing
            status_text.text("Indexing files...")
            results = st.session_state.indexer.incremental_index(
                files, st.session_state.extractor, max_workers=4
            )
            progress_bar.progress(100)
            
            st.session_state.last_scan_time = datetime.now()
            
            # Show results
            st.success(f"✅ Scan complete!")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Files Found", len(files))
            with col2:
                st.metric("Files Processed", results['processed'])
            with col3:
                st.metric("Files Skipped", results['skipped'])
            
            progress_bar.empty()
            status_text.empty()
            
    except Exception as e:
        st.error(f"Error during scan: {e}")

def perform_quick_scan():
    """Perform quick scan of recently modified files"""
    try:
        with st.spinner("⚡ Quick scanning recent files..."):
            # Scan only key directories
            config = ScanConfig(
                include_dirs=["~/Documents", "~/Desktop", "~/Downloads"],
                max_file_size_mb=20,
                parallel_processing=True,
                max_workers=2
            )
            quick_scanner = FilesystemScanner(config)
            
            files = quick_scanner.scan_system()
            
            # Filter to recent files (last 7 days)
            recent_files = quick_scanner.filter_by_date(files, days_back=7)
            
            if recent_files:
                results = st.session_state.indexer.incremental_index(
                    recent_files, st.session_state.extractor, max_workers=2
                )
                st.success(f"✅ Quick scan: {results['processed']} recent files processed")
            else:
                st.info("No recent files found to index")
                
    except Exception as e:
        st.error(f"Error during quick scan: {e}")

def scan_custom_directory(directory_path: str):
    """Scan a custom directory"""
    try:
        expanded_path = Path(directory_path).expanduser()
        if not expanded_path.exists():
            st.error(f"Directory not found: {directory_path}")
            return
        
        with st.spinner(f"📁 Scanning {directory_path}..."):
            config = ScanConfig(
                include_dirs=[directory_path],
                max_file_size_mb=50,
                parallel_processing=True
            )
            custom_scanner = FilesystemScanner(config)
            files = custom_scanner.scan_system()
            
            if files:
                results = st.session_state.indexer.incremental_index(
                    files, st.session_state.extractor
                )
                st.success(f"✅ Scanned {directory_path}: {results['processed']} files processed")
            else:
                st.warning(f"No supported files found in {directory_path}")
                
    except Exception as e:
        st.error(f"Error scanning directory: {e}")

def update_scanner_config(max_file_size: int, parallel: bool, workers: int):
    """Update scanner configuration"""
    config = ScanConfig(
        max_file_size_mb=max_file_size,
        parallel_processing=parallel,
        max_workers=workers
    )
    st.session_state.scanner = FilesystemScanner(config)
    st.success("Settings updated!")

def cleanup_index():
    """Clean up deleted files from index"""
    try:
        with st.spinner("🧹 Cleaning up deleted files..."):
            deleted_count = st.session_state.indexer.cleanup_deleted_files()
            if deleted_count > 0:
                st.success(f"✅ Cleaned up {deleted_count} deleted files")
            else:
                st.info("No deleted files found")
    except Exception as e:
        st.error(f"Error during cleanup: {e}")

def display_search_results(results: List, query: str):
    """Display search results with enhanced formatting"""
    if not results:
        st.warning("No relevant files found. Try a different search term or scan more directories.")
        return
    
    st.subheader(f"🔍 Found {len(results)} results for '{query}'")
    
    for i, result in enumerate(results):
        # Determine confidence level for styling
        confidence = result.confidence
        if confidence >= 0.8:
            confidence_class = "confidence-high"
            confidence_emoji = "🟢"
        elif confidence >= 0.6:
            confidence_class = "confidence-medium"
            confidence_emoji = "🟡"
        else:
            confidence_class = "confidence-low"
            confidence_emoji = "🔴"
        
        # Create result container
        with st.container():
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"""
                <div class="search-result {confidence_class}">
                    <h4>{confidence_emoji} {result.filename}</h4>
                    <p><strong>Relevance:</strong> {result.relevance_explanation}</p>
                    <p><strong>Category:</strong> {result.category} | 
                       <strong>Size:</strong> {result.file_size_mb:.2f} MB | 
                       <strong>Modified:</strong> {result.last_modified}</p>
                    <p><strong>Preview:</strong> {result.content_preview}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.metric("Confidence", f"{confidence:.1%}")
                
                # Action buttons
                if st.button(f"📁 Open", key=f"open_{i}"):
                    try:
                        import subprocess
                        subprocess.run(["open", result.file_path])
                        # Track file access
                        st.session_state.search_engine.update_file_access(result.file_path)
                    except Exception as e:
                        st.error(f"Error opening file: {e}")
                
                if st.button(f"📍 Show Location", key=f"location_{i}"):
                    st.info(f"📍 {result.file_path}")

def display_file_suggestions():
    """Display proactive file suggestions"""
    if st.session_state.search_engine and st.session_state.indexer.documents:
        suggestions = st.session_state.search_engine.suggest_files()
        
        if suggestions:
            st.markdown("""
            <div class="suggestion-box">
                <h4>💡 Suggested Files</h4>
                <p>Based on your recent activity and current time</p>
            </div>
            """, unsafe_allow_html=True)
            
            cols = st.columns(min(3, len(suggestions)))
            for i, suggestion in enumerate(suggestions[:3]):
                with cols[i]:
                    if st.button(f"📄 {suggestion.filename}", key=f"suggest_{i}"):
                        # Open suggested file
                        try:
                            import subprocess
                            subprocess.run(["open", suggestion.file_path])
                            st.session_state.search_engine.update_file_access(suggestion.file_path)
                        except Exception as e:
                            st.error(f"Error opening file: {e}")

def display_analytics():
    """Display search analytics"""
    if st.session_state.search_engine:
        analytics = st.session_state.search_engine.get_search_analytics()
        
        if analytics.get('total_searches', 0) > 0:
            st.subheader("📈 Search Analytics")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Searches", analytics['total_searches'])
            with col2:
                st.metric("Recent Searches (7d)", analytics['searches_last_7_days'])
            with col3:
                st.metric("Avg Results/Search", f"{analytics['avg_results_per_search']:.1f}")
            
            # Most common intents
            if analytics.get('most_common_intents'):
                st.subheader("🎯 Search Patterns")
                for intent, count in list(analytics['most_common_intents'].items())[:5]:
                    st.text(f"{intent}: {count} times")
            
            # Most accessed files
            if analytics.get('most_accessed_files'):
                st.subheader("📊 Most Accessed Files")
                for file_info in analytics['most_accessed_files'][:5]:
                    filename = Path(file_info['file']).name
                    st.text(f"{filename}: {file_info['access_count']} times")

def main():
    """Main application function"""
    # Initialize
    initialize_session_state()
    
    # Load components if not already loaded
    if not st.session_state.initialized:
        components = load_components()
        if all(components):
            st.session_state.extractor, st.session_state.indexer, st.session_state.search_engine, st.session_state.scanner = components
            st.session_state.initialized = True
        else:
            st.error("Failed to load AI components. Please check your installation.")
            return
    
    # Setup sidebar
    setup_sidebar()
    
    # Main content area
    st.markdown('<h1 class="main-header">🤖 AI File Assistant</h1>', unsafe_allow_html=True)
    
    # Status indicators
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.session_state.indexer and st.session_state.indexer.documents:
            st.success("✅ AI Ready")
        else:
            st.warning("⚠️ No Files Indexed")
    
    with col2:
        if st.session_state.last_scan_time:
            time_diff = datetime.now() - st.session_state.last_scan_time
            if time_diff.total_seconds() < 3600:  # Less than 1 hour
                st.success("✅ Recently Scanned")
            else:
                st.warning("⚠️ Scan Outdated")
        else:
            st.error("❌ Never Scanned")
    
    with col3:
        if st.session_state.indexer:
            stats = st.session_state.indexer.get_index_statistics()
            if stats['total_files'] > 0:
                st.info(f"📚 {stats['total_files']} Files")
            else:
                st.warning("📚 0 Files")
    
    with col4:
        if st.session_state.search_engine:
            analytics = st.session_state.search_engine.get_search_analytics()
            search_count = analytics.get('total_searches', 0)
            st.info(f"🔍 {search_count} Searches")
    
    # Main search interface
    st.subheader("🔍 Search Your Files")
    
    # Search input with suggestions
    search_query = st.text_input(
        "What are you looking for?",
        placeholder="e.g., 'recent financial reports', 'project meeting notes', 'customer feedback'",
        help="Use natural language to describe what you're looking for. Be specific for better results!"
    )
    
    # Search options
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_button = st.button("🔍 Search", type="primary", disabled=not search_query.strip())
    with col2:
        max_results = st.selectbox("Max Results", [5, 10, 20, 50], index=1)
    with col3:
        include_suggestions = st.checkbox("Smart Suggestions", value=True)
    
    # Quick search buttons
    st.subheader("⚡ Quick Searches")
    quick_search_cols = st.columns(4)
    
    quick_searches = [
        ("📊 Recent Reports", "recent reports financial data"),
        ("📝 Meeting Notes", "meeting notes agenda minutes"),
        ("💼 Project Files", "project status updates deliverables"),
        ("📧 Communications", "email correspondence communication")
    ]
    
    for i, (label, query) in enumerate(quick_searches):
        with quick_search_cols[i]:
            if st.button(label, key=f"quick_{i}"):
                search_query = query
                search_button = True
    
    # Perform search
    if search_button and search_query.strip():
        with st.spinner("🤖 AI is searching your files..."):
            try:
                # Record search start time
                search_start = time.time()
                
                # Perform search
                results = st.session_state.search_engine.search(
                    search_query, 
                    top_k=max_results
                )
                
                # Record search time
                search_time = time.time() - search_start
                
                # Store results and query
                st.session_state.current_results = results
                st.session_state.search_history.append({
                    'query': search_query,
                    'timestamp': datetime.now(),
                    'results_count': len(results),
                    'search_time': search_time
                })
                
                # Display results
                st.success(f"✅ Search completed in {search_time:.2f} seconds")
                display_search_results(results, search_query)
                
            except Exception as e:
                st.error(f"Search error: {e}")
    
    # Display current results if any
    elif st.session_state.current_results:
        st.subheader("📋 Previous Search Results")
        if st.session_state.search_history:
            last_search = st.session_state.search_history[-1]
            st.info(f"Results for: '{last_search['query']}'")
        display_search_results(st.session_state.current_results, "")
    
    # File suggestions section
    if include_suggestions and st.session_state.search_engine:
        st.markdown("---")
        display_file_suggestions()
    
    # Analytics section
    if st.session_state.search_engine:
        with st.expander("📈 Search Analytics & Insights"):
            display_analytics()
    
    # Quick actions section
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    
    action_cols = st.columns(4)
    with action_cols[0]:
        if st.button("🔄 Refresh Index"):
            perform_quick_scan()
    
    with action_cols[1]:
        if st.button("📊 Show All Categories"):
            if st.session_state.indexer:
                stats = st.session_state.indexer.get_index_statistics()
                if stats['categories']:
                    st.json(stats['categories'])
    
    with action_cols[2]:
        if st.button("📁 Browse Recent Files"):
            # Show recently indexed files
            if st.session_state.indexer and st.session_state.indexer.documents:
                recent_docs = sorted(
                    st.session_state.indexer.documents,
                    key=lambda x: x.get('indexed_time', 0),
                    reverse=True
                )[:10]
                
                st.subheader("📅 Recently Indexed Files")
                for doc in recent_docs:
                    filename = Path(doc['file_path']).name
                    category = doc.get('category', 'unknown')
                    size_mb = doc.get('metadata', {}).get('size_mb', 0)
                    st.text(f"📄 {filename} ({category}, {size_mb:.1f}MB)")
    
    with action_cols[3]:
        if st.button("🎯 Smart Suggestions"):
            # Force refresh suggestions
            if st.session_state.search_engine:
                current_hour = datetime.now().hour
                if 9 <= current_hour <= 17:
                    context_hint = "work meeting project"
                else:
                    context_hint = "personal notes learning"
                
                suggestions = st.session_state.search_engine.suggest_files(context_hint)
                if suggestions:
                    st.subheader("💡 AI File Suggestions")
                    for suggestion in suggestions:
                        st.text(f"📄 {suggestion.filename} - {suggestion.relevance_explanation}")
    
    # Footer with tips
    st.markdown("---")
    with st.expander("💡 Tips for Better Searches"):
        st.markdown("""
        **🎯 Search Tips:**
        - Use natural language: "recent financial reports" instead of just "finance"
        - Be specific about time: "this week's meeting notes"
        - Mention file types: "Excel data", "PDF documents", "code files"
        - Use context: "project budget for Q4", "customer feedback analysis"
        
        **🚀 Features:**
        - **Smart Ranking**: AI understands context and ranks results intelligently
        - **Query Expansion**: Automatically finds related terms and concepts
        - **File Suggestions**: Proactive recommendations based on your work patterns
        - **Incremental Indexing**: Only processes new/changed files for speed
        
        **⚙️ System Status:**
        - Index covers your Documents, Desktop, Downloads, and project folders
        - Files larger than 50MB are skipped for performance
        - Search index updates automatically when you scan directories
        """)
    
    # Debug information (only in development)
    if st.checkbox("🔧 Show Debug Info"):
        st.subheader("🛠️ Debug Information")
        
        if st.session_state.indexer:
            debug_stats = st.session_state.indexer.get_index_statistics()
            st.json(debug_stats)
        
        if st.session_state.search_history:
            st.subheader("Search History")
            for i, search in enumerate(st.session_state.search_history[-5:]):
                st.text(f"{i+1}. {search['query']} ({search['results_count']} results)")

if __name__ == "__main__":
    main()