"""
System-Wide Filesystem Scanner
Intelligently scans Mac filesystem for relevant documents
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Set, Optional
from datetime import datetime, timedelta
import concurrent.futures
from dataclasses import dataclass
import threading

@dataclass
class ScanConfig:
    """Configuration for filesystem scanning"""
    # Directories to include (will expand ~ to user home)
    include_dirs: List[str] = None
    
    # Directories to exclude
    exclude_dirs: Set[str] = None
    
    # File patterns to skip
    skip_patterns: Set[str] = None
    
    # Maximum file size (MB)
    max_file_size_mb: int = 50
    
    # Maximum files per directory
    max_files_per_dir: int = 1000
    
    # Enable parallel processing
    parallel_processing: bool = True
    
    # Number of worker threads
    max_workers: int = 4
    
    def __post_init__(self):
        if self.include_dirs is None:
            self.include_dirs = [
                "~/Documents",
                "~/Desktop", 
                "~/Downloads",
                "~/Code",
                "~/Projects",
                "~/Work",
                "~/Development"
            ]
        
        if self.exclude_dirs is None:
            self.exclude_dirs = {
                # System directories
                "/System", "/Library", "/private", "/usr", "/bin", "/sbin",
                "/var", "/tmp", "/dev", "/proc",
                
                # User system directories  
                "Library/Caches", "Library/Logs", "Library/Application Support",
                ".Trash", ".cache", ".local",
                
                # Development artifacts
                "node_modules", "__pycache__", ".git", ".svn", ".hg",
                "venv", ".venv", "env", ".env", "virtualenv",
                "build", "dist", "target", "bin", "obj",
                
                # IDE and editor files
                ".vscode", ".idea", ".eclipse", ".settings",
                
                # OS files
                ".DS_Store", ".localized", "Thumbs.db"
            }
        
        if self.skip_patterns is None:
            self.skip_patterns = {
                # Temporary files
                "*.tmp", "*.temp", "*.bak", "*.swp", "*.lock",
                
                # System files
                "*.dylib", "*.so", "*.dll", "*.exe",
                
                # Media files (too large/not text-searchable)
                "*.mp4", "*.avi", "*.mov", "*.mp3", "*.wav", "*.flac",
                "*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.tiff",
                
                # Archive files
                "*.zip", "*.tar", "*.gz", "*.rar", "*.7z",
                
                # Database files
                "*.db", "*.sqlite", "*.sqlite3"
            }

class FilesystemScanner:
    """Intelligent filesystem scanner for Mac"""
    
    def __init__(self, config: ScanConfig = None):
        self.config = config or ScanConfig()
        self.scan_stats = {
            'directories_scanned': 0,
            'files_found': 0,
            'files_processed': 0,
            'files_skipped': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        self._stop_scanning = False
        
    def expand_user_paths(self, paths: List[str]) -> List[Path]:
        """Expand user paths like ~/Documents"""
        expanded = []
        for path_str in paths:
            try:
                path = Path(path_str).expanduser().resolve()
                if path.exists() and path.is_dir():
                    expanded.append(path)
                else:
                    print(f"⚠️ Directory not found: {path}")
            except Exception as e:
                print(f"⚠️ Invalid path {path_str}: {e}")
        return expanded
    
    def should_skip_directory(self, dir_path: Path) -> bool:
        """Check if directory should be skipped"""
        dir_str = str(dir_path)
        dir_name = dir_path.name
        
        # Check exclude patterns
        for exclude_pattern in self.config.exclude_dirs:
            if exclude_pattern in dir_str or exclude_pattern == dir_name:
                return True
        
        # Skip hidden directories (starting with .)
        if dir_name.startswith('.') and dir_name not in {'.', '..'}:
            return True
        
        # Skip very deep directory structures (likely not user content)
        if len(dir_path.parts) > 10:
            return True
        
        return False
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        # Check file size
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            if size_mb > self.config.max_file_size_mb:
                return True
        except:
            return True
        
        # Check skip patterns
        filename = file_path.name.lower()
        for pattern in self.config.skip_patterns:
            if pattern.startswith('*'):
                suffix = pattern[1:]
                if filename.endswith(suffix):
                    return True
            elif pattern in filename:
                return True
        
        # Skip hidden files
        if filename.startswith('.'):
            return True
        
        return False
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> List[Path]:
        """Scan a single directory for relevant files"""
        files_found = []
        
        try:
            if self.should_skip_directory(directory):
                return files_found
            
            self.scan_stats['directories_scanned'] += 1
            
            # Get directory contents
            try:
                items = list(directory.iterdir())
            except PermissionError:
                print(f"⚠️ Permission denied: {directory}")
                return files_found
            
            # Process files in current directory
            files_in_dir = 0
            for item in items:
                if self._stop_scanning:
                    break
                
                if item.is_file():
                    if not self.should_skip_file(item):
                        files_found.append(item)
                        files_in_dir += 1
                        
                        # Limit files per directory for performance
                        if files_in_dir >= self.config.max_files_per_dir:
                            print(f"⚠️ Too many files in {directory}, limiting to {self.config.max_files_per_dir}")
                            break
                
                elif item.is_dir() and recursive:
                    # Recursively scan subdirectories
                    subdirectory_files = self.scan_directory(item, recursive=True)
                    files_found.extend(subdirectory_files)
            
            self.scan_stats['files_found'] += len(files_found)
            
        except Exception as e:
            print(f"❌ Error scanning {directory}: {e}")
            self.scan_stats['errors'] += 1
        
        return files_found
    
    def scan_system(self, progress_callback=None) -> List[Path]:
        """Scan entire system for relevant files"""
        print("🔍 Starting system-wide file scan...")
        
        self.scan_stats['start_time'] = datetime.now()
        self._stop_scanning = False
        
        # Expand include directories
        include_dirs = self.expand_user_paths(self.config.include_dirs)
        print(f"📂 Scanning {len(include_dirs)} directories:")
        for dir_path in include_dirs:
            print(f"   • {dir_path}")
        
        all_files = []
        
        if self.config.parallel_processing:
            # Parallel directory scanning
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                future_to_dir = {
                    executor.submit(self.scan_directory, dir_path): dir_path 
                    for dir_path in include_dirs
                }
                
                for future in concurrent.futures.as_completed(future_to_dir):
                    directory = future_to_dir[future]
                    try:
                        files = future.result()
                        all_files.extend(files)
                        
                        if progress_callback:
                            progress_callback(len(all_files), directory)
                            
                    except Exception as e:
                        print(f"❌ Error processing {directory}: {e}")
                        self.scan_stats['errors'] += 1
        else:
            # Sequential scanning
            for dir_path in include_dirs:
                if self._stop_scanning:
                    break
                
                files = self.scan_directory(dir_path)
                all_files.extend(files)
                
                if progress_callback:
                    progress_callback(len(all_files), dir_path)
        
        self.scan_stats['end_time'] = datetime.now()
        self.scan_stats['files_found'] = len(all_files)
        
        print(f"✅ Scan complete! Found {len(all_files)} files")
        self.print_scan_summary()
        
        return all_files
    
    def print_scan_summary(self):
        """Print scanning statistics"""
        duration = (self.scan_stats['end_time'] - self.scan_stats['start_time']).total_seconds()
        
        print("\n📊 Scan Summary:")
        print(f"   ⏱️  Duration: {duration:.1f} seconds")
        print(f"   📁 Directories scanned: {self.scan_stats['directories_scanned']}")
        print(f"   📄 Files found: {self.scan_stats['files_found']}")
        print(f"   ❌ Errors: {self.scan_stats['errors']}")
        
        if duration > 0:
            print(f"   🚀 Speed: {self.scan_stats['files_found'] / duration:.1f} files/second")
    
    def stop_scan(self):
        """Stop the current scan"""
        self._stop_scanning = True
        print("🛑 Stopping scan...")
    
    def filter_by_date(self, files: List[Path], days_back: int = 30) -> List[Path]:
        """Filter files by modification date"""
        cutoff_date = datetime.now() - timedelta(days=days_back)
        recent_files = []
        
        for file_path in files:
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime > cutoff_date:
                    recent_files.append(file_path)
            except:
                continue
        
        print(f"📅 Found {len(recent_files)} files modified in last {days_back} days")
        return recent_files
    
    def group_by_type(self, files: List[Path]) -> Dict[str, List[Path]]:
        """Group files by type/category"""
        groups = {
            'documents': [],
            'code': [],
            'data': [], 
            'text': [],
            'other': []
        }
        
        # File type mappings
        doc_extensions = {'.pdf', '.docx', '.doc', '.rtf', '.odt'}
        code_extensions = {'.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.go', '.rs', '.php', '.rb', '.swift', '.kt', '.ts', '.jsx', '.vue'}
        data_extensions = {'.csv', '.xlsx', '.xls', '.json', '.xml', '.yaml', '.yml', '.sql'}
        text_extensions = {'.txt', '.md', '.rst', '.log'}
        
        for file_path in files:
            ext = file_path.suffix.lower()
            
            if ext in doc_extensions:
                groups['documents'].append(file_path)
            elif ext in code_extensions:
                groups['code'].append(file_path)
            elif ext in data_extensions:
                groups['data'].append(file_path)
            elif ext in text_extensions:
                groups['text'].append(file_path)
            else:
                groups['other'].append(file_path)
        
        # Print summary
        print("\n📋 Files by Type:")
        for category, file_list in groups.items():
            if file_list:
                print(f"   {category}: {len(file_list)} files")
        
        return groups

# Test the filesystem scanner
if __name__ == "__main__":
    print("🧪 Testing Filesystem Scanner...")
    
    # Create scanner with custom config
    config = ScanConfig(
        include_dirs=["~/Documents", "~/Desktop"],
        max_file_size_mb=10,  # Smaller for testing
        parallel_processing=True,
        max_workers=2
    )
    
    scanner = FilesystemScanner(config)
    
    # Progress callback function
    def show_progress(file_count, current_dir):
        print(f"  📊 Found {file_count} files... (scanning {current_dir.name})")
    
    # Scan system
    files = scanner.scan_system(progress_callback=show_progress)
    
    # Group files by type
    grouped_files = scanner.group_by_type(files)
    
    # Show recent files
    recent_files = scanner.filter_by_date(files, days_back=7)
    print(f"\n📅 Recent files (last 7 days): {len(recent_files)}")
    
    # Show sample files
    print("\n📄 Sample files found:")
    for i, file_path in enumerate(files[:10]):
        size_mb = file_path.stat().st_size / (1024 * 1024)
        print(f"   {i+1}. {file_path.name} ({size_mb:.2f}MB) - {file_path.parent}")
    
    if len(files) > 10:
        print(f"   ... and {len(files) - 10} more files")