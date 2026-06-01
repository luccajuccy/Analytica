import os
import re
import time
import base64
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import markdown
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import numpy as np
import fitz  # PyMuPDF
import pandas as pd
import hashlib
import pickle
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import queue
import traceback

# ====================
# 🔷 CONFIGURAÇÕES AVANÇADAS
# ====================
DEFAULT_KNOWLEDGE_DIR = r"\\srv-evt\Central de Operações\Central de Utilidades\GP1 - HVAC e Utilidades\Operadores\Lucca Juccy\Ajuster\Projetos de Melhoria"
CACHE_DIR = "./search_cache"
CHUNK_SIZE = 3500
CHUNK_OVERLAP = 900
TOP_K = 10
MIN_SIMILARITY = 0.16
MAX_THREADS = 12
SUPPORTED_EXTENSIONS = ['.md', '.pdf', '.txt', '.docx', '.xlsx', '.pptx']
PRELOAD_FILE_TYPES = ['.md', '.txt']  # Arquivos para pré-carregamento rápido
PROGRESS_UPDATE_INTERVAL = 0.5  # Atualizar progresso a cada 0.5 segundos

# ====================
# 🛠️ INICIALIZAÇÃO
# ====================
nltk.download('stopwords', quiet=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# ====================
# 🎨 TEMA PROFISSIONAL
# ====================
def setup_ui():
    st.set_page_config(
        page_title="EVT HyperSearch",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # CSS avançado com animações
    st.markdown(f"""
    <style>
        :root {{
            --primary: #1e88e5;
            --secondary: #0d47a1;
            --accent: #64b5f6;
            --background: #0a192f;
            --text: #e3f2fd;
            --card: #132f4c;
            --success: #4caf50;
            --warning: #ff9800;
            --error: #f44336;
        }}
        
        .stApp {{
            background: linear-gradient(135deg, var(--background) 0%, #0a192f 100%);
            color: var(--text);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            animation: fadeIn 1s ease-in;
        }}
        
        @keyframes fadeIn {{
            0% {{ opacity: 0; }}
            100% {{ opacity: 1; }}
        }}
        
        .header-gradient {{
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.8s ease-out;
        }}
        
        @keyframes slideIn {{
            0% {{ transform: translateY(-50px); opacity: 0; }}
            100% {{ transform: translateY(0); opacity: 1; }}
        }}
        
        .search-box {{
            background-color: rgba(19, 47, 76, 0.85);
            padding: 25px;
            border-radius: 18px;
            margin-bottom: 30px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(100, 181, 246, 0.4);
        }}
        
        .search-result-card {{
            background-color: var(--card);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            border: 1px solid rgba(100, 181, 246, 0.3);
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.15);
        }}
        
        .search-result-card:hover {{
            transform: translateY(-7px);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
            border-color: var(--accent);
        }}
        
        .result-title {{
            color: var(--accent);
            font-size: 1.4em;
            font-weight: 700;
            margin-bottom: 12px;
        }}
        
        .result-path {{
            color: #90caf9;
            font-size: 0.9em;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .result-snippet {{
            color: var(--text);
            font-size: 1.05em;
            line-height: 1.7;
            margin: 20px 0;
            padding: 15px;
            background: rgba(19, 47, 76, 0.6);
            border-radius: 12px;
            border-left: 4px solid var(--primary);
        }}
        
        .result-similarity {{
            display: inline-block;
            background: rgba(30, 136, 229, 0.25);
            padding: 6px 15px;
            border-radius: 20px;
            font-size: 0.95em;
            font-weight: 600;
            margin-top: 15px;
        }}
        
        .chunk-nav {{
            display: flex;
            gap: 12px;
            margin: 15px 0;
        }}
        
        .chunk-btn {{
            background: rgba(30, 136, 229, 0.2) !important;
            color: var(--accent) !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 8px 16px !important;
            font-size: 0.9em !important;
            transition: all 0.3s ease !important;
        }}
        
        .chunk-btn:hover {{
            background: rgba(30, 136, 229, 0.4) !important;
            transform: translateY(-2px);
        }}
        
        .mermaid-container {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin: 25px 0;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }}
        
        .performance-badge {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(25, 118, 210, 0.9);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.85em;
            z-index: 1000;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(4px);
        }}
        
        .stSpinner > div > div {{
            border-top-color: var(--primary) !important;
            border-bottom-color: var(--primary) !important;
        }}
        
        .highlight {{
            background: linear-gradient(120deg, rgba(255,255,0,0.3), rgba(255,255,0,0.6));
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: bold;
        }}
        
        .file-icon {{
            font-size: 1.2em;
            margin-right: 8px;
            vertical-align: middle;
        }}
        
        .progress-container {{
            margin: 20px 0;
            padding: 15px;
            background: rgba(19, 47, 76, 0.6);
            border-radius: 12px;
            border-left: 4px solid var(--primary);
        }}
        
        .progress-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
        }}
        
        .progress-bar {{
            height: 20px;
            background: rgba(30, 136, 229, 0.2);
            border-radius: 10px;
            overflow: hidden;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--accent));
            border-radius: 10px;
            transition: width 0.3s ease;
        }}
        
        .file-list {{
            max-height: 300px;
            overflow-y: auto;
            margin-top: 15px;
            padding: 10px;
            background: rgba(19, 47, 76, 0.4);
            border-radius: 8px;
        }}
        
        .file-item {{
            padding: 8px;
            border-bottom: 1px solid rgba(100, 181, 246, 0.2);
            display: flex;
            align-items: center;
        }}
        
        .file-icon-small {{
            margin-right: 10px;
            font-size: 1.2em;
        }}
    </style>
    """, unsafe_allow_html=True)

# ====================
# ⚡ SISTEMA DE CACHE
# ====================
def get_file_hash(file_path):
    """Gera hash único para o arquivo"""
    return hashlib.md5(Path(file_path).read_bytes()).hexdigest()

def get_cache_file(knowledge_dir):
    """Retorna caminho do arquivo de cache"""
    dir_hash = hashlib.md5(knowledge_dir.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{dir_hash}.pkl")

def load_from_cache(knowledge_dir):
    """Carrega dados do cache se disponível"""
    cache_file = get_cache_file(knowledge_dir)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            pass
    return None

def save_to_cache(data, knowledge_dir):
    """Salva dados no cache"""
    cache_file = get_cache_file(knowledge_dir)
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except:
        pass

# ====================
# 🚀 PROCESSAMENTO DE ARQUIVOS
# ====================
def extract_text_from_pdf(pdf_path):
    """Extrai texto de PDFs com PyMuPDF"""
    try:
        doc = fitz.open(pdf_path)
        return "\n".join(page.get_text() for page in doc)
    except:
        return ""

def extract_mermaid_diagrams(text):
    """Extrai diagramas Mermaid do texto"""
    diagrams = []
    pattern = r'```mermaid(.*?)```'
    for match in re.finditer(pattern, text, re.DOTALL):
        diagram = match.group(1).strip()
        if diagram:
            diagrams.append(diagram)
    return diagrams

def process_file(file_path, knowledge_dir):
    """Processa um arquivo e retorna metadados"""
    try:
        rel_path = os.path.relpath(file_path, knowledge_dir)
        file_ext = os.path.splitext(file_path)[1].lower()
        file_size = os.path.getsize(file_path)
        last_modified = os.path.getmtime(file_path)
        
        # Ignorar arquivos muito grandes
        if file_size > 50 * 1024 * 1024:  # 50MB
            return None
        
        text = ""
        mermaid_diagrams = []
        
        if file_ext == '.md' or file_ext == '.txt':
            for enc in ("utf-8", "latin-1", "iso-8859-1", "cp1252"):
                try:
                    with open(file_path, "r", encoding=enc) as f:
                        text = f.read()
                    mermaid_diagrams = extract_mermaid_diagrams(text)
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
        
        elif file_ext == '.pdf':
            text = extract_text_from_pdf(file_path)
            
        elif file_ext in ('.docx', '.xlsx', '.pptx'):
            # Implementação básica para outros formatos
            pass
            
        return {
            'filepath': rel_path,
            'full_path': file_path,
            'extension': file_ext,
            'content': text,
            'mermaid_diagrams': mermaid_diagrams,
            'size': file_size,
            'last_modified': last_modified
        }
    except Exception as e:
        print(f"Erro ao processar {file_path}: {str(e)}")
        return None

# ====================
# 🧠 PRÉ-PROCESSAMENTO DE TEXTO
# ====================
def preprocess_text(text):
    """Pré-processamento avançado com stemming"""
    if not text:
        return ""
    
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    
    stop_words = set(stopwords.words('portuguese'))
    stemmer = SnowballStemmer('portuguese')
    
    words = text.split()
    processed_words = [stemmer.stem(word) for word in words 
                      if word not in stop_words and len(word) > 2]
    
    return " ".join(processed_words)

def chunk_text(text, chunk_size, overlap):
    """Divide texto em chunks com sobreposição"""
    if not text:
        return []
    
    chunks = []
    start = 0
    step = chunk_size - overlap
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end]
        
        # Garantir que não dividimos palavras ao meio
        if end < len(text):
            last_space = chunk.rfind(' ')
            if last_space != -1 and last_space > len(chunk) * 0.8:
                end = start + last_space
                chunk = text[start:end]
        
        chunks.append(chunk)
        start += step
        
        if end == len(text):
            break
    
    return chunks

# ====================
# ⚙️ CARREGAMENTO DA BASE
# ====================
class KnowledgeLoader:
    def __init__(self, knowledge_dir):
        self.knowledge_dir = knowledge_dir
        self.progress_queue = queue.Queue()
        self.knowledge_data = None
        self.thread = None
        self.start_time = time.time()
        self.file_count = 0
        self.processed_count = 0
        self.current_file = ""
        
    def _run_loader(self):
        """Método interno para carregar dados em segundo plano"""
        try:
            # Verificar cache primeiro
            cached_data = load_from_cache(self.knowledge_dir)
            if cached_data:
                self.knowledge_data = cached_data
                self.progress_queue.put(("complete", 1.0, "Cache carregado"))
                return
                
            if not os.path.isdir(self.knowledge_dir):
                self.knowledge_data = {
                    'metadata': [],
                    'file_index': {},
                    'vectorizer': None,
                    'tfidf_matrix': None,
                    'chunks': [],
                    'mermaid_diagrams': {}
                }
                self.progress_queue.put(("complete", 1.0, "Diretório não encontrado"))
                return

            # Coletar arquivos de forma otimizada
            all_files = []
            for root, _, files in os.walk(self.knowledge_dir):
                for file in files:
                    file_ext = os.path.splitext(file)[1].lower()
                    if file_ext in SUPPORTED_EXTENSIONS:
                        all_files.append(os.path.join(root, file))
                        
            self.file_count = len(all_files)
            if self.file_count == 0:
                self.knowledge_data = {
                    'metadata': [],
                    'file_index': {},
                    'vectorizer': None,
                    'tfidf_matrix': None,
                    'chunks': [],
                    'mermaid_diagrams': {}
                }
                self.progress_queue.put(("complete", 1.0, "Nenhum arquivo encontrado"))
                return

            # Ordenar arquivos por tipo (pré-carregar tipos leves primeiro)
            all_files.sort(key=lambda x: 0 if os.path.splitext(x)[1].lower() in PRELOAD_FILE_TYPES else 1)

            # Processamento paralelo em duas etapas
            metadata_list = []
            file_index = {}
            mermaid_diagrams = {}
            all_chunks = []
            
            # Etapa 1: Processar arquivos em paralelo
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = {executor.submit(process_file, fp, self.knowledge_dir): fp for fp in all_files}
                
                for i, future in enumerate(as_completed(futures)):
                    result = future.result()
                    if result:
                        metadata_list.append(result)
                        file_index[result['filepath']] = result
                        
                        # Armazenar diagramas Mermaid
                        if result['mermaid_diagrams']:
                            mermaid_diagrams[result['filepath']] = result['mermaid_diagrams']
                            
                        self.current_file = os.path.basename(result['filepath'])
                        progress = (i + 1) / self.file_count
                        self.progress_queue.put(("progress", progress, f"Processando: {self.current_file}"))
            
            # Etapa 2: Criar chunks em paralelo
            total_chunks = 0
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                chunk_futures = []
                for meta in metadata_list:
                    chunk_futures.append(executor.submit(self._process_file_chunks, meta))
                
                for i, future in enumerate(as_completed(chunk_futures)):
                    chunks = future.result()
                    if chunks:
                        all_chunks.extend(chunks)
                        total_chunks += len(chunks)
                    
                    progress = (i + 1) / len(metadata_list)
                    self.progress_queue.put(("chunking", progress, f"Criando segmentos: {total_chunks} chunks"))
            
            # Criar matriz TF-IDF
            self.progress_queue.put(("vectorizing", 0, "Construindo índice de busca"))
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([c['preprocessed'] for c in all_chunks])
            self.progress_queue.put(("vectorizing", 1.0, "Índice construído"))
            
            # Construir estrutura final
            self.knowledge_data = {
                'metadata': metadata_list,
                'file_index': file_index,
                'vectorizer': vectorizer,
                'tfidf_matrix': tfidf_matrix,
                'chunks': all_chunks,
                'mermaid_diagrams': mermaid_diagrams,
                'load_time': time.time() - self.start_time
            }
            
            # Salvar em cache para próximo carregamento
            save_to_cache(self.knowledge_data, self.knowledge_dir)
            self.progress_queue.put(("complete", 1.0, "Base carregada com sucesso!"))
            
        except Exception as e:
            self.progress_queue.put(("error", 0, f"Erro: {str(e)}"))
            traceback.print_exc()
    
    def _process_file_chunks(self, file_meta):
        """Processa chunks para um arquivo"""
        chunks = chunk_text(file_meta['content'], CHUNK_SIZE, CHUNK_OVERLAP)
        result = []
        for i, chunk in enumerate(chunks):
            result.append({
                'filepath': file_meta['filepath'],
                'chunk_index': i,
                'chunk_text': chunk,
                'preprocessed': preprocess_text(chunk),
                'size': len(chunk)
            })
        return result
    
    def start_loading(self):
        """Inicia o carregamento em segundo plano"""
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run_loader, daemon=True)
            self.thread.start()
    
    def get_progress(self):
        """Obtém o progresso atual"""
        try:
            return self.progress_queue.get_nowait()
        except queue.Empty:
            return None
    
    def is_complete(self):
        """Verifica se o carregamento foi concluído"""
        return self.knowledge_data is not None and self.thread and not self.thread.is_alive()
    
    def get_data(self):
        """Retorna os dados carregados"""
        return self.knowledge_data

# ====================
# 🔍 MECANISMO DE BUSCA
# ====================
def search_knowledge(query, knowledge_data):
    """Executa busca com base na consulta"""
    if not knowledge_data or not knowledge_data.get('chunks'):
        return []
    
    # Pré-processar consulta
    processed_query = preprocess_text(query)
    query_vec = knowledge_data['vectorizer'].transform([processed_query])
    
    # Calcular similaridade
    sims = cosine_similarity(query_vec, knowledge_data['tfidf_matrix'])[0]
    
    # Obter top resultados
    top_idxs = np.argsort(sims)[::-1][:TOP_K]
    
    # Construir resultados
    results = []
    for idx in top_idxs:
        if sims[idx] > MIN_SIMILARITY:
            chunk = knowledge_data['chunks'][idx]
            file_meta = knowledge_data['file_index'][chunk['filepath']]
            
            results.append({
                'filepath': chunk['filepath'],
                'full_path': file_meta['full_path'],
                'chunk_index': chunk['chunk_index'],
                'chunk_text': chunk['chunk_text'],
                'similarity': sims[idx],
                'last_modified': file_meta['last_modified'],
                'size': file_meta['size'],
                'extension': file_meta['extension']
            })
    
    return results

# ====================
# 🎨 COMPONENTES DE UI
# ====================
def highlight_query_terms(text, query):
    """Destaca termos da consulta no texto"""
    if not text or not query:
        return text
    
    for word in re.split(r'\W+', query):
        if len(word) > 3:
            text = re.sub(
                f'({word})', 
                r'<span class="highlight">\1</span>', 
                text, 
                flags=re.IGNORECASE
            )
    return text

def display_progress(loader):
    """Exibe barra de progresso e status de carregamento"""
    status = st.empty()
    progress_bar = st.empty()
    file_list = st.empty()
    last_update = time.time()
    
    file_icons = {
        '.pdf': '📄',
        '.md': '📝',
        '.txt': '📄',
        '.docx': '📑',
        '.xlsx': '📊',
        '.pptx': '📽️'
    }
    
    processed_files = set()
    
    while True:
        progress_data = loader.get_progress()
        current_time = time.time()
        
        if progress_data:
            state, progress, message = progress_data
            
            if state == "complete":
                status.success(message)
                progress_bar.empty()
                file_list.empty()
                break
            elif state == "error":
                status.error(message)
                break
            else:
                status.info(message)
                
                # Atualizar barra de progresso
                progress_bar.progress(progress)
                
                # Atualizar lista de arquivos processados
                if state == "progress" and loader.current_file:
                    processed_files.add(loader.current_file)
                
                # Atualizar lista a cada 0.5 segundos
                if current_time - last_update > PROGRESS_UPDATE_INTERVAL and processed_files:
                    with file_list.container():
                        st.markdown("**Arquivos processados:**")
                        files_container = st.container()
                        with files_container:
                            for i, filename in enumerate(list(processed_files)[-10:]):
                                file_ext = os.path.splitext(filename)[1].lower()
                                icon = file_icons.get(file_ext, '📁')
                                st.markdown(f"<div class='file-item'>{icon} {filename}</div>", unsafe_allow_html=True)
                        last_update = current_time
        
        # Verificar se o carregamento foi concluído
        if loader.is_complete():
            status.success("Base de conhecimento carregada com sucesso!")
            progress_bar.empty()
            file_list.empty()
            break
            
        time.sleep(0.1)

def display_search_results(results, query, knowledge_data):
    """Exibe resultados de busca com visualização avançada"""
    if not results:
        st.markdown('<div class="info-box">🔍 Nenhum resultado encontrado. Tente reformular sua consulta.</div>', unsafe_allow_html=True)
        return
    
    # Agrupar por arquivo
    file_results = {}
    for result in results:
        filepath = result['filepath']
        if filepath not in file_results:
            file_results[filepath] = {
                'full_path': result['full_path'],
                'chunks': [],
                'max_similarity': 0,
                'extension': result['extension']
            }
        
        file_results[filepath]['chunks'].append(result)
        if result['similarity'] > file_results[filepath]['max_similarity']:
            file_results[filepath]['max_similarity'] = result['similarity']
    
    # Ordenar por relevância
    sorted_files = sorted(file_results.items(), key=lambda x: x[1]['max_similarity'], reverse=True)
    
    # Exibir resultados
    for filepath, file_data in sorted_files:
        # Obter o chunk mais relevante para preview
        best_chunk = max(file_data['chunks'], key=lambda x: x['similarity'])
        highlighted_text = highlight_query_terms(best_chunk['chunk_text'], query)
        similarity_percent = int(best_chunk['similarity'] * 100)
        
        # Ícone baseado no tipo de arquivo
        file_icons = {
            '.pdf': '📄',
            '.md': '📝',
            '.txt': '📄',
            '.docx': '📑',
            '.xlsx': '📊',
            '.pptx': '📽️'
        }
        file_icon = file_icons.get(file_data['extension'], '📁')
        
        with st.container():
            st.markdown(f"""
            <div class="search-result-card">
                <div class="result-title">{file_icon} {os.path.basename(filepath)}</div>
                <div class="result-path">📍 {filepath}</div>
                <div class="result-snippet">{highlighted_text}</div>
                <div class="result-similarity" style="color: {'#4caf50' if similarity_percent > 75 else '#ff9800'}">
                    Relevância: {similarity_percent}%
                </div>
            """, unsafe_allow_html=True)
            
            # Navegação entre chunks
            if len(file_data['chunks']) > 1:
                st.markdown("<div class='chunk-nav'>", unsafe_allow_html=True)
                for i, chunk in enumerate(file_data['chunks']):
                    if st.button(f"Trecho {i+1}", key=f"chunk_{filepath}_{i}"):
                        st.session_state.selected_chunk = chunk
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Diagramas Mermaid
            if knowledge_data and filepath in knowledge_data.get('mermaid_diagrams', {}):
                with st.expander("📊 Diagramas Relacionados", expanded=False):
                    for i, diagram in enumerate(knowledge_data['mermaid_diagrams'][filepath]):
                        st.markdown(f"```mermaid\n{diagram}\n```")
            
            st.markdown("</div>", unsafe_allow_html=True)

# ====================
# 🚀 INTERFACE PRINCIPAL
# ====================
def main():
    setup_ui()
    
    # Header
    with st.container():
        st.markdown('<div class="header-gradient">', unsafe_allow_html=True)
        st.title("🚀 EVT HyperSearch")
        st.subheader("Sistema Inteligente de Busca Corporativa")
        st.caption("Pesquise em toda a base de conhecimento com velocidade e precisão")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Inicializar carregador de conhecimento
    if 'knowledge_loader' not in st.session_state:
        st.session_state.knowledge_loader = None
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configurações")
        knowledge_dir = st.text_input("Diretório de Conhecimento:", DEFAULT_KNOWLEDGE_DIR)
        
        if st.button("Atualizar Base de Conhecimento", use_container_width=True):
            if 'knowledge_loader' in st.session_state:
                del st.session_state.knowledge_loader
            if os.path.exists(get_cache_file(knowledge_dir)):
                os.remove(get_cache_file(knowledge_dir))
            st.experimental_rerun()
            
        st.markdown("---")
        st.header("📊 Estatísticas")
        
        # Iniciar carregamento se necessário
        if st.session_state.knowledge_loader is None:
            st.session_state.knowledge_loader = KnowledgeLoader(knowledge_dir)
            st.session_state.knowledge_loader.start_loading()
        
        # Exibir estatísticas quando disponíveis
        loader = st.session_state.knowledge_loader
        if loader.is_complete():
            knowledge_data = loader.get_data()
            if knowledge_data and knowledge_data['metadata']:
                num_files = len(knowledge_data['metadata'])
                num_chunks = len(knowledge_data['chunks'])
                load_time = knowledge_data.get('load_time', 0)
                
                st.metric("Arquivos Indexados", num_files)
                st.metric("Segmentos de Texto", num_chunks)
                st.metric("Tempo de Carregamento", f"{load_time:.2f} segundos")
                
                # Tipos de arquivo
                ext_counts = pd.Series([m['extension'] for m in knowledge_data['metadata']]).value_counts()
                st.bar_chart(ext_counts)
            else:
                st.warning("Nenhum dado disponível")
        else:
            st.info("Carregando base de conhecimento...")
    
    # Área principal
    if not st.session_state.knowledge_loader.is_complete():
        with st.container():
            st.subheader("⚙️ Carregando Base de Conhecimento")
            st.info("Aguarde enquanto indexamos seus documentos...")
            display_progress(st.session_state.knowledge_loader)
    
    # Área de busca
    with st.container():
        st.markdown('<div class="search-box">', unsafe_allow_html=True)
        query = st.text_input("🔍 Busca Inteligente:", placeholder="Digite sua consulta...", key="search_query")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Processar busca se a base estiver carregada
    loader = st.session_state.knowledge_loader
    if loader.is_complete() and query:
        knowledge_data = loader.get_data()
        start_time = time.time()
        
        with st.spinner(f"🔍 Analisando {len(knowledge_data.get('chunks', []))} segmentos..."):
            results = search_knowledge(query, knowledge_data)
        
        search_time = time.time() - start_time
        
        # Exibir resultados
        st.subheader(f"📝 Resultados para: '{query}'")
        st.caption(f"Encontrados {len(results)} segmentos relevantes em {search_time:.3f} segundos")
        display_search_results(results, query, knowledge_data)
        
        # Badge de performance
        st.markdown(f"""
        <div class="performance-badge">
            ⚡ {len(knowledge_data.get('chunks', 0))} segmentos | 🕒 {search_time:.3f}s
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()