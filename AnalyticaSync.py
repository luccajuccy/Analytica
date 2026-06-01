# ==================================================
# EVT AnalyticaSync - Modo Demonstração
# ==================================================
# Versão adaptada para apresentação ao vivo.
# Sem dependências externas (SQL Server, MySQL, APIs reais).
# Todos os dados são mockados e fictícios.
# ==================================================

import os
import mimetypes
import re
import io
import time
import math
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import random
import json
import logging
import traceback
from typing import List, Dict
from functools import wraps

from dotenv import load_dotenv
from flask import (Flask, render_template, jsonify, request,
                   redirect, url_for, g, send_file, abort)
from urllib.parse import unquote
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Carregar variáveis de ambiente
load_dotenv()

# ==================================================
# Verificação do Modo Demo
# ==================================================
DEMO_MODE = os.getenv('DEMO_MODE', 'True').lower() in ('true', '1', 'yes')

# ==================================================
# Importação dos módulos de mock (quando em modo demo)
# ==================================================
if DEMO_MODE:
    try:
        from fake_weather import get_weather, get_news, scrape_climatempo
        from fake_ping import ping_ip, check_port
    except ImportError:
        # Fallback se os módulos não existirem ainda
        def get_weather(city='São Paulo,BR'):
            return {"main": {"temp": 24, "humidity": 65}, "weather": [{"description": "nublado"}], "name": "São Paulo"}
        def get_news():
            return []
        def scrape_climatempo():
            return []
        def ping_ip(ip):
            return random.random() > 0.1
        def check_port(ip, port=80):
            return random.random() > 0.1

# ==================================================
# Importação dos módulos internos
# ==================================================
from search_engine import SearchEngine
from chatbot import ChatbotEngine

# ==================================================
# Configuração do Logging
# ==================================================
LOG_FILE = "erro_log.txt"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==================================================
# Decorador de Erro Universal e Funções Seguras
# ==================================================

def safe_api(f):
    """
    Decorador que captura TODAS as exceções em rotas Flask,
    garantindo que o servidor nunca caia por erros isolados.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except FileNotFoundError as e:
            logger.error(f"Arquivo não encontrado em {f.__name__}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Arquivo não encontrado',
                'details': str(e),
                'endpoint': f.__name__
            }), 404
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido em {f.__name__}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'JSON inválido',
                'details': str(e),
                'endpoint': f.__name__
            }), 400
        except PermissionError as e:
            logger.error(f"Permissão negada em {f.__name__}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Permissão negada',
                'details': str(e),
                'endpoint': f.__name__
            }), 403
        except Exception as e:
            logger.error(f"ERRO CRÍTICO em {f.__name__}: {e}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Erro interno do servidor',
                'details': str(e),
                'endpoint': f.__name__
            }), 500
    return wrapper


def safe_read_json(filepath, default=None):
    """Lê arquivo JSON de forma segura, retornando default em caso de erro."""
    try:
        if not os.path.exists(filepath):
            logger.warning(f"Arquivo não encontrado (usando default): {filepath}")
            return default if default is not None else {}
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        logger.error(f"Erro ao ler {filepath}: {e}")
        return default if default is not None else {}


def safe_write_json(filepath, data):
    """Escreve arquivo JSON de forma segura."""
    try:
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Erro ao escrever {filepath}: {e}")
        return False


# ==================================================
# Configuração do Flask App
# ==================================================
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'analytica-demo-secret')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))  # 50MB

# Diretório de uploads
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Extensões de upload permitidas
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'xlsx', 'pptx', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Configurações do Search Engine — modo demo usa diretório local
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = SCRIPT_DIR  # Em demo, indexa arquivos locais
EXCLUDE_DIRS = [
    os.path.join(SCRIPT_DIR, 'venv'),
    os.path.join(SCRIPT_DIR, '__pycache__'),
    os.path.join(SCRIPT_DIR, '.git'),
]

search_engine = SearchEngine(ROOT_DIR, exclude_paths=EXCLUDE_DIRS)

# Inicializar Chatbot Engine
chatbot_engine = ChatbotEngine(search_engine)

# Variáveis de API (mock no demo)
CITY = os.getenv('CITY', 'São Paulo,BR')

# Pastas auxiliares
BI_FOLDER = "BI"
AC_FOLDER = "AC"
LOGS_FOLDER = 'logs'
DATA_FOLDER = 'data'
EDIFICIOS_METADATA_FILE = os.path.join(DATA_FOLDER, 'edificios_metadata.json')

for folder in [BI_FOLDER, AC_FOLDER, LOGS_FOLDER, DATA_FOLDER]:
    os.makedirs(folder, exist_ok=True)


# ==================================================
# Mapeamento de Edifícios Fictícios
# ==================================================
BUILDING_NAMES = {
    'B20': 'Torre Alpha',
    'TSUL': 'Torre Sul',
    'embarcada_II': 'Ed. Vera Cruz',
    'BETA': 'Edifício Beta',
    'GAMA': 'Shopping Gama',
}

# IPs fictícios dos edifícios
BUILDING_IPS = {
    'Torre Alpha': ['10.0.0.101 (FC)', '10.0.0.102 (CAG)'],
    'Torre Sul': ['10.0.0.111 (FC)', '10.0.0.112 (CAG)'],
    'Ed. Vera Cruz': ['10.0.0.121 (FC)', '10.0.0.122 (CAG)'],
    'Edifício Beta': ['10.0.0.131 (FC)', '10.0.0.132 (CAG)'],
    'Shopping Gama': ['10.0.0.141 (FC)', '10.0.0.142 (CAG)'],
}

# Tags CAG mockadas
CAG_TAGS_MAP = {
    'Torre Norte': ['TNORT_Ch01_Ali_AG_Temp.valor', 'TALPHA_Ch02_Ali_AG_Temp.valor'],
    'Torre Sul': ['TSUL_Ch01_Ali_AG_Temp.valor'],
    'Embarcada II': ['EMBARCADA_Ch01_Ali_AG_Temp.valor'],
    'Edifício Bridge': ['BRIDGE_Ch01_Ali_AG_Temp.valor', 'BETA_Ch02_Ali_AG_Temp.valor'],
    'Chic Shopping': ['CHICS_Ch01_Ali_AG_Temp.valor'],
}


# ==================================================
# Funções de Banco de Dados SQLite
# ==================================================
DB_PATH = os.getenv('DATABASE_PATH', os.getenv('DB_PATH', 'contatos_bms.db'))
# Resolver caminho relativo ao diretório do projeto.
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.join(SCRIPT_DIR, DB_PATH)

def get_db():
    """Conecta ao banco de dados SQLite."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    """Fecha a conexão com o banco de dados SQLite."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ==================================================
# Sistema de Cache para Edifícios (SQLite)
# ==================================================

def init_cache_db():
    """Inicializa tabela de cache."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS building_cache (
                    building_name TEXT PRIMARY KEY,
                    data_json TEXT,
                    last_updated TEXT,
                    next_update TEXT
                )
            ''')
            conn.commit()
    except Exception as e:
        logger.error(f"Error initializing cache DB: {e}")


def save_to_cache(building_name, data):
    """Salva dados no cache."""
    try:
        now = datetime.now()
        minutes_next = random.randint(15, 30)
        next_run = now + timedelta(minutes=minutes_next)

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO building_cache (building_name, data_json, last_updated, next_update)
                VALUES (?, ?, ?, ?)
            ''', (
                building_name,
                json.dumps(data, ensure_ascii=False),
                now.strftime('%Y-%m-%d %H:%M:%S'),
                next_run.strftime('%Y-%m-%d %H:%M:%S')
            ))
            conn.commit()
        logger.info(f"Cache atualizado para {building_name}. Próxima em {minutes_next} min")
    except Exception as e:
        logger.error(f"Error saving cache for {building_name}: {e}")


def get_cached_b20_data(floor=None):
    """Lê dados do cache do edifício Torre Alpha (B20)."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                'SELECT data_json, last_updated, next_update FROM building_cache WHERE building_name = ?',
                ('B20',)
            ).fetchone()

            if row:
                data = json.loads(row['data_json'])
                last_updated = row['last_updated']
                next_update = row['next_update']

                if floor and floor.upper() in data:
                    return {floor.upper(): data[floor.upper()]}, last_updated, next_update
                elif floor:
                    if floor == 'CAG' and 'CAG' in data:
                        return {'CAG': data['CAG']}, last_updated, next_update
                    return {}, last_updated, next_update

                return data, last_updated, next_update
    except Exception as e:
        logger.error(f"Error reading cache: {e}")

    return {}, None, None


def generate_mock_b20_data(floor=None):
    """Gera dados fictícios do B20 (Torre Alpha) em tempo real."""
    estrutura = {}
    andares = range(1, 21)
    equipamentos_por_andar = ['FC', 'SPLIT', 'VAV']
    status_options = ['normal', 'normal', 'normal', 'normal', 'falha']

    for andar_num in andares:
        andar_key = f"A{andar_num:02d}"

        if floor and floor.upper() != andar_key and floor.upper() != 'CAG':
            continue

        equips = {}
        for eq_name in equipamentos_por_andar:
            maquinas = {}
            for m_id in ['1', '2']:
                base_temp = 22.0 + random.uniform(-1.5, 3.0)
                setpoint = 23.0
                status = random.choice(status_options)
                maquinas[m_id] = {
                    'id': m_id,
                    'dados_individuais': [],
                    'setpoint': setpoint,
                    'temp_real': round(base_temp, 1),
                    'status': status,
                    'parametros': {},
                    'tags_processadas': [f"TALPHA_{andar_key}_{eq_name}_{m_id}"]
                }

            equips[eq_name] = {
                'nome': eq_name,
                'andar': andar_key,
                'maquinas': maquinas,
                'total_maquinas': len(maquinas),
                'maquinas_com_falha': sum(1 for m in maquinas.values() if m['status'] == 'falha'),
                'status': 'falha' if any(m['status'] == 'falha' for m in maquinas.values()) else 'normal'
            }

        estrutura[andar_key] = {
            'nome': andar_key,
            'equipamentos': equips
        }

    # Adicionar dados CAG
    estrutura['CAG'] = {
        'nome': 'Central de Água Gelada',
        'dados': [
            {'tag_original': 'TALPHA_Ch01_AG_Temp', 'valor': round(6.5 + random.uniform(-0.5, 0.5), 1),
             'tipo_dado': 'temp_real', 'qualidade': 'Good'},
            {'tag_original': 'TALPHA_Ch02_AG_Temp', 'valor': round(7.0 + random.uniform(-0.5, 0.5), 1),
             'tipo_dado': 'temp_real', 'qualidade': 'Good'},
        ],
        'equipamentos': {}
    }

    return estrutura


def update_b20_cache_job():
    """Tarefa de background para atualizar o cache."""
    logger.info("Atualizando cache B20 (Demo)...")
    try:
        data = generate_mock_b20_data()
        if data:
            save_to_cache('B20', data)
    except Exception as e:
        logger.error(f"Error updating B20 cache: {e}")

    # Atualizar resumo de edifícios
    try:
        summary = generate_buildings_summary()
        if summary:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO building_cache (building_name, data_json, last_updated, next_update)
                    VALUES (?, ?, ?, ?)
                ''', (
                    'BUILDINGS_SUMMARY',
                    json.dumps(summary, ensure_ascii=False),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
                ))
                conn.commit()
    except Exception as e:
        logger.error(f"Error updating summary cache: {e}")


def generate_buildings_summary():
    """Gera resumo fictício de todos os edifícios."""
    results = {}

    for building, tags in CAG_TAGS_MAP.items():
        if building not in results:
            results[building] = {}
        cag_data = []
        for t in tags:
            val = round(6.0 + random.uniform(0, 2.0), 1)
            cag_data.append({'tag': t, 'value': val})
        results[building]['cag'] = cag_data

    for building, hosts in BUILDING_IPS.items():
        if building not in results:
            results[building] = {}
        ping_results = []
        if hosts:
            for h in hosts:
                target = h.split(' ')[0]
                label = h.split(' ', 1)[1].strip('()') if ' ' in h else ''
                alive = ping_ip(target)
                latency = str(random.randint(1, 15)) if alive else None
                ping_results.append({
                    'host': target,
                    'label': label,
                    'status': alive,
                    'latency': latency
                })
        results[building]['pings'] = ping_results

    return results


def start_caching_jobs():
    """Inicia jobs na inicialização."""
    scheduler.add_job(
        func=update_b20_cache_job,
        trigger='date',
        run_date=datetime.now() + timedelta(seconds=5),
        id='update_B20'
    )


# ==================================================
# Filtros Jinja2
# ==================================================
@app.template_filter('slice')
def slice_filter(lst, start, end=None):
    """Filtro para fatiar listas no template."""
    if end is None:
        return lst[start:]
    return lst[start:end]


# ==================================================
# Weather History & News (Mock)
# ==================================================

def init_weather_db():
    """Inicializa tabela de histórico meteorológico."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS weather_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    city TEXT,
                    temperature REAL,
                    description TEXT,
                    min_temp REAL,
                    max_temp REAL,
                    humidity INTEGER,
                    wind_speed REAL
                )
            ''')
            conn.commit()
    except Exception as e:
        logger.error(f"Error initializing weather DB: {e}")


def update_weather_history():
    """Background task — salva dados meteorológicos fictícios."""
    try:
        weather_data = get_weather(CITY)
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
                INSERT INTO weather_history
                (timestamp, city, temperature, description, min_temp, max_temp, humidity, wind_speed)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                weather_data.get('name', 'São Paulo'),
                weather_data['main']['temp'],
                weather_data['weather'][0]['description'],
                weather_data['main']['temp_min'],
                weather_data['main']['temp_max'],
                weather_data['main']['humidity'],
                weather_data['wind']['speed']
            ))
            conn.commit()
        logger.info("Weather history atualizado (demo)")
    except Exception as e:
        logger.error(f"Error updating weather history: {e}")


def get_weather_news():
    """Retorna notícias de clima fictícias."""
    news_items = []

    # Método 1: Módulo fake_weather
    try:
        raw_news = get_news()
        for art in raw_news[:6]:
            date_str = art.get('publishedAt', '')
            try:
                if date_str:
                    dt_obj = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
                    date_fmt = dt_obj.strftime("%d/%m/%Y %H:%M")
                else:
                    date_fmt = datetime.now().strftime("%d/%m/%Y")
            except Exception:
                date_fmt = datetime.now().strftime("%d/%m/%Y")

            news_items.append({
                'title': art.get('title', 'Notícia sobre o clima'),
                'link': art.get('url', '#'),
                'thumb': art.get('urlToImage', ''),
                'summary': art.get('description', 'Notícia sobre o clima e previsão.'),
                'date': date_fmt
            })
    except Exception as e:
        logger.error(f"Erro ao buscar notícias: {e}")

    # Método 2: Fallback com Climatempo mockado
    if len(news_items) < 6:
        try:
            scraped = scrape_climatempo()
            for item in scraped:
                if len(news_items) >= 6:
                    break
                news_items.append({
                    'title': item.get('titulo', 'Previsão do tempo'),
                    'link': item.get('link', '#'),
                    'thumb': '',
                    'summary': item.get('resumo', 'Notícia sobre o clima.'),
                    'date': datetime.now().strftime("%d/%m/%Y")
                })
        except Exception as e:
            logger.error(f"Scraping error: {e}")

    return news_items[:6]


def linear_trend(values):
    if not values:
        return []
    if len(values) == 1:
        return values[:]
    x_mean = (len(values) - 1) / 2
    y_mean = sum(values) / len(values)
    denom = sum((i - x_mean) ** 2 for i in range(len(values))) or 1
    slope = sum((i - x_mean) * (value - y_mean) for i, value in enumerate(values)) / denom
    intercept = y_mean - slope * x_mean
    return [round((slope * i) + intercept, 1) for i in range(len(values))]


# ==================================================
# Demo BMS helpers (UTF-8 clean routes)
# ==================================================

WEEKDAY_LABELS = ["Domingo", "Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado"]


def dict_rows(rows):
    return [dict(row) for row in rows]


def demo_cag_temperature(building_id):
    rng = random.Random(20260526 + int(building_id) * 31)
    building_id = int(building_id)
    if building_id % 5 == 4:
        value = 10.8
    elif building_id % 5 == 1:
        value = 9.0
    else:
        value = round(rng.uniform(4.2, 7.8), 1)

    if value >= 10:
        return {
            "value": value,
            "level": "danger",
            "label": "Urgente",
            "icon": "fa-triangle-exclamation",
            "message": "Acionar tecnico para verificar a CAG.",
        }
    if value >= 9:
        return {
            "value": value,
            "level": "warn",
            "label": "Preocupante",
            "icon": "fa-circle-exclamation",
            "message": "Acompanhar tendencia e carga termica.",
        }
    return {
        "value": value,
        "level": "ok",
        "label": "Normal",
        "icon": "fa-circle-check",
        "message": "Faixa esperada entre 4C e 8C.",
    }


def get_demo_buildings():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        return dict_rows(conn.execute("SELECT * FROM buildings ORDER BY name").fetchall())


def resolve_building(identifier):
    normalized = (identifier or "").strip().lower()
    aliases = {
        "b20": "torre-alpha",
        "tsul": "torre-sul",
        "embarcada_II": "ed-vera-cruz",
        "vera-cruz": "ed-vera-cruz",
        "edificio-vera-cruz": "ed-vera-cruz",
    }
    normalized = aliases.get(normalized, normalized)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT * FROM buildings
            WHERE slug = ? OR lower(name) = ? OR replace(lower(name), ' ', '-') = ?
            """,
            (normalized, normalized, normalized),
        ).fetchone()
        if not row:
            abort(404)
        return dict(row)


def home_context():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        buildings = dict_rows(conn.execute("""
            SELECT b.*,
                   COALESCE((SELECT AVG(last_temperature) FROM sensors s WHERE s.building_id = b.id), 0) avg_temp,
                   COALESCE((SELECT COUNT(*) FROM chamados c WHERE c.building_id = b.id AND c.status = 'aberto'), 0) open_tickets,
                   COALESCE((SELECT status FROM equipamentos e WHERE e.building_id = b.id AND e.equipment_type = 'Chiller' ORDER BY e.last_event DESC LIMIT 1), 'desligado') cag_status
            FROM buildings b
            ORDER BY b.name
        """).fetchall())
        metrics = {
            "buildings": conn.execute("SELECT COUNT(*) FROM buildings").fetchone()[0],
            "sensors": conn.execute("SELECT COUNT(*) FROM sensors").fetchone()[0],
            "open_tickets": conn.execute("SELECT COUNT(*) FROM chamados WHERE status = 'aberto'").fetchone()[0],
            "critical_failures": conn.execute("SELECT COALESCE(SUM(critical_failures), 0) FROM buildings").fetchone()[0],
        }
    for building in buildings:
        building["cag_temperature"] = demo_cag_temperature(building["id"])
    return {"buildings": buildings, "metrics": metrics}


def dashboard_payload(building_slug="all", days=30, ticket_type="all", building_query=""):
    days = int(days or 30)
    start_ts = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    filters = ["c.data_abertura >= ?"]
    params = [start_ts]
    if building_slug and building_slug != "all":
        filters.append("b.slug = ?")
        params.append(building_slug)
    if building_query:
        filters.append("lower(b.name) LIKE ?")
        params.append(f"%{building_query.lower()}%")
    if ticket_type and ticket_type != "all":
        filters.append("c.temp_action = ?")
        params.append(ticket_type)
    where = " AND ".join(filters)

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        metrics = {
            "total_requests": conn.execute(
                f"SELECT COUNT(*) FROM chamados c JOIN buildings b ON b.id = c.building_id WHERE {where}",
                params,
            ).fetchone()[0],
            "open_tickets": conn.execute(
                f"SELECT COUNT(*) FROM chamados c JOIN buildings b ON b.id = c.building_id WHERE {where} AND c.status = 'aberto'",
                params,
            ).fetchone()[0],
            "critical_failures": conn.execute("SELECT COALESCE(SUM(critical_failures), 0) FROM buildings").fetchone()[0],
            "avg_external_temp": round(conn.execute(
                "SELECT AVG(temperature) FROM weather_history WHERE timestamp >= ?",
                (start_ts,),
            ).fetchone()[0] or 0, 1),
        }

        hour_rows = conn.execute(
            f"""
            SELECT strftime('%H', c.data_abertura) label, COUNT(*) value
            FROM chamados c JOIN buildings b ON b.id = c.building_id
            WHERE {where}
            GROUP BY label ORDER BY label
            """,
            params,
        ).fetchall()
        by_hour = {f"{i:02d}": 0 for i in range(24)}
        by_hour.update({row["label"]: row["value"] for row in hour_rows})

        weekday_rows = conn.execute(
            f"""
            SELECT strftime('%w', c.data_abertura) label, COUNT(*) value
            FROM chamados c JOIN buildings b ON b.id = c.building_id
            WHERE {where}
            GROUP BY label ORDER BY label
            """,
            params,
        ).fetchall()
        weekday_values = [0] * 7
        for row in weekday_rows:
            weekday_values[int(row["label"])] = row["value"]

        selected_params = []
        selected_where = []
        if building_slug and building_slug != "all":
            selected_where.append("slug = ?")
            selected_params.append(building_slug)
        if building_query:
            selected_where.append("lower(name) LIKE ?")
            selected_params.append(f"%{building_query.lower()}%")
        selected_sql = "SELECT id, name, slug, floors_count FROM buildings"
        if selected_where:
            selected_sql += " WHERE " + " AND ".join(selected_where)
        selected_sql += " ORDER BY name"
        selected_buildings = conn.execute(selected_sql, selected_params).fetchall()
        max_floor = max([row["floors_count"] for row in selected_buildings] or [1])
        floor_x = list(range(1, max_floor + 1))
        floor_y = [row["name"] for row in selected_buildings]
        floor_z = []
        for building in selected_buildings:
            floor_counts = {i: 0 for i in floor_x}
            rows = conn.execute(
                f"""
                SELECT c.floor_number, COUNT(*) value
                FROM chamados c
                WHERE c.building_id = ? AND c.data_abertura >= ?
                GROUP BY c.floor_number
                """,
                (building["id"], start_ts),
            ).fetchall()
            for row in rows:
                floor_counts[row["floor_number"]] = row["value"]
            floor_z.append([floor_counts[i] for i in floor_x])

        daily_tickets = conn.execute(
            f"""
            SELECT substr(c.data_abertura, 1, 10) day, COUNT(*) value
            FROM chamados c JOIN buildings b ON b.id = c.building_id
            WHERE {where}
            GROUP BY day ORDER BY day
            """,
            params,
        ).fetchall()
        daily_weather = {
            row["day"]: row["temp"]
            for row in conn.execute(
                "SELECT substr(timestamp, 1, 10) day, AVG(temperature) temp FROM weather_history WHERE timestamp >= ? GROUP BY day",
                (start_ts,),
            ).fetchall()
        }
        corr_x = [round(daily_weather.get(row["day"], metrics["avg_external_temp"]), 1) for row in daily_tickets]
        corr_y = [row["value"] for row in daily_tickets]
        if len(corr_x) >= 2:
            x_mean = sum(corr_x) / len(corr_x)
            y_mean = sum(corr_y) / len(corr_y)
            denom = sum((x - x_mean) ** 2 for x in corr_x) or 1
            slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(corr_x, corr_y)) / denom
            intercept = y_mean - slope * x_mean
            trend_x = [min(corr_x), max(corr_x)]
            trend_y = [round(slope * x + intercept, 2) for x in trend_x]
        else:
            trend_x, trend_y = corr_x, corr_y

        type_rows = conn.execute(
            f"""
            SELECT c.temp_action label, COUNT(*) value
            FROM chamados c JOIN buildings b ON b.id = c.building_id
            WHERE {where}
            GROUP BY c.temp_action
            """,
            params,
        ).fetchall()

        equipment_building = selected_buildings[0] if selected_buildings else conn.execute("SELECT * FROM buildings LIMIT 1").fetchone()
        eq_types = ["Fan Coil", "VAV", "Sensor Ambiente"]
        eq_x = list(range(1, equipment_building["floors_count"] + 1))
        eq_z = []
        for eq_type in eq_types:
            values = []
            for floor in eq_x:
                avg_temp = conn.execute(
                    """
                    SELECT AVG(last_temperature)
                    FROM sensors s JOIN floors f ON f.id = s.floor_id
                    WHERE s.building_id = ? AND f.floor_number = ? AND s.equipment_type = ?
                    """,
                    (equipment_building["id"], floor, eq_type),
                ).fetchone()[0]
                values.append(round(avg_temp or 23, 1))
            eq_z.append(values)

        failure_rows = conn.execute(
            """
            SELECT b.name, b.critical_failures + SUM(CASE WHEN s.status = 'offline' THEN 1 ELSE 0 END) value
            FROM buildings b LEFT JOIN sensors s ON s.building_id = b.id
            GROUP BY b.id ORDER BY value DESC
            """
        ).fetchall()

        outliers = dict_rows(conn.execute(
            """
            SELECT b.name building, f.label floor, th.temperature, th.timestamp
            FROM temp_history th
            JOIN buildings b ON b.id = th.building_id
            LEFT JOIN floors f ON f.id = th.floor_id
            WHERE th.timestamp >= ? AND (th.temperature > 28 OR th.temperature < 20)
            ORDER BY th.timestamp DESC LIMIT 12
            """,
            (start_ts,),
        ).fetchall())

    return {
        "metrics": metrics,
        "by_hour": {"labels": list(by_hour.keys()), "values": list(by_hour.values())},
        "by_weekday": {"labels": WEEKDAY_LABELS, "values": weekday_values},
        "floor_heatmap": {"x": floor_x, "y": floor_y, "z": floor_z},
        "correlation": {"x": corr_x, "y": corr_y, "trend_x": trend_x, "trend_y": trend_y},
        "by_type": {"labels": [row["label"] for row in type_rows], "values": [row["value"] for row in type_rows]},
        "equipment_heatmap": {"x": eq_x, "y": eq_types, "z": eq_z},
        "failures": {"labels": [row["name"] for row in failure_rows], "values": [row["value"] for row in failure_rows]},
        "outliers": outliers,
    }


def building_context(identifier):
    building = resolve_building(identifier)
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        summary = {
            "total_sensors": conn.execute("SELECT COUNT(*) FROM sensors WHERE building_id = ?", (building["id"],)).fetchone()[0],
            "avg_temp": round(conn.execute("SELECT AVG(last_temperature) FROM sensors WHERE building_id = ?", (building["id"],)).fetchone()[0] or 0, 1),
            "open_tickets": conn.execute("SELECT COUNT(*) FROM chamados WHERE building_id = ? AND status = 'aberto'", (building["id"],)).fetchone()[0],
        }
        temp_rows = conn.execute(
            """
            SELECT substr(timestamp, 12, 5) label, AVG(temperature) value
            FROM temp_history
            WHERE building_id = ? AND timestamp >= ?
            GROUP BY label ORDER BY label
            """,
            (building["id"], datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")),
        ).fetchall()
        if not temp_rows:
            temp_rows = conn.execute(
                """
                SELECT substr(timestamp, 12, 5) label, AVG(temperature) value
                FROM temp_history WHERE building_id = ?
                GROUP BY label ORDER BY label LIMIT 96
                """,
                (building["id"],),
            ).fetchall()
        equipment_rows = conn.execute(
            "SELECT status, COUNT(*) value FROM equipamentos WHERE building_id = ? GROUP BY status",
            (building["id"],),
        ).fetchall()
        tickets = dict_rows(conn.execute(
            "SELECT * FROM chamados WHERE building_id = ? ORDER BY data_abertura DESC LIMIT 10",
            (building["id"],),
        ).fetchall())
        now = datetime.now()
        for ticket in tickets:
            opened = datetime.strptime(ticket["data_abertura"], "%Y-%m-%d %H:%M:%S")
            overdue = ticket["status"] == "aberto" and (now - opened).total_seconds() > 180
            ticket["sla_status"] = "Estourado" if overdue else "Dentro do prazo"
            ticket["sla_overdue"] = overdue
        cag_ops = dict_rows(conn.execute(
            "SELECT * FROM cag_operations WHERE building_id = ? ORDER BY event_time DESC LIMIT 12",
            (building["id"],),
        ).fetchall())
        floors = conn.execute(
            "SELECT id, floor_number, label FROM floors WHERE building_id = ? ORDER BY floor_number",
            (building["id"],),
        ).fetchall()

        floor_system_rows = []
        for floor in floors:
            rng = random.Random((building["id"] * 1000) + floor["floor_number"])
            fan_on = rng.random() > 0.14
            setpoint = round(rng.uniform(21.5, 24.0), 1)
            sensor_temp = round(setpoint + rng.uniform(-0.8, 1.9), 1)
            vag = rng.randint(28, 92) if fan_on else rng.randint(0, 18)
            alarm = (abs(sensor_temp - setpoint) > 1.6) or (rng.random() < 0.08)
            floor_system_rows.append({
                "floor": floor["label"],
                "fancoil_status": "Ligado" if fan_on else "Desligado",
                "vag_percent": vag,
                "setpoint_temp": setpoint,
                "sensor_temp": sensor_temp,
                "alarm": "Sim" if alarm else "Nao",
                "lighting": "Ligada" if rng.random() > 0.18 else "Desligada",
            })

    return {
        "building": building,
        "summary": summary,
        "temp_series": {
            "labels": json.dumps([row["label"] for row in temp_rows]),
            "values": json.dumps([round(row["value"], 1) for row in temp_rows]),
        },
        "equipment_status": {
            "labels": json.dumps([row["status"] for row in equipment_rows]),
            "values": json.dumps([row["value"] for row in equipment_rows]),
        },
        "tickets": tickets,
        "cag_ops": cag_ops,
        "floor_system_rows": floor_system_rows,
    }


def edf_context():
    # Coordenadas GPS demo para cada edifício (São Paulo region)
    BUILDING_COORDS = {
        'Torre Alpha':       {'lat': -23.5605, 'lng': -46.6563},
        'Torre Sul':         {'lat': -23.5732, 'lng': -46.6835},
        'Ed. Vera Cruz':     {'lat': -23.5489, 'lng': -46.6388},
        'Edifício Beta':     {'lat': -23.5850, 'lng': -46.6720},
        'Shopping Gama':     {'lat': -23.5640, 'lng': -46.6510},
    }

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = dict_rows(conn.execute("""
            SELECT b.*,
                   COALESCE((SELECT AVG(last_temperature) FROM sensors s WHERE s.building_id = b.id), 0) avg_temp,
                   COALESCE((SELECT COUNT(*) FROM sensors s WHERE s.building_id = b.id), 0) total_sensors,
                   COALESCE((SELECT COUNT(*) FROM chamados c WHERE c.building_id = b.id AND c.status = 'aberto'), 0) open_tickets,
                   COALESCE((SELECT COUNT(*) FROM chamados c WHERE c.building_id = b.id), 0) total_tickets,
                   COALESCE((SELECT status FROM equipamentos e WHERE e.building_id = b.id AND e.equipment_type = 'Chiller' ORDER BY e.last_event DESC LIMIT 1), 'desligado') cag_status
            FROM buildings b
            ORDER BY b.name
        """).fetchall())
        for row in rows:
            row["avg_temp"] = round(row["avg_temp"] or 0, 1)
            row["ticket_ratio"] = min(100, int((row["open_tickets"] / max(row["total_tickets"], 1)) * 100))

            # Mock ping & availability
            is_online = row.get("status", "offline") == "online"
            row["ping_ms"] = random.randint(3, 18) if is_online else None
            row["availability"] = round(random.uniform(97.0, 99.99), 2) if is_online else round(random.uniform(0.0, 15.0), 2)

            # Sparkline: últimos 7 dias de disponibilidade
            if is_online:
                row["availability_history"] = [round(random.uniform(96.0, 100.0), 1) for _ in range(7)]
            else:
                base = random.uniform(0, 30)
                row["availability_history"] = [round(random.uniform(base - 10, base + 10), 1) for _ in range(7)]

            # IPs do edifício
            building_name = row.get("name", "")
            ips_raw = BUILDING_IPS.get(building_name, [])
            ips_list = []
            for ip_str in ips_raw:
                parts = ip_str.split(' ', 1)
                ip_addr = parts[0]
                label = parts[1].strip('()') if len(parts) > 1 else ''
                ip_ping = random.randint(3, 20) if is_online else None
                ips_list.append({'ip': ip_addr, 'label': label, 'ping': ip_ping, 'online': is_online})
            row["ips"] = ips_list

            # Coordenadas GPS
            coords = BUILDING_COORDS.get(building_name, {'lat': -23.55 + random.uniform(-0.03, 0.03), 'lng': -46.65 + random.uniform(-0.03, 0.03)})
            row["lat"] = coords["lat"]
            row["lng"] = coords["lng"]

    return {"buildings": rows}


def recent_notifications(limit=20):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return dict_rows(rows)


def cag_operations(limit=40):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT c.*, b.name building_name
            FROM cag_operations c JOIN buildings b ON b.id = c.building_id
            ORDER BY c.event_time DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return dict_rows(rows)


# ==================================================
# ROTAS FLASK — Páginas Principais
# ==================================================

@app.route('/')
def index():
    return redirect(url_for('home'))


@app.route('/home')
def home():
    """Página inicial."""
    try:
        search_engine.start_indexing()
    except Exception:
        pass
    return render_template('home_demo.html', **home_context())


@app.route('/TSUL')
def TSUL():
    """Página do edifício Torre Sul."""
    # Gerar dados mockados para Torre Sul (similar ao B20)
    dados = generate_mock_building_data('Torre Sul', floors=15)
    return redirect(url_for('building_page', nome='torre-sul'))


@app.route('/embarcada_II')
def embarcada_II():
    """Página do edifício Ed. Vera Cruz."""
    dados = generate_mock_building_data('Ed. Vera Cruz', floors=10)
    return redirect(url_for('building_page', nome='ed-vera-cruz'))


def generate_mock_building_data(building_name, floors=10):
    """Gera dados fictícios para qualquer edifício."""
    prefix = building_name.replace(' ', '').replace('.', '')[:4].upper()
    estrutura = {}

    for andar_num in range(1, floors + 1):
        andar_key = f"A{andar_num:02d}"
        equips = {}
        for eq_name in ['FC', 'SPLIT', 'VAV']:
            maquinas = {}
            for m_id in ['1', '2']:
                base_temp = 22.0 + random.uniform(-1.5, 3.0)
                status = 'normal' if random.random() > 0.1 else 'falha'
                maquinas[m_id] = {
                    'id': m_id,
                    'dados_individuais': [],
                    'setpoint': 23.0,
                    'temp_real': round(base_temp, 1),
                    'status': status,
                    'parametros': {},
                    'tags_processadas': [f"{prefix}_{andar_key}_{eq_name}_{m_id}"]
                }
            equips[eq_name] = {
                'nome': eq_name,
                'andar': andar_key,
                'maquinas': maquinas,
                'total_maquinas': len(maquinas),
                'maquinas_com_falha': sum(1 for m in maquinas.values() if m['status'] == 'falha'),
                'status': 'falha' if any(m['status'] == 'falha' for m in maquinas.values()) else 'normal'
            }
        estrutura[andar_key] = {
            'nome': andar_key,
            'equipamentos': equips
        }
    return estrutura


@app.route('/resumocag')
def resumocag():
    return render_template('cag.html', operations=cag_operations())


@app.route('/cag')
def cag_page():
    return render_template('cag.html', operations=cag_operations())


@app.route('/dashboard')
def dashboard():
    """Dashboard com dados de chamados (convertido do Streamlit)."""
    return render_template('dashboard_bms.html', buildings=get_demo_buildings())


@app.route('/api/dashboard-data')
def api_dashboard_data():
    return jsonify(dashboard_payload(
        request.args.get('building', 'all'),
        request.args.get('days', 30),
        request.args.get('type', 'all'),
        request.args.get('building_query', '').strip()
    ))


@app.route('/edificio/<nome>')
def building_page(nome):
    return render_template('edificio.html', **building_context(nome))


@app.route('/notifications')
def notifications_page():
    return render_template('notifications.html', notifications=recent_notifications(50))


@app.route('/api/notifications')
def api_notifications():
    limit = request.args.get('limit', 20, type=int)
    return jsonify({'notifications': recent_notifications(limit)})


def get_chamados_dashboard_data():
    """Lê dados de chamados do SQLite para o dashboard."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row

            # Total de chamados
            total = conn.execute('SELECT COUNT(*) as cnt FROM chamados').fetchone()
            total_chamados = total['cnt'] if total else 0

            # Chamados por status
            status_rows = conn.execute(
                'SELECT status, COUNT(*) as cnt FROM chamados GROUP BY status'
            ).fetchall()
            status_data = {row['status']: row['cnt'] for row in status_rows}

            # Chamados por local (edifício)
            local_rows = conn.execute(
                'SELECT local, COUNT(*) as cnt FROM chamados GROUP BY local ORDER BY cnt DESC LIMIT 10'
            ).fetchall()
            locais = [row['local'] for row in local_rows]
            locais_counts = [row['cnt'] for row in local_rows]

            # Chamados por tipo (OP vs IN)
            tipo_rows = conn.execute(
                "SELECT CASE WHEN tipo LIKE 'OP%' THEN 'Ordem Preventiva' ELSE 'Incidente' END as tipo_grupo, COUNT(*) as cnt FROM chamados GROUP BY tipo_grupo"
            ).fetchall()
            tipos = {row['tipo_grupo']: row['cnt'] for row in tipo_rows}

            # Chamados por prioridade
            prio_rows = conn.execute(
                'SELECT prioridade, COUNT(*) as cnt FROM chamados GROUP BY prioridade'
            ).fetchall()
            prioridades = {row['prioridade']: row['cnt'] for row in prio_rows}

            # Últimos 10 chamados
            recentes = conn.execute(
                'SELECT * FROM chamados ORDER BY data_abertura DESC LIMIT 10'
            ).fetchall()
            recentes_list = [dict(r) for r in recentes]

            return {
                'total_chamados': total_chamados,
                'status_data': json.dumps(status_data, ensure_ascii=False),
                'locais': json.dumps(locais, ensure_ascii=False),
                'locais_counts': json.dumps(locais_counts),
                'tipos': json.dumps(tipos, ensure_ascii=False),
                'prioridades': json.dumps(prioridades, ensure_ascii=False),
                'recentes': recentes_list
            }
    except Exception as e:
        logger.error(f"Erro ao carregar dados de chamados: {e}")
        return {
            'total_chamados': 0,
            'status_data': '{}',
            'locais': '[]',
            'locais_counts': '[]',
            'tipos': '{}',
            'prioridades': '{}',
            'recentes': []
        }


# ==================================================
# B20 (Torre Alpha) Dashboard
# ==================================================

@app.route('/B20')
def b20_dashboard():
    return redirect(url_for('building_page', nome='torre-alpha'))
    """Página principal do dashboard Torre Alpha (B20)."""
    try:
        andar_selecionado = request.args.get('andar', '').upper()

        # Busca dados do CACHE
        dados, last_upd, next_upd = get_cached_b20_data(
            andar_selecionado if andar_selecionado else None
        )

        # Se cache vazio, gera dados mock
        if not dados:
            dados = generate_mock_b20_data(
                andar_selecionado if andar_selecionado else None
            )
            last_upd = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            next_upd = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')

        template_data = {
            'building_name': 'Torre Alpha',
            'andares': dados,
            'andar_selecionado': andar_selecionado,
            'timestamp': last_upd,
            'next_update': next_upd,
            'total_andares': len([k for k in dados.keys() if k != 'CAG']),
            'total_equipamentos': sum(
                len(andar.get('equipamentos', {}))
                for k, andar in dados.items() if k != 'CAG'
            ),
            'andares_com_falha': sum(
                1 for k, andar in dados.items()
                if k != 'CAG' and any(
                    eq.get('status') == 'falha'
                    for eq in andar.get('equipamentos', {}).values()
                )
            )
        }

        return render_template('B20.html', **template_data)

    except Exception as e:
        logger.error(f"Erro no dashboard B20: {e}\n{traceback.format_exc()}")
        return f"Erro interno: {str(e)}", 500


@app.route('/B20/api/dados')
def b20_api_dados():
    """API JSON para dados B20."""
    try:
        andar = request.args.get('andar', '')
        dados, last, next_ = get_cached_b20_data(andar if andar else None)

        if not dados:
            dados = generate_mock_b20_data(andar if andar else None)
            last = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            next_ = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')

        return jsonify({
            'success': True,
            'dados': dados,
            'timestamp': last,
            'next_update': next_,
            'total_andares': len(dados),
            'filtro_andar': andar
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/B20/api/detalhes/<andar>/<equipamento>')
def b20_detalhes_equipamento(andar, equipamento):
    """API para detalhes de um equipamento."""
    try:
        dados, _, _ = get_cached_b20_data()
        if not dados:
            dados = generate_mock_b20_data()

        if andar in dados and 'equipamentos' in dados[andar] and equipamento in dados[andar]['equipamentos']:
            equipamento_data = dados[andar]['equipamentos'][equipamento]
            detalhes = {
                'equipamento': equipamento_data,
                'andar': andar,
                'todas_tags': []
            }
            for maq_id, maq_data in equipamento_data['maquinas'].items():
                for dado in maq_data.get('dados_individuais', []):
                    detalhes['todas_tags'].append(dado)

            return jsonify({
                'success': True,
                'detalhes': detalhes,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Equipamento não encontrado'
            }), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================================================
# API de Indexação e Busca
# ==================================================

@app.route('/api/indexing_status')
def indexing_status():
    """API para status da indexação."""
    return jsonify(search_engine.get_status())


@app.route('/search', methods=['GET', 'POST'])
def search():
    """Sistema de busca + upload de documentos."""
    upload_result = None

    # POST = upload de arquivo
    if request.method == 'POST':
        upload_result = handle_file_upload()

    query = request.args.get('q', '')
    results = []

    status = search_engine.get_status()
    logger.info(f"Search - Query: '{query}', Index: {status.get('total_indexed', 0)}")

    if query:
        results = search_engine.search(query)
    else:
        if status.get('total_indexed', 0) == 0 and not status.get('is_indexing', False):
            try:
                search_engine.start_indexing()
            except Exception:
                pass

    suggestions = search_engine.get_suggestions()

    return render_template('search.html',
                           query=query,
                           results=results,
                           suggestions=suggestions,
                           indexing_status=status,
                           upload_result=upload_result)


def handle_file_upload():
    """Processa upload de arquivo com categorização TFI."""
    try:
        if 'file' not in request.files:
            return {'success': False, 'message': 'Nenhum arquivo selecionado'}

        file = request.files['file']
        if file.filename == '':
            return {'success': False, 'message': 'Nenhum arquivo selecionado'}

        if not allowed_file(file.filename):
            return {'success': False, 'message': f'Tipo de arquivo não permitido. Aceitos: {", ".join(ALLOWED_EXTENSIONS)}'}

        # Salvar arquivo
        filename = hashlib.md5(
            (file.filename + datetime.now().isoformat()).encode()
        ).hexdigest()[:12] + '_' + file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Comentário do usuário
        user_comment = request.form.get('comment', '')

        # Classificar documento
        extracted_text = ''
        try:
            from tfi_classifier import classify_uploaded_file, extract_text_from_file
            extracted_text = extract_text_from_file(filepath)
            category, confidence = classify_uploaded_file(filepath, user_comment)
        except ImportError:
            category = 'Geral'
            confidence = 0.5
        except Exception as e:
            logger.error(f"Erro na classificação TFI: {e}")
            category = 'Geral'
            confidence = 0.0

        # Armazenar no banco de conhecimento
        try:
            search_engine.db.add_file({
                'path': filepath,
                'real_path': filepath,
                'title': file.filename,
                'content': f'[Upload] Categoria: {category}. Comentário: {user_comment}',
                'type': file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'unknown',
                'mime': file.content_type or 'application/octet-stream',
                'size': f"{os.path.getsize(filepath) / 1024:.1f} KB",
                'size_bytes': os.path.getsize(filepath),
                'modified': datetime.now().isoformat(),
                'hash': hashlib.md5(open(filepath, 'rb').read()).hexdigest()
            })
            with sqlite3.connect(search_engine.db.db_path) as upload_conn:
                upload_conn.execute('''
                    CREATE TABLE IF NOT EXISTS uploaded_documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        path TEXT NOT NULL,
                        title TEXT NOT NULL,
                        extracted_text TEXT,
                        category TEXT,
                        confidence REAL,
                        comment TEXT,
                        uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                upload_conn.execute('''
                    INSERT INTO uploaded_documents
                    (path, title, extracted_text, category, confidence, comment, uploaded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    filepath, file.filename, extracted_text, category,
                    float(confidence), user_comment,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                upload_conn.commit()
        except Exception as e:
            logger.error(f"Erro ao salvar no knowledge DB: {e}")

        return {
            'success': True,
            'message': f'Arquivo "{file.filename}" enviado e classificado com sucesso!',
            'filename': file.filename,
            'category': category,
            'confidence': round(confidence * 100, 1),
            'filepath': filepath
        }

    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        return {'success': False, 'message': f'Erro ao processar upload: {str(e)}'}


# ==================================================
# APIs de Likes / Rating
# ==================================================

@app.route('/api/like', methods=['POST'])
def api_like_file():
    try:
        data = request.get_json()
        file_path = data.get('path', '')
        if not file_path:
            return jsonify({'error': 'Path is required'}), 400
        new_likes = search_engine.db.like_file(file_path)
        return jsonify({'success': True, 'likes': new_likes, 'path': file_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dislike', methods=['POST'])
def api_dislike_file():
    try:
        data = request.get_json()
        file_path = data.get('path', '')
        if not file_path:
            return jsonify({'error': 'Path is required'}), 400
        new_dislikes = search_engine.db.dislike_file(file_path)
        return jsonify({'success': True, 'dislikes': new_dislikes, 'path': file_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/likes/<path:file_path>')
def api_get_likes(file_path):
    try:
        ratings = search_engine.db.get_file_likes(file_path)
        return jsonify(ratings)
    except Exception as e:
        return jsonify({'likes': 0, 'dislikes': 0})


@app.route('/api/top_rated')
def api_top_rated():
    try:
        limit = request.args.get('limit', 10, type=int)
        top_files = search_engine.db.get_top_rated(limit)
        return jsonify({'top_rated': top_files})
    except Exception as e:
        return jsonify({'top_rated': []})


# ==================================================
# APIs do Chatbot
# ==================================================

@app.route('/api/chatbot/message', methods=['POST'])
def api_chatbot_message():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        if not user_message:
            return jsonify({'error': 'Mensagem vazia'}), 400
        response_data = chatbot_engine.process_message(user_message)
        if response_data.get('success', False):
            try:
                documents = response_data.get('documents', [])
                search_engine.db.save_chat_message(
                    user_message,
                    response_data.get('message', ''),
                    documents if documents else None
                )
            except Exception as e:
                logger.warning(f"Erro ao salvar histórico do chat: {e}")
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Erro no chatbot: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro ao processar mensagem. Tente novamente.',
            'type': 'error',
            'documents': [],
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/chatbot/history', methods=['GET'])
def api_chatbot_history():
    try:
        limit = request.args.get('limit', 50, type=int)
        history = search_engine.db.get_chat_history(limit)
        return jsonify({'success': True, 'history': history, 'count': len(history)})
    except Exception as e:
        return jsonify({'success': False, 'history': [], 'count': 0}), 500


@app.route('/api/chatbot/clear', methods=['POST'])
def api_chatbot_clear():
    try:
        success = search_engine.db.clear_chat_history()
        if success:
            return jsonify({'success': True, 'message': 'Histórico limpo com sucesso'})
        return jsonify({'success': False, 'message': 'Erro ao limpar histórico'}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/chatbot/status', methods=['GET'])
def api_chatbot_status():
    try:
        status = chatbot_engine.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({'ready': False, 'error': str(e)}), 500


# ==================================================
# Rota para servir arquivos indexados
# ==================================================

@app.route('/knowledge_file/<path:path>')
def serve_knowledge_file(path):
    """Rota segura para servir arquivos indexados."""
    try:
        decoded_path = unquote(path)
        # Tenta servir do diretório local
        if os.path.exists(decoded_path):
            full_path = decoded_path
        else:
            full_path = os.path.join(ROOT_DIR, decoded_path.replace('/', os.sep))
            full_path = os.path.normpath(full_path)

        if not os.path.exists(full_path):
            abort(404)

        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = 'application/octet-stream'

        filename = os.path.basename(full_path)
        inline_types = ['application/pdf', 'image/', 'text/', 'audio/', 'video/']
        is_inline = any(mime_type.startswith(t) for t in inline_types)

        if is_inline:
            response = send_file(full_path, mimetype=mime_type, as_attachment=False)
        else:
            response = send_file(full_path, mimetype=mime_type, as_attachment=True)

        response.headers['Cache-Control'] = 'public, max-age=3600'
        return response

    except Exception as e:
        logger.error(f"Erro ao servir arquivo: {e}")
        abort(500)


# ==================================================
# Gerenciamento de Emails
# ==================================================

@app.route('/gerenciar_emails')
def gerenciar_emails():
    return render_template('gerenciar_emails.html')


@app.route('/api/buildings_with_emails')
@safe_api
def get_buildings_with_emails():
    buildings = {'BI': {}, 'AC': {}}
    for folder_key, folder_path in [('BI', BI_FOLDER), ('AC', AC_FOLDER)]:
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                if filename.endswith('.txt'):
                    building_name = filename[:-4]
                    filepath = os.path.join(folder_path, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        emails = [line.strip() for line in f.readlines() if line.strip()]
                    buildings[folder_key][building_name] = emails
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT name, slug FROM buildings ORDER BY name").fetchall()
        for index, row in enumerate(rows):
            folder_key = 'BI' if index % 2 else 'AC'
            other_key = 'AC' if folder_key == 'BI' else 'BI'
            if row['name'] not in buildings[folder_key] and row['name'] not in buildings[other_key]:
                buildings[folder_key][row['name']] = [f"operacao.{row['slug']}@exemplo.com"]
    except Exception as exc:
        logger.error(f"Erro ao carregar edificios para emails: {exc}")
    return jsonify(buildings)


@app.route('/api/save_emails', methods=['POST'])
def save_emails():
    try:
        data = request.get_json()
        folder = data.get('folder')
        building = data.get('building')
        emails = data.get('emails', '')

        if not folder or not building:
            return jsonify({'success': False, 'message': 'Pasta e edifício são obrigatórios'}), 400

        if folder not in ['BI', 'AC']:
            return jsonify({'success': False, 'message': 'Pasta deve ser BI ou AC'}), 400

        target_folder = BI_FOLDER if folder == 'BI' else AC_FOLDER
        filepath = os.path.join(target_folder, f"{building}.txt")
        os.makedirs(target_folder, exist_ok=True)

        email_list = re.split(r'[,;\n\r]+', emails)
        email_list = [email.strip() for email in email_list if email.strip()]

        with open(filepath, 'w', encoding='utf-8') as f:
            for email in email_list:
                f.write(f"{email}\n")

        return jsonify({'success': True, 'message': f'Emails salvos para {building}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================================================
# API de Metadados de Edifícios
# ==================================================

def load_edificios_metadata():
    return safe_read_json(EDIFICIOS_METADATA_FILE, {"edificios": {}})

def save_edificios_metadata_file(data):
    return safe_write_json(EDIFICIOS_METADATA_FILE, data)

@app.route('/api/edificios_metadata')
@safe_api
def get_edificios_metadata():
    data = load_edificios_metadata()
    return jsonify({'success': True, 'edificios': data.get('edificios', {})})


@app.route('/api/edificio_metadata/<edificio>')
@safe_api
def get_edificio_metadata(edificio):
    data = load_edificios_metadata()
    edificios = data.get('edificios', {})
    if edificio in edificios:
        return jsonify({'success': True, 'edificio': edificio, 'metadata': edificios[edificio]})
    return jsonify({
        'success': True,
        'edificio': edificio,
        'metadata': {
            'posto': 'BI', 'chillers': 2, 'operacao_24h': False,
            'coordenadas': '', 'mensagem_partida': 'Bom dia, a CAG partiu sem anormalidades.',
            'mensagem_desligamento': 'Boa tarde, a CAG foi desligada conforme programado.'
        }
    })


@app.route('/api/edificio_metadata', methods=['POST'])
@safe_api
def save_edificio_metadata():
    request_data = request.get_json()
    edificio = request_data.get('edificio')
    if not edificio:
        return jsonify({'success': False, 'message': 'Nome obrigatório'}), 400

    metadata = {
        'posto': request_data.get('posto', 'BI'),
        'chillers': request_data.get('chillers', 2),
        'operacao_24h': request_data.get('operacao_24h', False),
        'coordenadas': request_data.get('coordenadas', ''),
        'mensagem_partida': request_data.get('mensagem_partida', ''),
        'mensagem_desligamento': request_data.get('mensagem_desligamento', '')
    }

    data = load_edificios_metadata()
    if 'edificios' not in data:
        data['edificios'] = {}
    data['edificios'][edificio] = metadata

    if save_edificios_metadata_file(data):
        return jsonify({'success': True, 'message': f'Metadados de {edificio} salvos'})
    return jsonify({'success': False, 'message': 'Erro ao salvar'}), 500


# ==================================================
# ROTAS DE CONTATOS (PLANO DE CHAMADOS) — CRUD
# ==================================================

@app.route('/plannc')
def plannc():
    """Lista todos os contatos com filtros."""
    db = get_db()
    try:
        contatos = db.execute('SELECT * FROM contatos ORDER BY nome').fetchall()
        funcoes = db.execute('SELECT DISTINCT funcao FROM contatos WHERE funcao IS NOT NULL ORDER BY funcao').fetchall()
        funcoes_lista = [f['funcao'] for f in funcoes]
    except sqlite3.OperationalError:
        db.execute('''
            CREATE TABLE IF NOT EXISTS contatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                predio TEXT, empresa TEXT, funcao TEXT, categoria TEXT,
                acao TEXT, nome TEXT, telefone1 TEXT, telefone2 TEXT,
                email TEXT, observacao TEXT, data_atualizacao TEXT
            )
        ''')
        db.commit()
        contatos = []
        funcoes_lista = []
    return render_template('plano_de_chamados.html', contatos=contatos, funcoes_disponiveis=funcoes_lista)


@app.route('/add_contato', methods=['GET', 'POST'])
def add_contato():
    if request.method == 'POST':
        data_atualizacao = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db = get_db()
        try:
            db.execute(
                'INSERT INTO contatos (predio, empresa, funcao, categoria, acao, nome, telefone1, telefone2, email, observacao, data_atualizacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (request.form['predio'], request.form['empresa'], request.form['funcao'],
                 request.form['categoria'], request.form['acao'], request.form['nome'],
                 request.form['telefone1'], request.form['telefone2'], request.form['email'],
                 request.form['observacao'], data_atualizacao)
            )
            db.commit()
            return render_template('add_contato.html', message={'type': 'success', 'text': 'Contato adicionado com sucesso!'})
        except Exception as e:
            return render_template('add_contato.html', message={'type': 'error', 'text': f'Erro: {e}'})
    return render_template('add_contato.html')


@app.route('/edit_contato/<int:contato_id>', methods=['GET', 'POST'])
def edit_contato(contato_id):
    db = get_db()
    contato = db.execute('SELECT * FROM contatos WHERE id = ?', (contato_id,)).fetchone()
    if contato is None:
        return "Contato não encontrado", 404

    if request.method == 'POST':
        try:
            db.execute(
                'UPDATE contatos SET predio=?, empresa=?, funcao=?, categoria=?, acao=?, nome=?, telefone1=?, telefone2=?, email=?, observacao=? WHERE id=?',
                (request.form['predio'], request.form['empresa'], request.form['funcao'],
                 request.form['categoria'], request.form['acao'], request.form['nome'],
                 request.form['telefone1'], request.form['telefone2'], request.form['email'],
                 request.form['observacao'], contato_id)
            )
            db.commit()
            contato = db.execute('SELECT * FROM contatos WHERE id = ?', (contato_id,)).fetchone()
            return render_template('edit_contato.html', contato=contato,
                                   message={'type': 'success', 'text': 'Contato atualizado!'})
        except Exception as e:
            return render_template('edit_contato.html', contato=contato,
                                   message={'type': 'error', 'text': f'Erro: {e}'})
    return render_template('edit_contato.html', contato=contato)


@app.route('/delete_contato/<int:contato_id>', methods=['POST'])
def delete_contato(contato_id):
    db = get_db()
    try:
        db.execute('DELETE FROM contatos WHERE id = ?', (contato_id,))
        db.commit()
    except Exception as e:
        logger.error(f"Erro ao deletar contato {contato_id}: {e}")
    return redirect(url_for('plannc'))


# ==================================================
# API Detalhes de Edifício
# ==================================================

@app.route('/api/building_details/<name>')
def api_building_details(name):
    name_decoded = unquote(name)
    response = {'name': name_decoded, 'contacts': [], 'real_time': None}

    try:
        db = get_db()
        try:
            contatos = db.execute(
                "SELECT nome, funcao, telefone1, email, categoria FROM contatos WHERE predio LIKE ? OR predio LIKE ? ORDER BY funcao",
                (f"{name_decoded}%", f"%{name_decoded}%")
            ).fetchall()
        except Exception:
            contatos = []
        response['contacts'] = [dict(c) for c in contatos]
    except Exception as e:
        logger.error(f"Erro buscando contatos para {name_decoded}: {e}")

    # Dados real-time mockados
    response['real_time'] = {
        'status': 'Ativo',
        'alerts': random.randint(0, 3),
        'last_update': datetime.now().strftime('%H:%M:%S'),
        'message': f'Monitoramento ativo. {random.randint(10, 20)} andares online.'
    }

    return jsonify(response)


# ==================================================
# Clima
# ==================================================

@app.route('/clima')
def clima():
    """Página de clima com histórico e notícias mockadas."""
    try:
        current_weather = get_weather(CITY)

        history_labels = []
        history_temps = []
        history_min = []
        history_max = []

        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                start_ts = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')
                cursor = conn.execute(
                    'SELECT * FROM weather_history WHERE timestamp >= ? ORDER BY timestamp',
                    (start_ts,)
                )
                rows = cursor.fetchall()
                if len(rows) > 72:
                    step = max(1, len(rows) // 56)
                    rows = rows[::step]

                for row in rows:
                    try:
                        dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                        history_labels.append(dt.strftime('%d/%m %Hh'))
                    except Exception:
                        history_labels.append('--:--')
                    history_temps.append(round(row['temperature'], 1))
                    history_min.append(round(row['min_temp'], 1))
                    history_max.append(round(row['max_temp'], 1))
        except Exception as e:
            logger.error(f"Error fetching weather history: {e}")

        if not history_temps:
            rng = random.Random(20260526)
            base = datetime.now() - timedelta(days=7)
            for index in range(0, 7 * 8):
                ts = base + timedelta(hours=index * 3)
                hour_wave = math.sin((ts.hour - 7) / 24 * math.tau) * 4.4
                trend_wave = math.sin(index / 14) * 1.2
                temp = round(22.0 + hour_wave + trend_wave + rng.uniform(-0.8, 0.8), 1)
                history_labels.append(ts.strftime('%d/%m %Hh'))
                history_temps.append(temp)
                history_min.append(round(temp - rng.uniform(1.5, 2.8), 1))
                history_max.append(round(temp + rng.uniform(1.4, 3.0), 1))

        history_trend = linear_trend(history_temps)

        news_items = get_weather_news()

        return render_template('clima_demo.html',
                               weather=current_weather,
                               history_labels=history_labels,
                               history_temps=history_temps,
                               history_min=history_min,
                               history_max=history_max,
                               history_trend=history_trend,
                               news=news_items,
                               timestamp=datetime.now().strftime('%d/%m/%Y %H:%M'))

    except Exception as e:
        logger.error(f"Error in /clima: {e}")
        return render_template('clima_demo.html', error=str(e), timestamp=datetime.now().strftime('%d/%m/%Y %H:%M'))


@app.route('/help')
def help_page():
    return render_template('help_demo.html')


@app.route('/edf')
def edf_page():
    """Página de edifícios com resumo."""
    summary_data = {}
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT data_json FROM building_cache WHERE building_name = 'BUILDINGS_SUMMARY'"
            ).fetchone()
            if row:
                summary_data = json.loads(row['data_json'])
    except Exception as e:
        logger.error(f"Error reading summary cache: {e}")

    # Se não há dados, gera na hora
    if not summary_data:
        summary_data = generate_buildings_summary()

    return render_template('edf_detailed.html', **edf_context())


# ==================================================
# API de Chamados (Dashboard convertido do Streamlit)
# ==================================================

@app.route('/api/chamados/stats')
@safe_api
def api_chamados_stats():
    """API para dados de chamados (para atualização dinâmica do dashboard)."""
    return jsonify(get_chamados_dashboard_data())


# ==================================================
# Inicialização do Scheduler
# ==================================================
scheduler = BackgroundScheduler()
scheduler.add_job(func=update_weather_history, trigger="interval", minutes=15)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# Initialize DB on startup
with app.app_context():
    init_weather_db()
    init_cache_db()
    start_caching_jobs()


# ==================================================
# Ponto de Entrada
# ==================================================
if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("  Analytica - Modo Demonstracao")
    logger.info("  Acesse: http://localhost:5000")
    logger.info("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
