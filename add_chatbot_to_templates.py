"""
Script para adicionar o chatbot component a todos os templates
"""

import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

CHATBOT_INCLUDE = """
    <!-- Chatbot Component -->
    {% include 'components/chatbot.html' %}"""

def add_chatbot_to_template(filepath):
    """Adiciona o chatbot component antes da tag </body>"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se já tem o chatbot
        if "components/chatbot.html" in content:
            print(f"✓ {os.path.basename(filepath)} - Já possui chatbot")
            return False
        
        # Verificar se tem </body>
        if "</body>" not in content:
            print(f"✗ {os.path.basename(filepath)} - Sem tag </body>")
            return False
        
        # Adicionar chatbot antes de </body>
        new_content = content.replace("</body>", f"{CHATBOT_INCLUDE}\n</body>")
        
        # Salvar
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✓ {os.path.basename(filepath)} - Chatbot adicionado")
        return True
        
    except Exception as e:
        print(f"✗ {os.path.basename(filepath)} - Erro: {e}")
        return False

def main():
    """Processa todos os templates HTML"""
    if not os.path.exists(TEMPLATES_DIR):
        print(f"Diretório não encontrado: {TEMPLATES_DIR}")
        return
    
    templates = [
        "dashboard.html",
        "cag.html",
        "B20.html",
        "edf.html",
        "help.html",
        "plano_de_chamados.html",
        "add_contato.html",
        "edit_contato.html",
        "gerenciar_emails.html"
    ]
    
    print("=" * 60)
    print("ADICIONANDO CHATBOT AOS TEMPLATES")
    print("=" * 60)
    
    added = 0
    skipped = 0
    
    for template in templates:
        filepath = os.path.join(TEMPLATES_DIR, template)
        if os.path.exists(filepath):
            if add_chatbot_to_template(filepath):
                added += 1
            else:
                skipped += 1
        else:
            print(f"✗ {template} - Arquivo não encontrado")
    
    print("=" * 60)
    print(f"Resumo: {added} adicionados, {skipped} pulados")
    print("=" * 60)

if __name__ == "__main__":
    main()
