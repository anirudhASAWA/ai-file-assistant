"""
Enhanced Document Extractor with Multi-Format Support
Supports: TXT, PDF, DOCX, XLSX, CSV, MD, Code files, and more
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Optional, Set
import mimetypes
from datetime import datetime

# Import libraries with graceful fallbacks
try:
    import fitz  # PyMuPDF (better PDF handling)
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PDF support not available. Install: pip install PyMuPDF")

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("⚠️ DOCX support not available. Install: pip install python-docx")

try:
    import pandas as pd
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    print("⚠️ Excel support not available. Install: pip install pandas openpyxl")

class EnhancedDocumentExtractor:
    """Advanced document extractor supporting multiple file formats"""
    
    def __init__(self):
        # Define supported file types
        self.text_formats = {'.txt', '.md', '.rst', '.log'}
        self.code_formats = {'.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.ts', '.jsx', '.vue'}
        self.data_formats = {'.json', '.xml', '.yaml', '.yml', '.csv', '.tsv'}
        self.doc_formats = {'.pdf', '.docx', '.doc'}
        self.excel_formats = {'.xlsx', '.xls', '.xlsm'}
        
        self.supported_formats = (
            self.text_formats | self.code_formats | self.data_formats | 
            self.doc_formats | self.excel_formats
        )
        
        print(f"📄 Enhanced Document Extractor ready!")
        print(f"   Supports {len(self.supported_formats)} file types")
        if not PDF_AVAILABLE:
            print("   ⚠️ PDF support disabled (install PyMuPDF)")
        if not DOCX_AVAILABLE:
            print("   ⚠️ DOCX support disabled (install python-docx)")
        if not EXCEL_AVAILABLE:
            print("   ⚠️ Excel support disabled (install pandas openpyxl)")
    
    def get_file_metadata(self, file_path: Path) -> Dict:
        """Extract file metadata"""
        try:
            stat = file_path.stat()
            return {
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'extension': file_path.suffix.lower(),
                'mime_type': mimetypes.guess_type(str(file_path))[0] or 'unknown'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def extract_txt_content(self, file_path: Path) -> str:
        """Extract content from text files"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read().strip()
                        print(f"  ✅ Read {len(content)} characters (encoding: {encoding})")
                        return content
                except UnicodeDecodeError:
                    continue
            
            print(f"  ❌ Could not decode file with any encoding")
            return ""
        except Exception as e:
            print(f"  ❌ Error reading text file: {e}")
            return ""
    
    def extract_pdf_content(self, file_path: Path) -> str:
        """Extract content from PDF files"""
        if not PDF_AVAILABLE:
            print("  ❌ PDF support not available")
            return ""
        
        try:
            doc = fitz.open(str(file_path))
            text_content = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                text_content.append(text)
            
            doc.close()
            content = '\n\n'.join(text_content).strip()
            print(f"  ✅ Extracted {len(content)} characters from {len(text_content)} pages")
            return content
        except Exception as e:
            print(f"  ❌ Error reading PDF: {e}")
            return ""
    
    def extract_docx_content(self, file_path: Path) -> str:
        """Extract content from Word documents"""
        if not DOCX_AVAILABLE:
            print("  ❌ DOCX support not available")
            return ""
        
        try:
            doc = Document(str(file_path))
            paragraphs = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text.strip())
            
            content = '\n\n'.join(paragraphs)
            print(f"  ✅ Extracted {len(content)} characters from {len(paragraphs)} paragraphs")
            return content
        except Exception as e:
            print(f"  ❌ Error reading DOCX: {e}")
            return ""
    
    def extract_excel_content(self, file_path: Path) -> str:
        """Extract content from Excel files"""
        if not EXCEL_AVAILABLE:
            print("  ❌ Excel support not available")
            return ""
        
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(str(file_path))
            all_content = []
            
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(str(file_path), sheet_name=sheet_name)
                    
                    # Convert to text representation
                    sheet_content = f"Sheet: {sheet_name}\n"
                    sheet_content += f"Columns: {', '.join(df.columns.astype(str))}\n"
                    
                    # Sample of data (first few rows)
                    for idx, row in df.head(10).iterrows():
                        row_text = ', '.join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                        sheet_content += f"Row {idx + 1}: {row_text}\n"
                    
                    if len(df) > 10:
                        sheet_content += f"... and {len(df) - 10} more rows\n"
                    
                    all_content.append(sheet_content)
                except Exception as e:
                    all_content.append(f"Sheet: {sheet_name} - Error reading: {e}")
            
            content = '\n\n'.join(all_content)
            print(f"  ✅ Extracted content from {len(excel_file.sheet_names)} sheets")
            return content
        except Exception as e:
            print(f"  ❌ Error reading Excel file: {e}")
            return ""
    
    def extract_csv_content(self, file_path: Path) -> str:
        """Extract content from CSV files"""
        try:
            # Try to detect delimiter
            with open(file_path, 'r', encoding='utf-8') as file:
                sample = file.read(1024)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
            
            # Read CSV
            df = pd.read_csv(str(file_path), delimiter=delimiter, nrows=100)  # Limit rows for performance
            
            content = f"CSV File: {file_path.name}\n"
            content += f"Columns ({len(df.columns)}): {', '.join(df.columns.astype(str))}\n"
            content += f"Rows: {len(df)} (showing first 10)\n\n"
            
            # Add sample data
            for idx, row in df.head(10).iterrows():
                row_text = ', '.join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                content += f"Row {idx + 1}: {row_text}\n"
            
            print(f"  ✅ Extracted CSV with {len(df.columns)} columns, {len(df)} rows")
            return content
        except Exception as e:
            print(f"  ❌ Error reading CSV: {e}")
            return ""
    
    def extract_json_content(self, file_path: Path) -> str:
        """Extract content from JSON files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            # Convert JSON to readable text
            if isinstance(data, dict):
                content = f"JSON Object with keys: {', '.join(data.keys())}\n"
                content += json.dumps(data, indent=2, ensure_ascii=False)[:2000]  # Limit size
            elif isinstance(data, list):
                content = f"JSON Array with {len(data)} items\n"
                content += json.dumps(data[:10], indent=2, ensure_ascii=False)[:2000]  # First 10 items
            else:
                content = str(data)
            
            print(f"  ✅ Extracted JSON content ({len(content)} characters)")
            return content
        except Exception as e:
            print(f"  ❌ Error reading JSON: {e}")
            return ""
    
    def extract_content(self, file_path: str) -> Optional[Dict]:
        """Extract content from any supported file"""
        file_path = Path(file_path)
        extension = file_path.suffix.lower()
        
        print(f"📖 Processing: {file_path.name}")
        
        # Get file metadata
        metadata = self.get_file_metadata(file_path)
        
        # Skip large files (>50MB) for performance
        if metadata.get('size_mb', 0) > 50:
            print(f"  ⚠️ Skipping large file ({metadata['size_mb']}MB)")
            return None
        
        # Extract content based on file type
        content = ""
        
        if extension in self.text_formats or extension in self.code_formats:
            content = self.extract_txt_content(file_path)
        elif extension == '.pdf':
            content = self.extract_pdf_content(file_path)
        elif extension in {'.docx', '.doc'}:
            content = self.extract_docx_content(file_path)
        elif extension in self.excel_formats:
            content = self.extract_excel_content(file_path)
        elif extension in {'.csv', '.tsv'}:
            content = self.extract_csv_content(file_path)
        elif extension == '.json':
            content = self.extract_json_content(file_path)
        else:
            print(f"  ⚠️ File type {extension} not supported")
            return None
        
        if not content:
            return None
        
        # Determine content category
        if extension in self.code_formats:
            category = 'code'
        elif extension in self.doc_formats:
            category = 'document'
        elif extension in self.excel_formats or extension in {'.csv', '.tsv'}:
            category = 'data'
        elif extension == '.json':
            category = 'data'
        else:
            category = 'text'
        
        return {
            'file_path': str(file_path),
            'filename': file_path.name,
            'content': content,
            'word_count': len(content.split()),
            'char_count': len(content),
            'category': category,
            'metadata': metadata
        }
    
    def process_directory(self, directory_path: str, recursive: bool = True) -> List[Dict]:
        """Process all supported files in a directory"""
        directory_path = Path(directory_path)
        results = []
        
        print(f"🔍 Scanning: {directory_path}")
        print(f"   Recursive: {recursive}")
        
        # Define patterns to skip
        skip_patterns = {
            '.git', '__pycache__', 'node_modules', '.DS_Store', 
            'venv', '.venv', 'env', '.env', '.cache', 'cache'
        }
        
        def should_skip(path: Path) -> bool:
            return any(pattern in str(path) for pattern in skip_patterns)
        
        # Collect files to process
        files_to_process = []
        
        if recursive:
            for file_path in directory_path.rglob('*'):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in self.supported_formats and
                    not should_skip(file_path)):
                    files_to_process.append(file_path)
        else:
            for file_path in directory_path.iterdir():
                if (file_path.is_file() and 
                    file_path.suffix.lower() in self.supported_formats and
                    not should_skip(file_path)):
                    files_to_process.append(file_path)
        
        print(f"   Found {len(files_to_process)} files to process")
        
        # Process files
        for file_path in files_to_process:
            content_data = self.extract_content(file_path)
            if content_data:
                results.append(content_data)
        
        print(f"🎉 Successfully processed {len(results)} documents")
        
        # Print summary by category
        categories = {}
        for doc in results:
            cat = doc.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
        
        print("📊 Processing Summary:")
        for category, count in categories.items():
            print(f"   {category}: {count} files")
        
        return results

# Test function
if __name__ == "__main__":
    print("🧪 Testing Enhanced Document Extractor...")
    
    extractor = EnhancedDocumentExtractor()
    
    # Test with your documents directory
    docs = extractor.process_directory("../data/documents")
    
    for doc in docs:
        print(f"\n📄 {doc['filename']} ({doc['category']})")
        print(f"   Size: {doc['char_count']} chars, {doc['word_count']} words")
        print(f"   Preview: {doc['content'][:150]}...")