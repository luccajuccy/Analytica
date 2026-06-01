"""
Sistema de Cache e Database para o Search Engine
Armazena metadados de arquivos e permite busca mesmo durante indexação

MELHORIAS v2.0:
- WAL mode para leitura/escrita concorrente
- Thread-safety com locks
- Batch inserts para melhor performance
- Conexões otimizadas para acesso paralelo
"""

import sqlite3
import os
import hashlib
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class KnowledgeDatabase:
    def __init__(self, db_path='search_cache/knowledge.db'):
        """Inicializa o database de conhecimento com suporte a acesso concorrente"""
        self.db_path = db_path
        self._lock = threading.RLock()  # Lock reentrante para thread-safety
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Inicializar database com WAL mode
        self._init_database()
        
    @contextmanager
    def _get_connection(self, readonly=False):
        """Context manager para conexões thread-safe com timeout"""
        conn = sqlite3.connect(
            self.db_path, 
            timeout=30.0,  # Timeout de 30 segundos para evitar deadlocks
            check_same_thread=False,
            isolation_level='DEFERRED'
        )
        conn.row_factory = sqlite3.Row
        
        # Configurações de performance
        conn.execute('PRAGMA journal_mode=WAL')  # Write-Ahead Logging
        conn.execute('PRAGMA synchronous=NORMAL')  # Balance entre segurança e velocidade
        conn.execute('PRAGMA cache_size=10000')  # Cache maior
        conn.execute('PRAGMA temp_store=MEMORY')  # Temp tables em memória
        
        try:
            yield conn
            if not readonly:
                conn.commit()
        except Exception as e:
            if not readonly:
                conn.rollback()
            raise e
        finally:
            conn.close()
        
    def _init_database(self):
        """Cria as tabelas necessárias se não existirem"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de arquivos indexados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                real_path TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                type TEXT,
                mime TEXT,
                size TEXT,
                size_bytes INTEGER,
                modified TEXT,
                hash TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP
            )
        ''')
        
        # Índices para melhor performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_path ON files(path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON files(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON files(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON files(hash)')
        
        # Tabela para histórico de buscas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_query ON search_history(query)')
        
        # === NOVA TABELA: Ratings/Likes de arquivos ===
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                likes INTEGER DEFAULT 0,
                dislikes INTEGER DEFAULT 0,
                last_rated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path_rating ON file_ratings(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_likes ON file_ratings(likes DESC)')
        
        # === TABELA: Histórico de Chat ===
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                documents_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_history(created_at DESC)')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def get_file_hash(self, filepath):
        """Calcula hash MD5 de um arquivo para detectar mudanças"""
        try:
            hash_md5 = hashlib.md5()
            with open(filepath, "rb") as f:
                # Ler apenas primeiros 64KB para performance
                chunk = f.read(65536)
                if chunk:
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {filepath}: {e}")
            return None
    
    def is_file_indexed(self, filepath):
        """Verifica se arquivo já está indexado e se mudou (thread-safe)"""
        with self._lock:
            with self._get_connection(readonly=True) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT hash, size_bytes FROM files WHERE real_path = ?', (filepath,))
                result = cursor.fetchone()
                
                if not result:
                    return False, None
                
                stored_hash, stored_size = result
                
                # Verificar se arquivo mudou (por tamanho e hash)
                try:
                    current_size = os.path.getsize(filepath)
                    if current_size != stored_size:
                        return False, stored_hash
                    
                    # Se tamanho igual, verificar hash (apenas primeiros 64KB)
                    current_hash = self.get_file_hash(filepath)
                    if current_hash != stored_hash:
                        return False, stored_hash
                    
                    return True, stored_hash
                except:
                    return False, stored_hash
    
    def add_file(self, file_data):
        """Adiciona ou atualiza arquivo no database (thread-safe)"""
        try:
            # Calcular hash fora do lock para melhor performance
            file_hash = self.get_file_hash(file_data['real_path'])
            
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO files 
                        (path, real_path, title, content, type, mime, size, size_bytes, modified, hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        file_data['path'],
                        file_data['real_path'],
                        file_data['title'],
                        file_data.get('content', ''),
                        file_data['type'],
                        file_data['mime'],
                        file_data['size'],
                        file_data.get('size_bytes', 0),
                        file_data['modified'],
                        file_hash
                    ))
            return True
        except Exception as e:
            logger.error(f"Error adding file to database: {e}")
            return False
    
    def add_files_batch(self, files_data):
        """Adiciona múltiplos arquivos em uma transação (melhor performance para indexação)"""
        if not files_data:
            return True
        
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    for file_data in files_data:
                        file_hash = self.get_file_hash(file_data.get('real_path', ''))
                        cursor.execute('''
                            INSERT OR REPLACE INTO files 
                            (path, real_path, title, content, type, mime, size, size_bytes, modified, hash)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            file_data['path'],
                            file_data['real_path'],
                            file_data['title'],
                            file_data.get('content', ''),
                            file_data['type'],
                            file_data['mime'],
                            file_data['size'],
                            file_data.get('size_bytes', 0),
                            file_data['modified'],
                            file_hash
                        ))
            logger.info(f"Batch inserted {len(files_data)} files into database")
            return True
        except Exception as e:
            logger.error(f"Error batch adding files to database: {e}")
            return False
    
    def search(self, query):
        """Busca arquivos no database (thread-safe, funciona durante indexação)"""
        if not query:
            return []
        
        try:
            with self._get_connection(readonly=True) as conn:
                cursor = conn.cursor()
                
                # Registrar busca em transação separada para não bloquear
                try:
                    self._track_search(query)
                except:
                    pass  # Não bloquear busca se tracking falhar
                
                query_lower = query.lower()
                query_parts = query_lower.split()
                
                # Busca por título e conteúdo
                results = []
                
                # Buscar em título (maior pontuação)
                cursor.execute('''
                    SELECT * FROM files 
                    WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
                    ORDER BY 
                        CASE 
                            WHEN LOWER(title) LIKE ? THEN 1
                            WHEN LOWER(content) LIKE ? THEN 2
                            ELSE 3
                        END,
                        indexed_at DESC
                    LIMIT 100
                ''', (f'%{query_lower}%', f'%{query_lower}%', f'%{query_lower}%', f'%{query_lower}%'))
                
                for row in cursor.fetchall():
                    # Calcular score de relevância
                    score = 0
                    title_lower = row['title'].lower()
                    content_lower = (row['content'] or '').lower()
                    
                    if query_lower in title_lower:
                        score += 30
                    
                    if all(part in title_lower for part in query_parts):
                        score += 15
                    
                    if content_lower and query_lower in content_lower:
                        score += 5
                    
                    if score > 0:
                        results.append({
                            'title': row['title'],
                            'path': row['path'],
                            'real_path': row['real_path'],
                            'type': row['type'],
                            'size': row['size'],
                            'modified': row['modified'],
                            'thumbnail': None,
                            'snippet': self._generate_snippet(content_lower, query_lower) if content_lower else f"Arquivo {row['type']} encontrado.",
                            'score': score
                        })
                
                # Ordenar por score
                results.sort(key=lambda x: x['score'], reverse=True)
                
                # Remover campo score antes de retornar
                for r in results:
                    r.pop('score', None)
                
                return results
                
        except Exception as e:
            logger.error(f"Error searching database: {e}")
            return []
    
    def _generate_snippet(self, content, query):
        """Gera snippet do conteúdo com contexto ao redor da query"""
        if not content:
            return ""
        
        try:
            start_idx = content.find(query)
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
    
    def _track_search(self, query):
        """Registra busca no histórico (thread-safe)"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    clean_query = query.lower().strip()
                    
                    # Verifica se já existe
                    cursor.execute('SELECT id, count FROM search_history WHERE query = ?', (clean_query,))
                    result = cursor.fetchone()
                    
                    if result:
                        # Atualiza contador
                        cursor.execute('''
                            UPDATE search_history 
                            SET count = count + 1, last_searched = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        ''', (result[0],))
                    else:
                        # Insere nova busca
                        cursor.execute('''
                            INSERT INTO search_history (query, count) 
                            VALUES (?, 1)
                        ''', (clean_query,))
        except Exception as e:
            logger.error(f"Error tracking search: {e}")
    
    def get_suggestions(self, limit=5):
        """Retorna sugestões de busca baseadas no histórico (thread-safe)"""
        try:
            with self._get_connection(readonly=True) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT query FROM search_history 
                    ORDER BY count DESC, last_searched DESC 
                    LIMIT ?
                ''', (limit,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting suggestions: {e}")
            return []
    
    def get_stats(self):
        """Retorna estatísticas do database (thread-safe)"""
        try:
            with self._get_connection(readonly=True) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM files')
                total_files = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(DISTINCT type) FROM files')
                total_types = cursor.fetchone()[0]
                
                cursor.execute('SELECT SUM(size_bytes) FROM files')
                total_size = cursor.fetchone()[0] or 0
                
                return {
                    'total_files': total_files,
                    'total_types': total_types,
                    'total_size_bytes': total_size
                }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
    
    def clear_cache(self):
        """Limpa todo o cache (usar com cuidado) - thread-safe"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM files')
                    cursor.execute('DELETE FROM search_history')
            logger.info("Cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    # ========================================
    # SISTEMA DE LIKES / RATING
    # ========================================
    
    def like_file(self, file_path):
        """Incrementa like de um arquivo (thread-safe)"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Verifica se já existe registro
                    cursor.execute('SELECT id, likes FROM file_ratings WHERE file_path = ?', (file_path,))
                    result = cursor.fetchone()
                    
                    if result:
                        # Incrementa likes
                        new_likes = result['likes'] + 1
                        cursor.execute('''
                            UPDATE file_ratings 
                            SET likes = ?, last_rated = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        ''', (new_likes, result['id']))
                        return new_likes
                    else:
                        # Cria novo registro com 1 like
                        cursor.execute('''
                            INSERT INTO file_ratings (file_path, likes, last_rated) 
                            VALUES (?, 1, CURRENT_TIMESTAMP)
                        ''', (file_path,))
                        return 1
        except Exception as e:
            logger.error(f"Error liking file: {e}")
            return 0
    
    def dislike_file(self, file_path):
        """Incrementa dislike de um arquivo (thread-safe)"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('SELECT id, dislikes FROM file_ratings WHERE file_path = ?', (file_path,))
                    result = cursor.fetchone()
                    
                    if result:
                        new_dislikes = result['dislikes'] + 1
                        cursor.execute('''
                            UPDATE file_ratings 
                            SET dislikes = ?, last_rated = CURRENT_TIMESTAMP 
                            WHERE id = ?
                        ''', (new_dislikes, result['id']))
                        return new_dislikes
                    else:
                        cursor.execute('''
                            INSERT INTO file_ratings (file_path, dislikes, last_rated) 
                            VALUES (?, 1, CURRENT_TIMESTAMP)
                        ''', (file_path,))
                        return 1
        except Exception as e:
            logger.error(f"Error disliking file: {e}")
            return 0
    
    def get_file_likes(self, file_path):
        """Retorna contagem de likes de um arquivo"""
        try:
            with self._get_connection(readonly=True) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT likes, dislikes FROM file_ratings WHERE file_path = ?', (file_path,))
                result = cursor.fetchone()
                
                if result:
                    return {'likes': result['likes'], 'dislikes': result['dislikes']}
                return {'likes': 0, 'dislikes': 0}
        except Exception as e:
            logger.error(f"Error getting file likes: {e}")
            return {'likes': 0, 'dislikes': 0}
    
    def get_all_ratings(self):
        """Retorna todos os ratings como dicionário {path: likes} para uso em ranking"""
        try:
            with self._get_connection(readonly=True) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT file_path, likes, dislikes FROM file_ratings')
                ratings = {}
                for row in cursor.fetchall():
                    ratings[row['file_path']] = {
                        'likes': row['likes'],
                        'dislikes': row['dislikes'],
                        'score': row['likes'] - row['dislikes']
                    }
                return ratings
        except Exception as e:
            logger.error(f"Error getting all ratings: {e}")
            return {}
    
    def get_top_rated(self, limit=10):
        """Retorna os arquivos mais bem avaliados"""
        try:
            with self._get_connection(readonly=True) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT fr.file_path, fr.likes, fr.dislikes, f.title, f.type
                    FROM file_ratings fr
                    LEFT JOIN files f ON fr.file_path = f.path
                    WHERE fr.likes > 0
                    ORDER BY (fr.likes - fr.dislikes) DESC, fr.last_rated DESC
                    LIMIT ?
                ''', (limit,))
                
                return [
                    {
                        'path': row['file_path'],
                        'likes': row['likes'],
                        'dislikes': row['dislikes'],
                        'title': row['title'] or 'Arquivo',
                        'type': row['type'] or 'Desconhecido'
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Error getting top rated: {e}")
            return []
    
    # ========================================
    # HISTÓRICO DE CHAT
    # ========================================
    
    def save_chat_message(self, user_message, bot_response, documents_used=None):
        """Salva uma interação do chat no histórico"""
        try:
            import json
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Serializar documentos se fornecidos
                    docs_json = json.dumps(documents_used) if documents_used else None
                    
                    cursor.execute('''
                        INSERT INTO chat_history (user_message, bot_response, documents_used)
                        VALUES (?, ?, ?)
                    ''', (user_message, bot_response, docs_json))
                    
                    logger.debug(f"Chat message saved: {user_message[:50]}...")
                    return True
        except Exception as e:
            logger.error(f"Error saving chat message: {e}")
            return False
    
    def get_chat_history(self, limit=50):
        """Retorna histórico de conversas do chat"""
        try:
            import json
            with self._get_connection(readonly=True) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT user_message, bot_response, documents_used, created_at
                    FROM chat_history
                    ORDER BY created_at DESC
                    LIMIT ?
                ''', (limit,))
                
                history = []
                for row in cursor.fetchall():
                    docs = None
                    if row['documents_used']:
                        try:
                            docs = json.loads(row['documents_used'])
                        except:
                            docs = None
                    
                    history.append({
                        'user_message': row['user_message'],
                        'bot_response': row['bot_response'],
                        'documents': docs,
                        'timestamp': row['created_at']
                    })
                
                # Inverter para ordem cronológica
                return list(reversed(history))
        except Exception as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    def clear_chat_history(self):
        """Limpa todo o histórico de chat"""
        try:
            with self._lock:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM chat_history')
                    logger.info("Chat history cleared")
                    return True
        except Exception as e:
            logger.error(f"Error clearing chat history: {e}")
            return False

