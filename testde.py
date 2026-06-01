# testdb.py (VERSÃO OTIMIZADA)
import sqlite3

def init_db():
    conn = sqlite3.connect('contatos_bms.db')
    cursor = conn.cursor()
    
    # Criação da tabela com constraints e formatação de dados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contatos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            predio TEXT NOT NULL CHECK(length(predio) <= 10),
            empresa TEXT NOT NULL CHECK(length(empresa) <= 50),
            funcao TEXT NOT NULL CHECK(length(funcao) <= 30),
            categoria TEXT NOT NULL CHECK(length(categoria) <= 30),
            acao TEXT NOT NULL CHECK(length(acao) <= 50),
            nome TEXT NOT NULL CHECK(length(nome) <= 100),
            telefone1 TEXT NOT NULL CHECK(length(telefone1) >= 10 AND telefone1 GLOB '[0-9]*'),
            telefone2 TEXT DEFAULT '' CHECK(length(telefone2) >= 10 AND telefone2 GLOB '[0-9]*'),
            email TEXT NOT NULL CHECK(email LIKE '%@%'),
            observacao TEXT DEFAULT '',
            data_atualizacao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()