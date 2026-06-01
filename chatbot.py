"""
Chatbot Engine para Analytica
==================================
Motor de chatbot inteligente com base de conhecimento local.
Sem dependência de APIs externas. Dados 100% preservados.
"""

import logging
import re
import random
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class ChatbotEngine:
    """
    Motor do chatbot com inteligência local:
    - Base de conhecimento embutida (sistema, navegação, funcionalidades)
    - Detecção de intenção por padrões e palavras-chave
    - Integração com SearchEngine para busca documental
    - Respostas contextuais e variadas
    """

    def __init__(self, search_engine):
        self.search_engine = search_engine

        # ====================================================
        # BASE DE CONHECIMENTO LOCAL (sem API)
        # ====================================================
        self.knowledge_base = {
            # --- Sobre o Sistema ---
            'sistema': {
                'keywords': ['analytica', 'sistema', 'plataforma', 'aplicação', 'aplicacao', 'software', 'o que é', 'o que e'],
                'responses': [
                    "O **Analytica** é um ecossistema integrado para gestão e monitoramento de infraestruturas corporativas.\n\n"
                    "Ele centraliza dados do BMS (Building Management System), tickets de manutenção, sensores ambientais e processos da CAG.\n\n"
                    "📊 **Principais funcionalidades:**\n"
                    "• Monitoramento em tempo real de edifícios\n"
                    "• Gestão de CAG (Central de Água Gelada)\n"
                    "• Dashboards analíticos\n"
                    "• Sistema de busca inteligente de documentos\n"
                    "• Plano de chamados e contatos\n"
                    "• Monitoramento climático"
                ]
            },
            # --- Navegação ---
            'navegacao': {
                'keywords': ['navegar', 'ir para', 'onde fica', 'como acessar', 'acessar', 'página', 'pagina', 'tela', 'menu', 'rota'],
                'responses': [
                    "🧭 **Navegação do Analytica:**\n\n"
                    "• **Home** (`/home`) — Visão geral com KPIs dos edifícios\n"
                    "• **Dashboard** (`/dashboards`) — Métricas e gráficos operacionais\n"
                    "• **Busca** (`/search`) — Pesquisa inteligente de documentos\n"
                    "• **Edifícios** (`/edf`) — Status, ping e disponibilidade por torre\n"
                    "• **Clima** (`/clima`) — Dados meteorológicos em tempo real\n"
                    "• **Plano de Chamados** (`/plannc`) — Gestão de contatos e tickets\n"
                    "• **CAG** (`/cag`) — Controle da Central de Água Gelada\n"
                    "• **Ajuda** (`/help`) — Documentação e FAQ\n\n"
                    "💡 Use a **sidebar** à esquerda para navegar entre as telas."
                ]
            },
            # --- Edifícios ---
            'edificios': {
                'keywords': ['edifício', 'edificio', 'prédio', 'predio', 'torre', 'building', 'ping', 'uptime', 'disponibilidade', 'link', 'rede', 'sensor'],
                'responses': [
                    "🏢 **Módulo de Edifícios** (`/edf`)\n\n"
                    "Este módulo exibe o portfólio completo de edifícios monitorados:\n\n"
                    "• **Status Online/Offline** — Indicador visual com orb pulsante\n"
                    "• **Ping** — Latência de rede em tempo real (ms)\n"
                    "• **Uptime** — Percentual de disponibilidade do edifício\n"
                    "• **Sensores** — Quantidade de sensores instalados\n"
                    "• **Disponibilidade dos Links** — Lista de IPs com barra de sinal\n"
                    "• **Sparkline** — Mini-gráfico de disponibilidade dos últimos 7 dias\n"
                    "• **Mapa** — Visualização geográfica com marcadores interativos\n\n"
                    "Clique em **\"Acessar Edifício\"** para ver detalhes específicos de cada torre."
                ]
            },
            # --- CAG ---
            'cag': {
                'keywords': ['cag', 'chiller', 'água gelada', 'agua gelada', 'partida', 'desligamento', 'ligamento', 'manobra', 'refrigeração', 'refrigeracao'],
                'responses': [
                    "❄️ **Módulo CAG** — Central de Água Gelada (`/cag`)\n\n"
                    "Gerencia as rotinas operacionais dos sistemas de refrigeração:\n\n"
                    "• **Status das Partidas** — Ligado/Desligado com indicador visual\n"
                    "• **E-mail de Formalização** — Geração automática de instruções de manobra\n"
                    "• **Histórico** — Log imutável de todas as operações realizadas\n"
                    "• **Cards Empilhados** — Layout responsivo para visualização de cada CAG\n\n"
                    "⚠️ Ações de ligamento/desligamento geram logs automáticos para auditoria."
                ]
            },
            # --- Dashboard ---
            'dashboard': {
                'keywords': ['dashboard', 'gráfico', 'grafico', 'métrica', 'metrica', 'kpi', 'indicador', 'análise', 'analise', 'estatística', 'estatistica'],
                'responses': [
                    "📊 **Dashboards** (`/dashboards`)\n\n"
                    "Visualize métricas operacionais em tempo real:\n\n"
                    "• KPIs de desempenho operacional\n"
                    "• Gráficos de volumetria de chamados\n"
                    "• Análise de falhas crônicas\n"
                    "• Filtros dinâmicos por período e edifício\n"
                    "• Notificações e alertas do sistema\n\n"
                    "Os dashboards são atualizados automaticamente com dados do BMS."
                ]
            },
            # --- Busca ---
            'busca': {
                'keywords': ['busca', 'buscar', 'pesquisa', 'pesquisar', 'procurar', 'search', 'documento', 'arquivo', 'indexação', 'indexacao', 'indexar'],
                'responses': [
                    "🔍 **Sistema de Busca** (`/search`)\n\n"
                    "O motor de busca indexa documentos automaticamente:\n\n"
                    "• **Busca por conteúdo** — Pesquisa dentro dos arquivos\n"
                    "• **Busca por nome** — Localiza arquivos por título\n"
                    "• **Filtros por tipo** — Word, Excel, PDF, Imagens, etc.\n"
                    "• **Ranking inteligente** — Resultados ordenados por relevância\n"
                    "• **Sistema de likes** — Documentos favoritos sobem no ranking\n\n"
                    "💡 Eu também posso buscar documentos para você! Basta perguntar, por exemplo:\n"
                    "\"*Encontre documentos sobre Chiller*\""
                ]
            },
            # --- Plano de Chamados ---
            'chamados': {
                'keywords': ['chamado', 'ticket', 'contato', 'plano de chamados', 'plannc', 'telefone', 'ramal', 'suporte'],
                'responses': [
                    "📋 **Plano de Chamados** (`/plannc`)\n\n"
                    "Gerencie contatos e informações de suporte:\n\n"
                    "• **Lista de contatos** — Filtrada por prédio e função\n"
                    "• **Busca rápida** — Localize contatos por nome\n"
                    "• **Filtros dinâmicos** — Por prédio e por função\n"
                    "• **Informações de contato** — Telefone, ramal e e-mail\n\n"
                    "Use os dropdowns para filtrar contatos por edifício ou área de atuação."
                ]
            },
            # --- Clima ---
            'clima': {
                'keywords': ['clima', 'tempo', 'temperatura', 'meteorologia', 'previsão', 'previsao', 'chuva', 'umidade', 'vento', 'weather'],
                'responses': [
                    "🌤️ **Monitoramento Climático** (`/clima`)\n\n"
                    "Acompanhe condições meteorológicas em tempo real:\n\n"
                    "• Temperatura atual e sensação térmica\n"
                    "• Umidade relativa do ar\n"
                    "• Velocidade e direção do vento\n"
                    "• Previsão para os próximos dias\n"
                    "• Alertas meteorológicos\n\n"
                    "Os dados ajudam na tomada de decisão sobre operações nos edifícios."
                ]
            },
            # --- Segurança e LGPD ---
            'seguranca': {
                'keywords': ['segurança', 'seguranca', 'lgpd', 'proteção', 'protecao', 'dados', 'privacidade', 'senha', 'login', 'acesso'],
                'responses': [
                    "🔒 **Segurança e Privacidade**\n\n"
                    "O Analytica segue práticas rigorosas de segurança:\n\n"
                    "• **LGPD** — Dados pessoais tratados em conformidade\n"
                    "• **Sem chaves expostas** — Nenhuma API key ou token no código\n"
                    "• **Banco local** — SQLite com dados em instância isolada\n"
                    "• **Logs auditáveis** — Todas as operações são registradas\n"
                    "• **Dados demo** — Registros fictícios para demonstração\n\n"
                    "Dados de telemetria são anonimizados em relação à ocupação humana."
                ]
            },
            # --- Problemas técnicos ---
            'problemas': {
                'keywords': ['erro', 'bug', 'problema', 'não funciona', 'nao funciona', 'travou', 'lento', 'offline', 'caiu', 'falha'],
                'responses': [
                    "🔧 **Solução de Problemas**\n\n"
                    "Algumas ações que podem ajudar:\n\n"
                    "1. **Recarregue a página** — `Ctrl + F5` para forçar atualização\n"
                    "2. **Verifique a conexão** — Certifique-se de estar na rede correta\n"
                    "3. **Limpe o cache** — Configurações do navegador → Limpar dados\n"
                    "4. **Tente outro navegador** — Chrome ou Edge são recomendados\n\n"
                    "Se o problema persistir, entre em contato:\n"
                    "📧 **devops@analytica.com**"
                ]
            },
        }

        # Respostas de saudação (variadas)
        self.greetings_responses = [
            "Olá! 👋 Sou o assistente do **Analytica**.\n\nPosso ajudar com:\n"
            "• 🧭 Navegação entre telas\n"
            "• 🏢 Informações sobre edifícios\n"
            "• ❄️ Status e operações da CAG\n"
            "• 🔍 Busca de documentos\n"
            "• 📋 Plano de chamados\n\n"
            "O que precisa saber?",

            "Hey! 👋 Bem-vindo ao assistente **Analytica**!\n\n"
            "Pergunte-me qualquer coisa sobre o sistema, ou peça para buscar um documento.\n"
            "Estou aqui para ajudar! 😊",

            "Olá! 😊 Sou o seu assistente virtual.\n\n"
            "Posso te guiar pelo sistema, explicar funcionalidades ou buscar documentos.\n"
            "Como posso te ajudar hoje?"
        ]

        # Quick actions sugeridas
        self.quick_actions = [
            {"label": "Como navegar?", "query": "navegação"},
            {"label": "O que é o sistema?", "query": "sistema"},
            {"label": "Status dos edifícios", "query": "edifícios"},
            {"label": "Como funciona a CAG?", "query": "cag"},
            {"label": "Buscar documentos", "query": "busca"},
        ]

    def process_message(self, user_message: str) -> Dict:
        """Processa mensagem do usuário e retorna resposta inteligente."""
        try:
            clean_message = user_message.strip()
            if not clean_message:
                return self._error_response("Por favor, envie uma mensagem válida.")

            # 1. Detectar intenção
            intent, confidence = self._detect_intent(clean_message)

            # 2. Processar com base na intenção
            if intent == 'greeting':
                return self._greeting_response()
            elif intent == 'help':
                return self._help_response()
            elif intent == 'quick_actions':
                return self._quick_actions_response()
            elif intent in self.knowledge_base and confidence >= 0.6:
                return self._knowledge_response(intent, clean_message)
            else:
                # Fallback inteligente: buscar nos documentos E na base de conhecimento
                return self._smart_fallback(clean_message)

        except Exception as e:
            logger.error(f"Erro ao processar mensagem do chatbot: {e}")
            return self._error_response("Desculpe, ocorreu um erro ao processar sua mensagem.")

    def _detect_intent(self, message: str) -> tuple:
        """
        Detecta a intenção com scoring de confiança.
        Retorna (intent_name, confidence_score).
        """
        message_lower = message.lower()

        # Saudações
        greetings = ['oi', 'olá', 'ola', 'hey', 'hello', 'hi', 'bom dia', 'boa tarde', 'boa noite', 'e aí', 'e ai', 'fala']
        if any(message_lower.strip() == greet or message_lower.startswith(greet + ' ') or message_lower.startswith(greet + ',') for greet in greetings):
            return ('greeting', 1.0)

        # Pedidos de ajuda
        help_keywords = ['ajuda', 'help', 'o que você faz', 'o que voce faz',
                         'como funciona', 'pode fazer', 'como usar', 'comandos',
                         'o que posso perguntar', 'funcionalidades']
        if any(keyword in message_lower for keyword in help_keywords):
            return ('help', 1.0)

        # Quick actions
        if message_lower in ['ações', 'acoes', 'opções', 'opcoes', 'sugestões', 'sugestoes']:
            return ('quick_actions', 1.0)

        # Score por base de conhecimento
        best_intent = None
        best_score = 0

        for intent_name, intent_data in self.knowledge_base.items():
            score = 0
            total_keywords = len(intent_data['keywords'])

            for keyword in intent_data['keywords']:
                if keyword in message_lower:
                    # Peso extra para matches exatos
                    if message_lower.strip() == keyword:
                        score += 3
                    elif keyword in message_lower.split():
                        score += 2
                    else:
                        score += 1

            if total_keywords > 0:
                confidence = score / (total_keywords * 0.5)  # Normalizar
                confidence = min(confidence, 1.0)

                if confidence > best_score:
                    best_score = confidence
                    best_intent = intent_name

        if best_intent and best_score >= 0.3:
            return (best_intent, best_score)

        return ('search', 0.0)

    def _greeting_response(self) -> Dict:
        """Resposta para saudações (variada)."""
        return {
            'success': True,
            'message': random.choice(self.greetings_responses),
            'type': 'greeting',
            'documents': [],
            'quick_actions': self.quick_actions,
            'timestamp': datetime.now().isoformat()
        }

    def _help_response(self) -> Dict:
        """Resposta para pedidos de ajuda."""
        help_text = (
            "💡 **O que posso fazer por você:**\n\n"
            "**🧭 Navegação** — Pergunte como chegar em qualquer tela\n"
            "**🏢 Edifícios** — Status, ping, disponibilidade\n"
            "**❄️ CAG** — Operações da Central de Água Gelada\n"
            "**📊 Dashboards** — Métricas e indicadores\n"
            "**🔍 Busca** — Encontro documentos para você\n"
            "**📋 Chamados** — Informações de contatos e suporte\n"
            "**🌤️ Clima** — Condições meteorológicas\n"
            "**🔒 Segurança** — Políticas de privacidade e LGPD\n\n"
            "💬 Basta perguntar naturalmente! Exemplos:\n"
            "• *\"O que é o Analytica?\"*\n"
            "• *\"Como acessar os edifícios?\"*\n"
            "• *\"Encontre documentos sobre Chiller\"*\n"
            "• *\"O que a CAG faz?\"*"
        )
        return {
            'success': True,
            'message': help_text,
            'type': 'help',
            'documents': [],
            'quick_actions': self.quick_actions,
            'timestamp': datetime.now().isoformat()
        }

    def _quick_actions_response(self) -> Dict:
        """Resposta com ações rápidas."""
        return {
            'success': True,
            'message': "✨ Aqui estão algumas sugestões do que posso fazer por você:",
            'type': 'quick_actions',
            'documents': [],
            'quick_actions': self.quick_actions,
            'timestamp': datetime.now().isoformat()
        }

    def _knowledge_response(self, intent: str, original_query: str) -> Dict:
        """Resposta baseada na base de conhecimento local."""
        kb_entry = self.knowledge_base[intent]
        response_text = random.choice(kb_entry['responses'])

        # Também buscar documentos relevantes se o search engine tiver dados
        documents = []
        try:
            results = self.search_engine.search(original_query)
            if results and len(results) > 0:
                documents = self._format_documents(results[:3])
                if documents:
                    response_text += "\n\n📄 **Documentos relacionados encontrados:**"
        except Exception:
            pass

        return {
            'success': True,
            'message': response_text,
            'type': 'knowledge',
            'documents': documents,
            'quick_actions': [],
            'timestamp': datetime.now().isoformat()
        }

    def _smart_fallback(self, query: str) -> Dict:
        """
        Fallback inteligente: tenta buscar documentos e,
        se não encontrar, oferece sugestões contextuais.
        """
        # Extrair palavras-chave
        keywords = self._extract_keywords(query)
        search_query = ' '.join(keywords) if keywords else query

        # Buscar documentos
        try:
            results = self.search_engine.search(search_query)
        except Exception:
            results = []

        if results and len(results) > 0:
            # Encontrou documentos — gerar resposta rica
            response_text = self._generate_response_text(query, results)
            documents = self._format_documents(results[:5])
            return {
                'success': True,
                'message': response_text,
                'type': 'search_results',
                'documents': documents,
                'total_results': len(results),
                'quick_actions': [],
                'timestamp': datetime.now().isoformat()
            }
        else:
            # Sem resultados — sugerir tópicos da base de conhecimento
            suggestions = self._suggest_topics(query)
            message = (
                f"😕 Não encontrei resultados específicos sobre **\"{query}\"**.\n\n"
                "💡 **Posso ajudar com:**\n"
            )
            message += suggestions
            message += "\n\n💬 Tente reformular sua pergunta ou escolha uma sugestão acima!"

            return {
                'success': True,
                'message': message,
                'type': 'no_results',
                'documents': [],
                'quick_actions': self.quick_actions,
                'timestamp': datetime.now().isoformat()
            }

    def _suggest_topics(self, query: str) -> str:
        """Sugere tópicos relevantes com base na query."""
        topic_map = {
            'sistema': '🖥️ Sistema Analytica',
            'navegacao': '🧭 Navegação',
            'edificios': '🏢 Edifícios',
            'cag': '❄️ CAG',
            'dashboard': '📊 Dashboards',
            'busca': '🔍 Busca de Documentos',
            'chamados': '📋 Plano de Chamados',
            'clima': '🌤️ Clima',
            'seguranca': '🔒 Segurança',
        }

        lines = []
        for key, label in topic_map.items():
            lines.append(f"• {label}")

        return '\n'.join(lines)

    def _extract_keywords(self, query: str) -> List[str]:
        """Extrai palavras-chave relevantes da query."""
        stopwords = {
            'o', 'a', 'os', 'as', 'um', 'uma', 'de', 'do', 'da', 'dos', 'das',
            'em', 'no', 'na', 'nos', 'nas', 'por', 'para', 'com', 'sem', 'é', 'e',
            'sobre', 'que', 'qual', 'quais', 'como', 'quando', 'onde', 'eu', 'meu',
            'me', 'mostre', 'encontre', 'busque', 'procure', 'ache', 'quero', 'preciso',
            'documento', 'documentos', 'arquivo', 'arquivos', 'fala', 'falam', 'pode',
            'ser', 'ter', 'está', 'esta', 'isso', 'esse', 'essa', 'aquele', 'aquela',
        }
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        return keywords

    def _generate_response_text(self, query: str, results: List[Dict]) -> str:
        """Gera texto de resposta com base nos resultados de busca."""
        num_results = len(results)
        doc_word = "documento" if num_results == 1 else "documentos"

        response = f"🔍 Encontrei **{num_results} {doc_word}** relacionado(s) à sua busca.\n\n"

        for i, result in enumerate(results[:3], 1):
            title = result.get('title', 'Documento sem título')
            snippet = result.get('snippet', '')
            file_type = result.get('type', 'Arquivo')

            response += f"**{i}. {title}**\n"
            response += f"📄 *{file_type}*\n"

            if snippet:
                short_snippet = snippet[:150] + "..." if len(snippet) > 150 else snippet
                response += f"_{short_snippet}_\n"
            response += "\n"

        if num_results > 3:
            response += f"💡 _Há mais {num_results - 3} documento(s) relacionado(s)._"

        return response

    def _format_documents(self, results: List[Dict]) -> List[Dict]:
        """Formata resultados para o frontend."""
        documents = []
        for result in results:
            documents.append({
                'title': result.get('title', 'Documento'),
                'path': result.get('path', ''),
                'type': result.get('type', 'Arquivo'),
                'size': result.get('size', ''),
                'modified': result.get('modified', '')
            })
        return documents

    def _error_response(self, error_message: str) -> Dict:
        """Resposta de erro."""
        return {
            'success': False,
            'message': f"❌ {error_message}",
            'type': 'error',
            'documents': [],
            'quick_actions': self.quick_actions,
            'timestamp': datetime.now().isoformat()
        }

    def get_status(self) -> Dict:
        """Retorna status do chatbot."""
        engine_status = self.search_engine.get_status()
        return {
            'ready': True,  # Always ready since we have local knowledge
            'total_documents': engine_status.get('total_indexed', 0),
            'is_indexing': engine_status.get('is_indexing', False),
            'knowledge_topics': len(self.knowledge_base)
        }
