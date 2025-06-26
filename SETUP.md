# 🚀 Quick Setup Guide

## Prerequisites
- macOS (M1/M2/M3 optimized)
- Python 3.9+
- 16GB RAM recommended

## 1. Clone and Install
```bash
git clone https://github.com/yourusername/ai-file-assistant.git
cd ai-file-assistant
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 2. Run Dependency Check
```bash
cd src
python dependency_checker.py
```

## 3. Launch Application
```bash
streamlit run src/chat_app.py
```

## 4. First Time Setup
1. Open browser to `http://localhost:8501`
2. Click "🔍 Scan System Files" in sidebar
3. Wait for indexing to complete
4. Start searching!

## Troubleshooting

### Dependency Issues
If you get PyTorch or sentence-transformers errors:
```bash
# Option 1: Install full AI stack
pip install torch==2.1.0 sentence-transformers==2.2.2 faiss-cpu==1.7.4

# Option 2: Use lightweight mode
# Edit chat_app.py line 15:
# from lightweight_indexer import LightweightIndexer as IncrementalIndexer
```

### Permission Errors
- System respects macOS file permissions
- Some directories may be inaccessible (normal)
- Use "Custom Directory" feature for specific folders

### Performance Issues
- Reduce max file size in settings
- Limit directories to scan
- Use fewer worker threads

## Support
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📧 Email: your.email@example.com