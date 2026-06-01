# -*- coding: utf-8 -*-
"""Generate fictitious BMS data for the Analytica Flask demo.

The generated data is realistic enough for a live presentation, but contains
no real people, buildings, IPs, credentials, or operational history.
"""

import json
import math
import os
import random
import sqlite3
from datetime import datetime, timedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(PROJECT_DIR, "contatos_bms.db")
KNOWLEDGE_DB = os.path.join(BASE_DIR, "search_cache", "knowledge.db")
DATA_DIR = os.path.join(BASE_DIR, "data")
METADATA_PATH = os.path.join(DATA_DIR, "edificios_metadata.json")
NEWS_PATH = os.path.join(DATA_DIR, "news_fake.json")

BUILDINGS = [
    {"name": "Torre Alpha", "slug": "torre-alpha", "ip_start": 101},
    {"name": "Edificio Beta", "slug": "edificio-beta", "ip_start": 121},
    {"name": "Shopping Gama", "slug": "shopping-gama", "ip_start": 141},
    {"name": "Torre Sul", "slug": "torre-sul", "ip_start": 161},
    {"name": "Ed. Vera Cruz", "slug": "ed-vera-cruz", "ip_start": 181},
]

FIRST_NAMES = [
    "Ana Paula", "Carlos Eduardo", "Mariana", "Rafael", "Juliana",
    "Bruno", "Fernanda", "Lucas", "Patricia", "Diego", "Camila",
    "Renato", "Bianca", "Gustavo", "Larissa", "Marcelo", "Tatiane",
    "Rodrigo", "Aline", "Felipe",
]
LAST_NAMES = [
    "Silva", "Oliveira", "Santos", "Costa", "Pereira", "Lima",
    "Almeida", "Ribeiro", "Martins", "Carvalho", "Mendes", "Barbosa",
]
COMPANIES = [
    "XYZ Consultoria", "Delta Energia", "Norte Office", "Atlas Coworking",
    "Zenith Labs", "Prime Facilities", "Ponto Azul", "Viva Tech",
]
EQUIPMENT_TYPES = ["Chiller", "Bomba AG", "Bomba AC", "Torre de Resfriamento", "Fan Coil", "VAV"]
WEEKDAYS = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta", "Sabado", "Domingo"]


def phone():
    first = random.randint(90000, 99999)
    second = random.randint(1000, 9999)
    return f"(11) {first}-{second}"


def person_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def smooth_internal_temp(ts, base=23.5):
    hour = ts.hour + ts.minute / 60
    day_wave = math.sin((hour - 8) / 24 * math.tau) * 1.2
    noise = random.uniform(-0.35, 0.35)
    spike = random.choice([0, 0, 0, 0, random.uniform(1.0, 2.8), random.uniform(-2.0, -1.0)])
    return round(max(18.5, min(30.5, base + day_wave + noise + spike)), 1)


def fake_external_temp(ts):
    day_of_year = int(ts.strftime("%j"))
    seasonal = 23 + 9 * math.sin((day_of_year - 20) / 365 * math.tau)
    hourly = 5 * math.sin((ts.hour - 8) / 24 * math.tau)
    return round(max(8, min(38, seasonal + hourly + random.uniform(-1.5, 1.5))), 1)


def reset_main_db():
    random.seed(20260526)
    now = datetime.now().replace(second=0, microsecond=0)

    for path in (f"{DB_PATH}-wal", f"{DB_PATH}-shm", f"{DB_PATH}-journal"):
        if os.path.exists(path):
            os.remove(path)
    open(DB_PATH, "wb").close()

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.executescript(
            """
            DROP TABLE IF EXISTS buildings;
            DROP TABLE IF EXISTS floors;
            DROP TABLE IF EXISTS rooms;
            DROP TABLE IF EXISTS sensors;
            DROP TABLE IF EXISTS equipamentos;
            DROP TABLE IF EXISTS temp_history;
            DROP TABLE IF EXISTS weather_history;
            DROP TABLE IF EXISTS chamados;
            DROP TABLE IF EXISTS contatos;
            DROP TABLE IF EXISTS cag_operations;
            DROP TABLE IF EXISTS notifications;
            DROP TABLE IF EXISTS building_cache;

            CREATE TABLE buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                floors_count INTEGER NOT NULL,
                ip_start TEXT NOT NULL,
                ip_end TEXT NOT NULL,
                status TEXT NOT NULL,
                critical_failures INTEGER DEFAULT 0
            );

            CREATE TABLE floors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                floor_number INTEGER NOT NULL,
                label TEXT NOT NULL,
                FOREIGN KEY(building_id) REFERENCES buildings(id)
            );

            CREATE TABLE rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                floor_id INTEGER NOT NULL,
                room_number TEXT NOT NULL,
                company TEXT NOT NULL,
                FOREIGN KEY(floor_id) REFERENCES floors(id)
            );

            CREATE TABLE sensors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                floor_id INTEGER NOT NULL,
                room_id INTEGER,
                ip TEXT NOT NULL,
                tag TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                equipment_type TEXT NOT NULL,
                status TEXT NOT NULL,
                latency_ms INTEGER,
                last_temperature REAL,
                last_seen TEXT,
                FOREIGN KEY(building_id) REFERENCES buildings(id),
                FOREIGN KEY(floor_id) REFERENCES floors(id)
            );

            CREATE TABLE equipamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                floor_id INTEGER,
                name TEXT NOT NULL,
                equipment_type TEXT NOT NULL,
                status TEXT NOT NULL,
                last_event TEXT,
                health_score INTEGER,
                FOREIGN KEY(building_id) REFERENCES buildings(id)
            );

            CREATE TABLE temp_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                floor_id INTEGER,
                sensor_id INTEGER,
                timestamp TEXT NOT NULL,
                temperature REAL NOT NULL,
                setpoint REAL NOT NULL,
                external_temperature REAL NOT NULL,
                FOREIGN KEY(building_id) REFERENCES buildings(id)
            );

            CREATE TABLE weather_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                city TEXT,
                temperature REAL,
                description TEXT,
                min_temp REAL,
                max_temp REAL,
                humidity INTEGER,
                wind_speed REAL
            );

            CREATE TABLE chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT,
                tipo TEXT,
                local TEXT,
                building_id INTEGER,
                andar TEXT,
                floor_number INTEGER,
                empresa TEXT,
                temp_action TEXT,
                observacao_cliente TEXT,
                status TEXT,
                prioridade TEXT,
                descricao TEXT,
                responsavel TEXT,
                data_abertura TEXT,
                data_fechamento TEXT,
                FOREIGN KEY(building_id) REFERENCES buildings(id)
            );

            CREATE TABLE contatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                predio TEXT,
                empresa TEXT,
                funcao TEXT,
                categoria TEXT,
                acao TEXT,
                nome TEXT,
                telefone1 TEXT,
                telefone2 TEXT,
                email TEXT,
                observacao TEXT,
                data_atualizacao TEXT
            );

            CREATE TABLE cag_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                building_id INTEGER NOT NULL,
                equipment_name TEXT NOT NULL,
                equipment_type TEXT NOT NULL,
                status TEXT NOT NULL,
                event_time TEXT NOT NULL,
                command_origin TEXT NOT NULL,
                note TEXT,
                FOREIGN KEY(building_id) REFERENCES buildings(id)
            );

            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                severity TEXT NOT NULL,
                building_name TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                acknowledged INTEGER DEFAULT 0
            );

            CREATE TABLE building_cache (
                building_name TEXT PRIMARY KEY,
                data_json TEXT,
                last_updated TEXT,
                next_update TEXT
            );
            """
        )

        building_rows = []
        for building in BUILDINGS:
            floors_count = random.randint(8, 25)
            ip_start = building["ip_start"]
            ip_end = min(ip_start + floors_count * 3, 200)
            status = "online" if random.random() < 0.86 else "offline"
            failures = random.randint(0, 3 if status == "online" else 6)
            cur.execute(
                """
                INSERT INTO buildings (name, slug, floors_count, ip_start, ip_end, status, critical_failures)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (building["name"], building["slug"], floors_count, f"10.0.0.{ip_start}", f"10.0.0.{ip_end}", status, failures),
            )
            building_rows.append({**building, "id": cur.lastrowid, "floors_count": floors_count, "status": status})

        floor_rows = []
        sensor_rows = []
        for building in building_rows:
            for floor_number in range(1, building["floors_count"] + 1):
                label = f"Andar {floor_number}"
                cur.execute(
                    "INSERT INTO floors (building_id, floor_number, label) VALUES (?, ?, ?)",
                    (building["id"], floor_number, label),
                )
                floor_id = cur.lastrowid
                floor_rows.append({"id": floor_id, "building_id": building["id"], "floor_number": floor_number})

                for room_idx in range(1, random.randint(3, 6)):
                    room_number = f"{floor_number:02d}{room_idx:02d}"
                    cur.execute(
                        "INSERT INTO rooms (floor_id, room_number, company) VALUES (?, ?, ?)",
                        (floor_id, room_number, random.choice(COMPANIES)),
                    )
                    room_id = cur.lastrowid
                    ip_octet = min(200, building["ip_start"] + ((floor_number * 3 + room_idx) % 19))
                    sensor_status = "online" if random.random() < 0.85 else "offline"
                    temp = smooth_internal_temp(now, 23.2 + random.uniform(-0.5, 0.5))
                    tag = f"{building['slug'].replace('-', '_').upper()}_A{floor_number:02d}_TEMP_{room_idx:02d}"
                    cur.execute(
                        """
                        INSERT INTO sensors
                        (building_id, floor_id, room_id, ip, tag, sensor_type, equipment_type, status,
                         latency_ms, last_temperature, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            building["id"], floor_id, room_id, f"10.0.0.{ip_octet}", tag,
                            "Temperatura", random.choice(["Fan Coil", "VAV", "Sensor Ambiente"]),
                            sensor_status, random.randint(2, 180) if sensor_status == "online" else None,
                            temp, (now - timedelta(minutes=random.randint(0, 25))).strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
                    sensor_rows.append({"id": cur.lastrowid, "building_id": building["id"], "floor_id": floor_id, "temp": temp})

                for eq_type in ["Fan Coil", "VAV"]:
                    cur.execute(
                        """
                        INSERT INTO equipamentos
                        (building_id, floor_id, name, equipment_type, status, last_event, health_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            building["id"], floor_id, f"{eq_type} A{floor_number:02d}",
                            eq_type, "ligado" if random.random() < 0.82 else "falha",
                            (now - timedelta(minutes=random.randint(5, 240))).strftime("%Y-%m-%d %H:%M:%S"),
                            random.randint(55, 100),
                        ),
                    )

            for eq_type in ["Chiller", "Chiller", "Bomba AG", "Bomba AC", "Torre de Resfriamento"]:
                cur.execute(
                    """
                    INSERT INTO equipamentos
                    (building_id, floor_id, name, equipment_type, status, last_event, health_score)
                    VALUES (?, NULL, ?, ?, ?, ?, ?)
                    """,
                    (
                        building["id"], f"{eq_type} {random.randint(1, 3)}", eq_type,
                        "ligado" if random.random() < 0.75 else "desligado",
                        (now - timedelta(minutes=random.randint(5, 480))).strftime("%Y-%m-%d %H:%M:%S"),
                        random.randint(62, 99),
                    ),
                )

        start = now - timedelta(days=30)
        sample_sensors = sensor_rows[:]
        for i in range(30 * 96):
            ts = start + timedelta(minutes=15 * i)
            external = fake_external_temp(ts)
            if i % 8 == 0:
                weather_desc = random.choice(["ceu limpo", "nublado", "chuva leve", "parcialmente nublado"])
                cur.execute(
                    """
                    INSERT INTO weather_history
                    (timestamp, city, temperature, description, min_temp, max_temp, humidity, wind_speed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ts.strftime("%Y-%m-%d %H:%M:%S"), "Sao Paulo", external, weather_desc,
                        round(external - random.uniform(1.0, 3.5), 1),
                        round(external + random.uniform(1.0, 4.0), 1),
                        random.randint(38, 88), round(random.uniform(1.0, 8.5), 1),
                    ),
                )
            for sensor in random.sample(sample_sensors, min(28, len(sample_sensors))):
                cur.execute(
                    """
                    INSERT INTO temp_history
                    (building_id, floor_id, sensor_id, timestamp, temperature, setpoint, external_temperature)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sensor["building_id"], sensor["floor_id"], sensor["id"],
                        ts.strftime("%Y-%m-%d %H:%M:%S"),
                        smooth_internal_temp(ts, 23.0 + (external - 24) * 0.035),
                        23.0, external,
                    ),
                )

        for building in building_rows:
            for _ in range(14):
                name = person_name()
                email_slug = name.lower().replace(" ", ".")
                cur.execute(
                    """
                    INSERT INTO contatos
                    (predio, empresa, funcao, categoria, acao, nome, telefone1, telefone2,
                     email, observacao, data_atualizacao)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        building["name"], random.choice(COMPANIES), random.choice(["Tecnico BMS", "Facilities", "Supervisor", "Operacao"]),
                        random.choice(["HVAC", "Automacao", "Eletrica", "CAG"]), "Acionar equipe responsavel",
                        name, phone(), phone() if random.random() > 0.55 else "",
                        f"{email_slug}@exemplo.com", "Contato ficticio para demonstracao.",
                        now.strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )

        observations = [
            "Sala de reuniao muito quente apos as 14h.",
            "Equipe relatou corrente de ar frio proxima as estacoes.",
            "Ambiente instavel durante reuniao com clientes.",
            "Setor financeiro solicitou ajuste fino do conforto termico.",
            "Sala tecnica aqueceu depois do aumento de ocupacao.",
            "Recepcao com sensacao termica baixa no inicio da manha.",
        ]
        for i in range(1, 181):
            building = random.choice(building_rows)
            floor_number = random.randint(1, building["floors_count"])
            action = random.choice(["aumentar", "diminuir"])
            opened = now - timedelta(days=random.randint(0, 29), hours=random.randint(0, 23), minutes=random.randint(0, 59))
            closed = opened + timedelta(minutes=random.randint(35, 360))
            is_closed = random.random() < 0.72
            status = "fechado" if is_closed else "aberto"
            priority = random.choices(["Baixa", "Media", "Alta", "Critica"], weights=[24, 42, 26, 8], k=1)[0]
            obs = random.choice(observations)
            desc = f"Andar {building['floors_count']}/{floor_number} solicitou para {action} a temperatura. OBS do cliente: {obs}"
            cur.execute(
                """
                INSERT INTO chamados
                (numero, tipo, local, building_id, andar, floor_number, empresa, temp_action,
                 observacao_cliente, status, prioridade, descricao, responsavel, data_abertura, data_fechamento)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"CH-2026-{i:04d}", "Ajuste de Temperatura", building["name"], building["id"],
                    f"Andar {building['floors_count']}/{floor_number}", floor_number, random.choice(COMPANIES),
                    action, obs, status, priority, desc, person_name(),
                    opened.strftime("%Y-%m-%d %H:%M:%S"),
                    closed.strftime("%Y-%m-%d %H:%M:%S") if is_closed else None,
                ),
            )

        for building in building_rows:
            for i in range(22):
                event_time = now - timedelta(days=random.randint(0, 14), hours=random.randint(0, 23), minutes=random.randint(0, 59))
                eq_type = random.choice(["Chiller", "Bomba AG", "Bomba AC", "Torre de Resfriamento"])
                status = random.choice(["ligado", "desligado"])
                origin = "Lógica de Automação" if random.random() < 0.60 else f"Operador: {person_name()}"
                cur.execute(
                    """
                    INSERT INTO cag_operations
                    (building_id, equipment_name, equipment_type, status, event_time, command_origin, note)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        building["id"], f"{eq_type} {random.randint(1, 3)}", eq_type, status,
                        event_time.strftime("%Y-%m-%d %H:%M:%S"), origin,
                        "Operacao automatica registrada no modo demonstracao.",
                    ),
                )

        for building in building_rows:
            if building["status"] == "offline":
                cur.execute(
                    "INSERT INTO notifications (severity, building_name, message, created_at) VALUES (?, ?, ?, ?)",
                    (
                        "critical", building["name"],
                        f"{building['name']} sem comunicacao por mais de 15 minutos. Possivel perda de conectividade.",
                        (now - timedelta(minutes=random.randint(10, 45))).strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
            for _ in range(random.randint(1, 3)):
                cur.execute(
                    "INSERT INTO notifications (severity, building_name, message, created_at) VALUES (?, ?, ?, ?)",
                    (
                        random.choice(["warning", "info"]),
                        building["name"],
                        f"Chamado de {building['name']} foi fechado recentemente, mas a temperatura ainda nao atingiu o setpoint esperado.",
                        (now - timedelta(minutes=random.randint(5, 120))).strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )

        summary = {}
        for building in building_rows:
            pings = cur.execute(
                "SELECT ip, equipment_type, status, latency_ms FROM sensors WHERE building_id = ? LIMIT 8",
                (building["id"],),
            ).fetchall()
            summary[building["name"]] = {
                "cag": [
                    {"tag": f"{building['slug'].replace('-', '_').upper()}_CH1_AG_TEMP", "value": round(6.1 + random.random(), 1)},
                    {"tag": f"{building['slug'].replace('-', '_').upper()}_CH2_AG_TEMP", "value": round(6.4 + random.random(), 1)},
                ],
                "pings": [
                    {"host": row["ip"], "label": row["equipment_type"], "status": row["status"] == "online", "latency": row["latency_ms"]}
                    for row in pings
                ],
            }
        cur.execute(
            "INSERT INTO building_cache VALUES (?, ?, ?, ?)",
            (
                "BUILDINGS_SUMMARY", json.dumps(summary, ensure_ascii=False),
                now.strftime("%Y-%m-%d %H:%M:%S"),
                (now + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"),
            ),
        )
        conn.commit()


def reset_knowledge_db():
    os.makedirs(os.path.dirname(KNOWLEDGE_DB), exist_ok=True)
    with sqlite3.connect(KNOWLEDGE_DB) as conn:
        cur = conn.cursor()
        cur.executescript(
            """
            DROP TABLE IF EXISTS files;
            DROP TABLE IF EXISTS search_history;
            DROP TABLE IF EXISTS file_ratings;
            DROP TABLE IF EXISTS chat_history;
            DROP TABLE IF EXISTS uploaded_documents;

            CREATE TABLE files (
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
            );
            CREATE TABLE search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                last_searched TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE file_ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                likes INTEGER DEFAULT 0,
                dislikes INTEGER DEFAULT 0,
                last_rated TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_message TEXT NOT NULL,
                bot_response TEXT NOT NULL,
                documents_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE uploaded_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL,
                title TEXT NOT NULL,
                extracted_text TEXT,
                category TEXT,
                confidence REAL,
                comment TEXT,
                uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        docs = [
            ("manual-hvac-torre-alpha.txt", "Manual HVAC Torre Alpha", "Procedimento de operacao de fan coils, VAV, setpoint, chiller e CAG."),
            ("plano-eletrica-torre-sul.txt", "Plano Eletrica Torre Sul", "Inspecao preventiva de quadros eletricos, nobreaks e aterramento."),
            ("relatorio-ed-vera-cruz.txt", "Relatorio Ed. Vera Cruz", "Resumo de chamados, temperaturas, sensores offline e disponibilidade BMS."),
            ("procedimento-shopping-gama.txt", "Procedimento Shopping Gama", "Rotina de abertura, monitoramento de bombas e verificacao de alarmes."),
        ]
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        for path, title, content in docs:
            cur.execute(
                """
                INSERT INTO files
                (path, real_path, title, content, type, mime, size, size_bytes, modified, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (path, path, title, content, "Documento de Texto", "text/plain", "2.0 KB", 2048, now, path),
            )
        conn.commit()


def write_json_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    metadata = {
        "edificios": {
            b["name"]: {
                "posto": "AC" if i % 2 else "BI",
                "chillers": 2 + (i % 2),
                "operacao_24h": i in (2, 4),
                "coordenadas": "",
                "mensagem_partida": "Bom dia, a CAG partiu sem anormalidades.",
                "mensagem_desligamento": "Boa tarde, a CAG foi desligada conforme programado.",
            }
            for i, b in enumerate(BUILDINGS)
        }
    }
    with open(METADATA_PATH, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2)

    news = [
        {"title": "Frente fria ficticia reduz carga termica em edificios corporativos", "summary": "A simulacao indica queda de demanda por resfriamento durante a madrugada."},
        {"title": "Onda de calor de demonstracao eleva solicitacoes de conforto termico", "summary": "Dados mockados mostram picos de ajustes no periodo da tarde."},
        {"title": "Chuva isolada altera rotina de partida da CAG", "summary": "Operadores acompanham tendencia de umidade e temperatura externa."},
        {"title": "Sensores virtuais registram estabilidade em areas de escritorio", "summary": "Amostras simuladas mantem ambientes dentro do setpoint esperado."},
        {"title": "Alerta preventivo indica possivel perda de comunicacao em controlador", "summary": "Evento ficticio usado para demonstrar notificacoes inteligentes."},
        {"title": "Manha fria reduz chamados para diminuir temperatura", "summary": "Padrao semanal da demo destaca correlacao com temperatura externa."},
        {"title": "Dashboard BMS passa a destacar outliers por andar", "summary": "Mapa de calor facilita a leitura de pontos de desconforto."},
        {"title": "Simulacao de CAG registra partida escalonada de chillers", "summary": "Sequencia ficticia prepara modelo de email operacional."},
        {"title": "Shopping Gama testa rotina de automacao predial offline", "summary": "Cenario demonstra operacao local sem APIs externas."},
        {"title": "Torre Alpha apresenta maior volume de ajustes no periodo vespertino", "summary": "Historico ficticio apoia a narrativa da apresentacao."},
    ]
    with open(NEWS_PATH, "w", encoding="utf-8") as fh:
        json.dump(news, fh, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    reset_main_db()
    reset_knowledge_db()
    write_json_files()
    print("Dados mockados gerados com sucesso.")
    print(f"Banco principal: {DB_PATH}")
    print(f"Banco de conhecimento: {KNOWLEDGE_DB}")
