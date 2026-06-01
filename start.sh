#!/bin/bash

# ==============================================================
# Analytica - Arch Linux / Universal Start Script
# ==============================================================
# Este script prepara o ambiente e inicializa a aplicação.
# Recomendado rodar via Arch Linux ou outra distro Systemd/Bash.

echo -e "\e[1;34m[Analytica]\e[0m Iniciando verificação de ambiente..."

# 1. Verifica se Python 3 está instalado
if ! command -v python3 &> /dev/null
then
    echo -e "\e[1;31m[ERRO]\e[0m Python 3 não encontrado. Instale com: sudo pacman -S python"
    exit 1
fi

# 2. Cria o ambiente virtual se não existir
if [ ! -d "venv" ]; then
    echo -e "\e[1;33m[Analytica]\e[0m Criando ambiente virtual (venv)..."
    python3 -m venv venv
fi

# 3. Ativa o ambiente virtual
echo -e "\e[1;34m[Analytica]\e[0m Ativando venv..."
source venv/bin/activate

# 4. Instala dependências (se houver requirements.txt)
if [ -f "requirements.txt" ]; then
    echo -e "\e[1;34m[Analytica]\e[0m Verificando/Instalando dependências..."
    pip install -r requirements.txt --upgrade pip
else
    echo -e "\e[1;33m[AVISO]\e[0m Arquivo requirements.txt não encontrado. Prosseguindo..."
fi

# 5. Inicializa o banco de dados (se necessário mock data pode ser mantida)
# Neste caso, o SQLite é criado automaticamente no código

# 6. Inicia a aplicação
echo -e "\e[1;32m[Analytica]\e[0m Iniciando o Servidor Analytica (Flask)..."
echo -e "Acesse \e[1;36mhttp://localhost:5000\e[0m em seu navegador."
python AnalyticaSync.py

# Caso falhe e caia, desativa venv
deactivate
