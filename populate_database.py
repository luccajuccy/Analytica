# populate_db.py
import sqlite3
from datetime import datetime
import random

EDIFICIOS = [
    "Bonfiglioli", "Atrium V", "São Luiz", "Vera Cruz II", "Teleporto",
    "Berrini 500", "Américas Corporate", "Torre Sul", "Tower Bridge",
    "Pátio Malzoni", "B20", "One Hundred", "São Bento", "Bolsa de Imóveis",
    "Curt", "Peninsula", "Castelo", "Maria Cecilia", "Americas Business",
    "Atrium VI", "Continental Square", "Jatobá", "Millennium", "New Century",
    "New England", "Paulista 500", "Passeio Paulista", "Plaza I",
    "Santa Catarina", "Thera Corporate", "Torres Ibirapuera",
    "CEA (Centro Empresarial do Aço)"
]

FUNCOES = ["Técnico", "Supervisor", "Gerente", "Coordenador"]
CATEGORIAS = ["Elétrica", "Ar Condicionado", "Hidráulica", "Segurança"]
EMPRESAS = ["Empresa A", "Empresa B", "Empresa C", "Empresa D"]

def generate_phone():
    return f"11{random.randint(900000000, 999999999)}"

def generate_email(nome):
    return f"{nome.lower().replace(' ', '.')}@empresa.com"

def insert_sample_data():
    conn = sqlite3.connect('contatos_bms.db')
    cursor = conn.cursor()
    
    # Criar tabela se não existir (garantia)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contatos (
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
        )
    ''')
    conn.commit()

    for predio in EDIFICIOS:
        for _ in range(random.randint(3, 8)):  # 3-8 contatos por edifício
            nome = f"Contato {random.randint(1, 100)}"
            contato = (
                predio,
                random.choice(EMPRESAS),
                random.choice(FUNCOES),
                random.choice(CATEGORIAS),
                f"Ação {random.randint(1, 5)}",
                nome,
                generate_phone(),
                generate_phone() if random.random() > 0.3 else "",
                generate_email(nome),
                f"Observações para {nome}",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            )
            
            cursor.execute('''
                INSERT INTO contatos (
                    predio, empresa, funcao, categoria, acao, nome, 
                    telefone1, telefone2, email, observacao, data_atualizacao
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
            ''', contato)
    
    conn.commit()
    conn.close()
    print(f"{len(EDIFICIOS)} edifícios e seus contatos inseridos!")

if __name__ == '__main__':
    insert_sample_data()