import os
import mimetypes
from datetime import datetime
import logging
from collections import Counter, deque
import json
import threading
import time
from knowledge_database import KnowledgeDatabase

# Configure logging
logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self, root_path, exclude_paths=None, history_file='search_history.json'):
        """
        Initialize the Search Engine.
        :param root_path: The root directory to index.
        :param exclude_paths: List of absolute paths to exclude from indexing.
        :param history_file: Path to save/load search history (deprecated, using database now).
        """
        self.original_root = os.path.abspath(root_path)
        self.root_path = self._fix_long_path(self.original_root)
        
        # Normalize exclude paths
        self.exclude_paths = [os.path.normpath(p).lower() for p in (exclude_paths or [])]
        
        # In-memory index (for backward compatibility)
        self.index = []
        self.is_indexing = False
        self.current_scanning_path = ""
        self.scanned_count = 0
        self.scanning_phase = "Ready" 
        self.log_buffer = deque(maxlen=15)
        
        # Initialize database for persistent cache
        self.db = KnowledgeDatabase()
        
        # Load existing index from database on startup
        logger.info("Loading cached index from database...")
        self._load_from_database()
        
        # Deprecated: JSON history file (now using database)
        self.history_file = history_file
        self.search_history = Counter()  # Not used anymore
        self.stop_words = {'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'no', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'ao', 'ele', 'das'}

    def get_status(self):
        """Returns the current status of the engine."""
        return {
            'is_indexing': self.is_indexing,
            'current_path': self.current_scanning_path,
            'scanned_count': self.scanned_count,
            'total_indexed': len(self.index),
            'phase': self.scanning_phase,
            'logs': list(self.log_buffer)
        }

    def _fix_long_path(self, path):
        """Prepares path for Windows long path support (MAX_PATH bypass)."""
        if os.name == 'nt':
            if path.startswith(r"\\"):
                # Network path: \\server\share -> \\?\UNC\server\share
                if not path.startswith(r"\\?\UNC"):
                    return r"\\?\UNC" + path[1:]
            elif not path.startswith(r"\\?"):
                # Local path: C:\path -> \\?\C:\path
                return r"\\?\%s" % path
        return path

    def _load_history(self):
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return Counter(json.load(f))
        except Exception as e:
            logger.error(f"Failed to load search history: {e}")
        return Counter()

    def _save_history(self):
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.search_history, f)
        except Exception as e:
            logger.error(f"Failed to save search history: {e}")
    
    def _load_from_database(self):
        """Loads cached index from database on startup"""
        try:
            stats = self.db.get_stats()
            total_files = stats.get('total_files', 0)
            
            if total_files > 0:
                logger.info(f"Loaded {total_files} files from cache database")
                # Update self.index size for status reporting
                self.index = [{'cached': True}] * total_files  # Placeholder for count
            else:
                logger.info("No cached index found. Will perform full indexation on first search.")
        except Exception as e:
            logger.error(f"Error loading from database: {e}")

    def start_indexing(self):
        """Starts the indexing process in a background thread."""
        if self.is_indexing:
            logger.warning("Indexing already in progress.")
            return
        
        thread = threading.Thread(target=self._build_index_worker, daemon=True)
        thread.start()

    def _build_index_worker(self):
        """Worker method for indexing (Two-Phase Strategy)."""
        self.is_indexing = True
        logger.info(f"Starting async index build for {self.root_path}")
        start_time = time.time()
        
        # Temporary storage for processing
        content_queue = []
        new_index = []
        
        try:
            # === PHASE 1: METADATA SCAN (Fast) ===
            self.scanning_phase = "METADATA SCAN"
            logger.info("Phase 1: Starting Metadata Scan")
            
            for root, dirs, files in os.walk(self.root_path):
                # Normalize raw path for exclusion checking
                clean_root = root.replace(r"\\?\UNC", r"\\").replace("\\\\?\\", "")
                norm_root = os.path.normpath(clean_root).lower()
                
                # Check exclusions
                if any(norm_root.startswith(excl) for excl in self.exclude_paths):
                    dirs[:] = [] 
                    continue
                
                # Exclude system folders
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', '__pycache__', 'node_modules', '.git', '$RECYCLE.BIN', 'System Volume Information']]
                
                for file in files:
                    if file.startswith('.') or file.startswith('~$'):
                        continue
                        
                    try:
                        self.scanned_count += 1
                        full_path = os.path.join(root, file)
                        self.current_scanning_path = file
                        self.log_buffer.append(f"> FOUND: {file}")
                        
                        # Fix stats call for long paths
                        try:
                            stats = os.stat(full_path)
                        except OSError:
                            continue

                        # Calculate relative path - FIXED for UNC paths
                        # Clean full path: remove long path prefix
                        clean_full_path = full_path
                        if clean_full_path.startswith(r"\\?\UNC"):
                             # Replace \\?\UNC with \ (so \\?\UNC\server -> \\server)
                             clean_full_path = clean_full_path.replace(r"\\?\UNC", "\\", 1)
                        elif clean_full_path.startswith(r"\\?\C:"): # Handle local drives if needed
                             clean_full_path = clean_full_path.replace("\\\\?\\", "", 1)
                        elif clean_full_path.startswith("\\\\?\\"):
                             clean_full_path = clean_full_path[4:]  # \\?\C:\path -> C:\path
                        
                        # Calculate relative path from the ORIGINAL root (without long path prefix)
                        try:
                            rel_path = os.path.relpath(clean_full_path, self.original_root)
                        except ValueError:
                            # Different drives on Windows - use clean path as is
                            rel_path = os.path.basename(clean_full_path)
                        
                        # Check if file is already in database and hasn't changed
                        is_indexed, old_hash = self.db.is_file_indexed(clean_full_path)
                        if is_indexed:
                            self.log_buffer.append(f"> CACHED: {file}")
                            # Skip to next file - already in database
                            continue
                        
                        mtime = datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M')
                        size_str = self._format_size(stats.st_size)
                        
                        # Guess MIME
                        mime_type, _ = mimetypes.guess_type(clean_full_path)
                        if not mime_type:
                            mime_type = 'application/octet-stream'
                        
                        human_type = self._human_readable_type(mime_type, file)

                        entry = {
                            'path': rel_path.replace('\\', '/'),
                            'real_path': clean_full_path,
                            'full_path_long': full_path, # Keep for phase 2
                            'title': file,
                            'content': "", # Placeholder for now
                            'type': human_type,
                            'mime': mime_type,
                            'size': size_str,
                            'size_bytes': stats.st_size,  # Add size_bytes for database
                            'modified': mtime,
                            'thumbnail': self._get_thumbnail_path(mime_type, rel_path, clean_full_path)
                        }
                        
                        new_index.append(entry)
                        
                        # Add to content queue if it's text-based
                        if 'text' in mime_type or human_type == 'Código Fonte':
                            content_queue.append(entry)
                        
                        # === SAVE TO DATABASE INCREMENTALLY (every 20 files) ===
                        # This makes results available for search immediately
                        if len(new_index) % 20 == 0:
                            try:
                                # Get last 20 entries for batch insert
                                batch = new_index[-20:]
                                self.db.add_files_batch(batch)
                            except Exception as db_err:
                                logger.debug(f"Batch insert skipped: {db_err}")
                            
                            self.index = list(new_index) # Copy to live index
                            time.sleep(0.001) # Yield
                        
                    except Exception as e:
                        if "Permission denied" not in str(e):
                            logger.error(f"Error processing file {file}: {str(e)[:100]}")
                        continue
            
            # Save remaining files (last batch)
            remaining = len(new_index) % 20
            if remaining > 0:
                try:
                    batch = new_index[-remaining:]
                    self.db.add_files_batch(batch)
                except Exception:
                    pass
            
            # Commit full metadata index
            self.index = list(new_index)
            logger.info(f"Phase 1 Complete. {len(self.index)} files indexed and saved to database.")

            # === PHASE 2: CONTENT INDEXING (Slower) ===
            self.scanning_phase = "CONTENT ANALYSIS"
            logger.info(f"Phase 2: Starting Content Analysis on {len(content_queue)} files")
            
            processed_content = 0
            for entry in content_queue:
                try:
                    self.current_scanning_path = f"Reading: {entry['title']}"
                    self.log_buffer.append(f"> ANALYZING: {entry['title']}")
                    
                    # Read content safely
                    content = self._read_text_file(entry['full_path_long'])
                    entry['content'] = content # Update in place (reference in self.index)
                    
                    # Update content in database
                    try:
                        entry_for_db = entry.copy()
                        entry_for_db['content'] = content
                        self.db.add_file(entry_for_db)
                    except Exception as e:
                        logger.error(f"Failed to update content in database: {e}")
                    
                    processed_content += 1
                    if processed_content % 10 == 0:
                        time.sleep(0.001)
                        
                except Exception:
                    continue
            
            duration = time.time() - start_time
            logger.info(f"Index built successfully in {duration:.2f}s. {len(self.index)} items indexed.")
            
        except Exception as e:
            logger.error(f"Critical error building index: {e}")
        finally:
            self.is_indexing = False
            self.scanning_phase = "READY"
            self.current_scanning_path = ""

    def search(self, query):
        """
        Search using database (allows search during indexing).
        Falls back to in-memory index if database is empty.
        INCLUDES: likes in ranking score
        """
        if not query:
            return []
        
        # Get all ratings for ranking boost
        try:
            all_ratings = self.db.get_all_ratings()
        except:
            all_ratings = {}
        
        # Use database search (works even during indexing)
        try:
            results = self.db.search(query)
            if results:
                # Enhance results with likes and recalculate score
                for result in results:
                    path = result.get('path', '')
                    rating = all_ratings.get(path, {'likes': 0, 'dislikes': 0, 'score': 0})
                    result['likes'] = rating.get('likes', 0)
                    result['dislikes'] = rating.get('dislikes', 0)
                    # Add rating score for client-side info
                    result['rating_score'] = rating.get('score', 0)
                
                # Re-sort results including likes (5 points per like)
                # Note: Database already sorted by relevance, now we boost by likes
                def combined_score(item):
                    rating_boost = item.get('rating_score', 0) * 5
                    return rating_boost
                
                # Stable sort: keeps original relevance order, then boosts by likes
                results = sorted(results, key=combined_score, reverse=True)
                
                return results
        except Exception as e:
            logger.error(f"Database search failed: {e}")
        
        # Fallback to in-memory index if database is empty or failed
        if not self.index or len(self.index) == 0:
            return []
        
        # Original in-memory search logic (for backward compatibility) 
        self._track_search(query)
            
        query_lower = query.lower()
        query_parts = query_lower.split()
        results = []
        
        for item in self.index:
            # Skip placeholder items from cache
            if item.get('cached'):
                continue
                
            score = 0
            title_lower = item['title'].lower()
            content_lower = item['content'].lower() if item['content'] else ""
            
            if query_lower in title_lower:
                score += 30 
            
            if all(part in title_lower for part in query_parts):
                score += 15
                
            if content_lower and query_lower in content_lower:
                score += 5
                
            if score > 0:
                res = {
                    'title': item['title'],
                    'path': item['path'],
                    'real_path': item.get('real_path', item['path']),
                    'type': item['type'],
                    'size': item['size'],
                    'modified': item['modified'],
                    'thumbnail': item['thumbnail'],
                    'snippet': self._generate_snippet(item['content'], query_lower) if item['content'] else f"Arquivo {item['type']} encontrado."
                }
                results.append((score, res))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results]

    def _track_search(self, query):
        clean_query = query.lower().strip()
        if len(clean_query) > 2 and clean_query not in self.stop_words:
            self.search_history[clean_query] += 1
            self._save_history()

    def get_suggestions(self, limit=5):
        """Get search suggestions from database"""
        try:
            return self.db.get_suggestions(limit)
        except:
            return []

    def _read_text_file(self, path):
        """Reads a chunk of a text file safely."""
        try:
            # Open with buffering and standard encoding
            # Use 'path' which should be the long path if needed
            with open(path, 'r', encoding='utf-8', errors='ignore', buffering=8192) as f:
                # Read 50KB - enough for a snippet, avoids loading massive files
                return f.read(51200) 
        except Exception:
            return ""

    def _generate_snippet(self, content, query):
        if not content: return ""
        try:
            lower_content = content.lower()
            start_idx = lower_content.find(query)
            if start_idx == -1:
                return content[:150] + "..."
            
            start = max(0, start_idx - 60)
            end = min(len(content), start_idx + len(query) + 100)
            snippet = content[start:end]
            
            if start > 0:
                snippet = "..." + snippet
            if end < len(content):
                snippet = snippet + "..."
            
            return snippet.replace('\n', ' ')
        except:
            return content[:100]

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"

    def _human_readable_type(self, mime, filename):
        ext = os.path.splitext(filename)[1].lower()
        
        # Office
        if ext in ['.doc', '.docx', '.dot']: return 'Word Document'
        if ext in ['.xls', '.xlsx', '.csv']: return 'Excel Spreadsheet'
        if ext in ['.ppt', '.pptx']: return 'PowerPoint Presentation'
        if ext == '.pdf': return 'PDF Document'
        
        # Images/Media
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff']: return 'Imagem'
        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']: return 'Vídeo'
        if ext in ['.mp3', '.wav', '.ogg']: return 'Áudio'
        
        # Code
        if ext in ['.py', '.js', '.html', '.css', '.cpp', '.java', '.php', '.sql', '.json', '.xml']: return 'Código Fonte'
        if ext in ['.txt', '.md', '.log', '.rst', '.url', '.lnk']: return 'Documento de Texto'
        
        # Archives
        if ext in ['.zip', '.rar', '.7z', '.tar', '.gz']: return 'Arquivo Compactado'
        
        return mime or 'Arquivo'

    def _get_thumbnail_path(self, mime, rel_path, full_path):
        if mime and mime.startswith('image/'):
            # Return relative path for the server to serve as image source
            return rel_path.replace('\\', '/')
        return None

