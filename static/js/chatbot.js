/**
 * Chatbot Client - Analytica
 * Gerencia a interface e interações do chat
 */

(function () {
    'use strict';

    // Estado do chatbot
    const ChatbotState = {
        isOpen: false,
        isLoading: false,
        messages: [],
        apiEndpoint: '/api/chatbot'
    };

    // Elementos DOM
    const elements = {
        container: null,
        toggle: null,
        window: null,
        messages: null,
        input: null,
        form: null,
        sendBtn: null,
        closeBtn: null,
        clearBtn: null,
        status: null,
        badge: null
    };

    /**
     * Inicializa o chatbot
     */
    function initChatbot() {
        // Obter elementos
        elements.container = document.getElementById('chatbotContainer');
        elements.toggle = document.getElementById('chatbotToggle');
        elements.window = document.getElementById('chatbotWindow');
        elements.messages = document.getElementById('chatbotMessages');
        elements.input = document.getElementById('chatbotInput');
        elements.form = document.getElementById('chatbotForm');
        elements.sendBtn = document.getElementById('chatbotSendBtn');
        elements.closeBtn = document.getElementById('closeChatBtn');
        elements.clearBtn = document.getElementById('clearChatBtn');
        elements.status = document.getElementById('chatbotStatus');
        elements.badge = document.getElementById('chatbotBadge');

        if (!elements.container) {
            console.warn('Chatbot container not found');
            return;
        }

        // Event listeners
        elements.toggle.addEventListener('click', toggleChat);
        elements.closeBtn.addEventListener('click', closeChat);
        elements.clearBtn.addEventListener('click', clearHistory);
        elements.form.addEventListener('submit', handleSubmit);
        elements.input.addEventListener('keydown', handleInputKeydown);
        elements.input.addEventListener('input', autoResize);

        // Carregar histórico e status
        checkStatus();
        loadHistory();

        // Mostrar mensagem de boas-vindas
        if (ChatbotState.messages.length === 0) {
            addWelcomeMessage();
        }
    }

    /**
     * Alterna visibilidade do chat
     */
    function toggleChat() {
        if (ChatbotState.isOpen) {
            closeChat();
        } else {
            openChat();
        }
    }

    /**
     * Abre o chat
     */
    function openChat() {
        ChatbotState.isOpen = true;
        elements.window.classList.add('open');
        elements.toggle.classList.add('active');
        elements.badge.classList.remove('visible');
        elements.input.focus();
        scrollToBottom();
    }

    /**
     * Fecha o chat
     */
    function closeChat() {
        ChatbotState.isOpen = false;
        elements.window.classList.remove('open');
        elements.toggle.classList.remove('active');
    }

    /**
     * Verifica status do chatbot
     */
    async function checkStatus() {
        try {
            const response = await fetch(`${ChatbotState.apiEndpoint}/status`);
            const data = await response.json();

            if (data.ready) {
                elements.status.classList.remove('offline');
                elements.status.title = `Pronto (${data.total_documents} documentos)`;
            } else {
                elements.status.classList.add('offline');
                elements.status.title = 'Indexando documentos...';
            }
        } catch (error) {
            console.error('Erro ao verificar status:', error);
            elements.status.classList.add('offline');
        }
    }

    /**
     * Carrega histórico de conversas
     */
    async function loadHistory() {
        try {
            const response = await fetch(`${ChatbotState.apiEndpoint}/history?limit=50`);
            const data = await response.json();

            if (data.success && data.history && data.history.length > 0) {
                // Limpar mensagens atuais
                elements.messages.innerHTML = '';
                ChatbotState.messages = [];

                // Adicionar mensagens do histórico
                data.history.forEach(item => {
                    addMessage(item.user_message, 'user', false);
                    addMessage(item.bot_response, 'bot', false, item.documents);
                });

                scrollToBottom();
            }
        } catch (error) {
            console.error('Erro ao carregar histórico:', error);
        }
    }

    /**
     * Limpa histórico
     */
    async function clearHistory() {
        if (!confirm('Deseja limpar todo o histórico de conversas?')) {
            return;
        }

        try {
            const response = await fetch(`${ChatbotState.apiEndpoint}/clear`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (data.success) {
                elements.messages.innerHTML = '';
                ChatbotState.messages = [];
                addWelcomeMessage();
            } else {
                alert('Erro ao limpar histórico');
            }
        } catch (error) {
            console.error('Erro ao limpar histórico:', error);
            alert('Erro ao limpar histórico');
        }
    }

    /**
     * Adiciona mensagem de boas-vindas
     */
    function addWelcomeMessage() {
        const welcomeMsg = 'Ola! 👋 Sou o assistente virtual do Analytica.\n\nPosso ajuda-lo a encontrar informacoes nos documentos indexados. Pergunte-me sobre equipamentos, relatórios, plantas ou qualquer conteudo nos arquivos.';
        addMessage(welcomeMsg, 'bot', false);
    }

    /**
     * Processa envio do formulário
     */
    async function handleSubmit(e) {
        e.preventDefault();

        const message = elements.input.value.trim();
        if (!message || ChatbotState.isLoading) {
            return;
        }

        // Adicionar mensagem do usuário
        addMessage(message, 'user');

        // Limpar input
        elements.input.value = '';
        autoResize();

        // Enviar para API
        await sendMessage(message);
    }

    /**
     * Envia mensagem para a API
     */
    async function sendMessage(message) {
        ChatbotState.isLoading = true;
        elements.sendBtn.disabled = true;

        // Mostrar indicador de digitação
        const typingIndicator = showTypingIndicator();

        try {
            const response = await fetch(`${ChatbotState.apiEndpoint}/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const data = await response.json();

            // Remover indicador de digitação
            typingIndicator.remove();

            if (data.success) {
                addMessage(data.message, 'bot', true, data.documents);
            } else {
                addMessage(data.message || 'Erro ao processar mensagem', 'bot', true);
            }
        } catch (error) {
            typingIndicator.remove();
            console.error('Erro ao enviar mensagem:', error);
            addMessage('❌ Erro de conexão. Tente novamente.', 'bot', true);
        } finally {
            ChatbotState.isLoading = false;
            elements.sendBtn.disabled = false;
            elements.input.focus();
        }
    }

    /**
     * Adiciona mensagem ao chat
     */
    function addMessage(text, type, scroll = true, documents = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${type}`;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';

        // Formatar texto (suporte básico a Markdown)
        bubble.innerHTML = formatMessage(text);

        // Adicionar documentos se houver
        if (documents && documents.length > 0) {
            const docsDiv = document.createElement('div');
            docsDiv.className = 'message-documents';

            documents.forEach(doc => {
                const docBadge = document.createElement('a');
                docBadge.className = 'doc-badge';
                docBadge.href = `/knowledge_file/${doc.path}`;
                docBadge.target = '_blank';
                docBadge.innerHTML = `<i class="fas fa-file"></i> ${doc.title}`;
                docsDiv.appendChild(docBadge);
            });

            bubble.appendChild(docsDiv);
        }

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(bubble);

        elements.messages.appendChild(messageDiv);
        ChatbotState.messages.push({ text, type, documents });

        if (scroll) {
            scrollToBottom();
        }
    }

    /**
     * Mostra indicador de digitação
     */
    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator active';
        indicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        elements.messages.appendChild(indicator);
        scrollToBottom();
        return indicator;
    }

    /**
     * Formata mensagem (suporte básico a Markdown)
     */
    function formatMessage(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // **bold**
            .replace(/\*(.*?)\*/g, '<em>$1</em>')             // *italic*
            .replace(/`(.*?)`/g, '<code>$1</code>')           // `code`
            .replace(/\n/g, '<br>');                          // line breaks
    }

    /**
     * Scroll automático para o final
     */
    function scrollToBottom() {
        setTimeout(() => {
            elements.messages.scrollTop = elements.messages.scrollHeight;
        }, 100);
    }

    /**
     * Auto-resize do textarea
     */
    function autoResize() {
        elements.input.style.height = 'auto';
        elements.input.style.height = Math.min(elements.input.scrollHeight, 100) + 'px';
    }

    /**
     * Trata teclas no input
     */
    function handleInputKeydown(e) {
        // Enter sem Shift envia mensagem
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            elements.form.dispatchEvent(new Event('submit'));
        }
    }

    // Inicializar quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initChatbot);
    } else {
        initChatbot();
    }

    // Atualizar status periodicamente
    setInterval(checkStatus, 60000); // A cada 1 minuto

})();


