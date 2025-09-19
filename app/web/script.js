// Legal Assistant Chat Interface JavaScript

class LegalAssistantChat {
    constructor() {
        this.API_BASE_URL = 'http://localhost:8000/api/v1';
        this.currentChatId = null;
        this.uploadedFiles = [];
        
        this.initializeElements();
        this.bindEvents();
        this.initialize();
    }

    // Initialize DOM elements
    initializeElements() {
        this.elements = {
            closeSidebarBtn: document.getElementById('close-sidebar-btn'),
            openSidebarBtn: document.getElementById('open-sidebar-btn'),
            expandedSidebar: document.getElementById('expanded-sidebar'),
            collapsedSidebar: document.getElementById('collapsed-sidebar'),
            welcomeScreen: document.getElementById('welcome-screen'),
            chatForm: document.getElementById('chat-form'),
            messageInput: document.getElementById('message-input'),
            chatContainer: document.getElementById('chat-container'),
            chatMessages: document.getElementById('chat-messages'),
            statusIndicator: document.getElementById('status-indicator'),
            statusText: document.getElementById('status-text'),
            fileUpload: document.getElementById('file-upload'),
            collapsedNewChatBtn: document.getElementById('collapsed-new-chat-btn'),
            filePreviewArea: document.getElementById('file-preview-area'),
            selectedFilesContainer: document.getElementById('selected-files'),
            newChatBtn: document.getElementById('new-chat-btn'),
            sendBtn: document.getElementById('send-btn'),
            mainContent: document.getElementById('main-content')
        };
    }

    // Bind event listeners
    bindEvents() {
        // Sidebar toggle events
        this.elements.closeSidebarBtn.addEventListener('click', () => this.closeSidebar());
        this.elements.openSidebarBtn.addEventListener('click', () => this.openSidebar());
        
        // New chat button events
        this.elements.newChatBtn.addEventListener('click', () => this.createNewChat());
        if (this.elements.collapsedNewChatBtn) {
            this.elements.collapsedNewChatBtn.addEventListener('click', () => this.createNewChat());
        }

        // File upload event
        this.elements.fileUpload.addEventListener('change', (e) => this.handleFileUpload(e));

        // Chat form submission
        this.elements.chatForm.addEventListener('submit', (e) => this.handleFormSubmission(e));

        // Textarea auto-resize
        this.elements.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateSendButtonState();
        });

        // Keyboard shortcuts
        this.elements.messageInput.addEventListener('keydown', (e) => this.handleKeyboard(e));
    }

    // Initialize the application
    initialize() {
        // Initial state check
        if (this.elements.chatMessages.children.length === 0) {
            this.elements.welcomeScreen.classList.remove('hidden');
        }
        
        // Load chat history
        this.loadChatHistory();
    }

    // Sidebar methods
    closeSidebar() {
        this.elements.expandedSidebar.classList.add('hidden');
        this.elements.collapsedSidebar.classList.remove('hidden');
        this.elements.collapsedSidebar.classList.add('flex');
        this.elements.mainContent.classList.remove('main-expanded');
        this.elements.mainContent.classList.add('main-collapsed');
    }

    openSidebar() {
        this.elements.expandedSidebar.classList.remove('hidden');
        this.elements.collapsedSidebar.classList.add('hidden');
        this.elements.collapsedSidebar.classList.remove('flex');
        this.elements.mainContent.classList.remove('main-collapsed');
        this.elements.mainContent.classList.add('main-expanded');
    }

    // Chat history methods
    async loadChatHistory() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/chats/history`);
            if (response.ok) {
                const chatHistory = await response.json();
                this.updateChatHistorySidebar(chatHistory);
            }
        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    updateChatHistorySidebar(chatHistory) {
        const navElement = document.querySelector('nav.flex-1.space-y-1');
        navElement.innerHTML = '';
        
        chatHistory.forEach((chat, index) => {
            const chatItem = document.createElement('a');
            chatItem.classList.add('block', 'px-3', 'py-2', 'rounded-md', 'text-sm', 'font-medium', 'text-claude-dark-subtle', 'hover:bg-claude-dark-button', 'truncate', 'cursor-pointer', 'sidebar-item');
            if (index === 0) {
                chatItem.classList.add('bg-claude-dark-button', 'text-claude-dark-text');
            }
            chatItem.textContent = chat.title || `Chat ${chat.id}`;
            chatItem.onclick = () => this.loadChat(chat.id);
            navElement.appendChild(chatItem);
        });
    }

    async loadChat(chatId) {
        try {
            this.currentChatId = chatId;
            const response = await fetch(`${this.API_BASE_URL}/chats/${chatId}/messages`);
            if (response.ok) {
                const messages = await response.json();
                this.displayChatMessages(messages);
                
                // Update sidebar selection
                document.querySelectorAll('nav a').forEach(item => {
                    item.classList.remove('bg-claude-dark-button', 'text-claude-dark-text');
                    item.classList.add('text-claude-dark-subtle');
                });
                event.target.classList.add('bg-claude-dark-button', 'text-claude-dark-text');
                event.target.classList.remove('text-claude-dark-subtle');
            }
        } catch (error) {
            console.error('Failed to load chat:', error);
        }
    }

    displayChatMessages(messages) {
        if (!this.elements.welcomeScreen.classList.contains('hidden')) {
            this.elements.welcomeScreen.classList.add('hidden');
        }
        
        this.elements.chatMessages.innerHTML = '';
        messages.forEach(message => {
            if (message.role === 'user') {
                this.addUserMessage(message.content, message.attachments);
            } else {
                this.addBotMessage(message.content);
            }
        });
        this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
    }

    async createNewChat() {
        try {
            const response = await fetch(`${this.API_BASE_URL}/chats/new`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            if (response.ok) {
                const newChat = await response.json();
                this.currentChatId = newChat.id;
                this.elements.chatMessages.innerHTML = '';
                this.elements.welcomeScreen.classList.remove('hidden');
                this.loadChatHistory(); // Refresh sidebar
            }
        } catch (error) {
            console.error('Failed to create new chat:', error);
        }
    }

    // File upload methods
    async handleFileUpload(e) {
        const files = Array.from(e.target.files);
        for (const file of files) {
            await this.uploadFile(file);
        }
        e.target.value = ''; // Reset file input
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${this.API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
            });
            
            if (response.ok) {
                const result = await response.json();
                this.uploadedFiles.push({
                    id: result.file_id,
                    name: file.name,
                    type: file.type,
                    size: file.size
                });
                this.displayUploadedFile(file);
            } else {
                alert('Failed to upload file: ' + file.name);
            }
        } catch (error) {
            console.error('Upload failed:', error);
            alert('Failed to upload file: ' + file.name);
        }
    }

    displayUploadedFile(file) {
        this.elements.filePreviewArea.classList.remove('hidden');
        
        const fileTag = document.createElement('div');
        fileTag.className = 'flex items-center bg-claude-dark-button text-claude-dark-text px-3 py-1 rounded-md text-sm';
        fileTag.innerHTML = `
            <span class="material-icons text-sm mr-1">${this.getFileIcon(file.type)}</span>
            <span class="truncate max-w-32" title="${file.name}">${file.name}</span>
            <button type="button" class="ml-2 text-claude-dark-subtle hover:text-red-400" onclick="chatApp.removeUploadedFile(this, '${file.name}')">
                <span class="material-icons text-sm">close</span>
            </button>
        `;
        this.elements.selectedFilesContainer.appendChild(fileTag);
    }

    getFileIcon(fileType) {
        if (fileType.startsWith('image/')) return 'image';
        if (fileType.includes('pdf')) return 'picture_as_pdf';
        if (fileType.includes('word') || fileType.includes('document')) return 'description';
        return 'attach_file';
    }

    removeUploadedFile(button, fileName) {
        this.uploadedFiles = this.uploadedFiles.filter(f => f.name !== fileName);
        button.parentElement.remove();
        
        if (this.elements.selectedFilesContainer.children.length === 0) {
            this.elements.filePreviewArea.classList.add('hidden');
        }
    }

    // Form submission and messaging
    async handleFormSubmission(e) {
        e.preventDefault();
        const message = this.elements.messageInput.value.trim();
        if (!message && this.uploadedFiles.length === 0) return;
        
        // Create new chat if none exists
        if (!this.currentChatId) {
            await this.createNewChat();
        }
        
        if (!this.elements.welcomeScreen.classList.contains('hidden')) {
            this.elements.welcomeScreen.classList.add('hidden');
        }
        
        // Add user message to UI
        this.addUserMessage(message, [...this.uploadedFiles]);
        
        // Clear input and uploaded files
        this.elements.messageInput.value = '';
        this.elements.messageInput.style.height = 'auto';
        this.uploadedFiles = [];
        this.elements.filePreviewArea.classList.add('hidden');
        this.elements.selectedFilesContainer.innerHTML = '';
        
        // Show typing indicator
        this.addTypingIndicator();
        
        // Send message to backend
        await this.sendMessage(message, [...this.uploadedFiles]);
        
        this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
    }

    async sendMessage(message, attachments) {
        this.showStatus();
        
        try {
            const requestBody = {
                message: message,
                chat_id: this.currentChatId,
                attachments: attachments.map(f => f.id)
            };
            
            const response = await fetch(`${this.API_BASE_URL}/chats/${this.currentChatId}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
            });
            
            if (response.ok) {
                // Handle streaming response
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                // Remove typing indicator and create bot message
                this.removeTypingIndicator();
                this.hideStatus();
                const botMessageEl = this.createBotMessageElement();
                const responseTextEl = botMessageEl.querySelector('.bot-response-text');
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                if (data.content) {
                                    responseTextEl.innerHTML += data.content;
                                    this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
                                }
                            } catch (e) {
                                // Ignore parsing errors for partial chunks
                            }
                        }
                    }
                }
            } else {
                this.removeTypingIndicator();
                this.hideStatus();
                this.addBotMessage("Sorry, I encountered an error processing your request. Please try again.");
            }
        } catch (error) {
            this.removeTypingIndicator();
            this.hideStatus();
            console.error('Failed to send message:', error);
            this.addBotMessage("Sorry, I couldn't connect to the server. Please check your connection and try again.");
        }
    }

    // Message display methods
    addUserMessage(message, attachments = []) {
        const userMessageEl = document.createElement('div');
        userMessageEl.classList.add('flex', 'items-start', 'gap-4', 'chat-message');
        
        let attachmentHtml = '';
        if (attachments && attachments.length > 0) {
            attachmentHtml = '<div class="mt-2 flex flex-wrap gap-2">';
            attachments.forEach(file => {
                attachmentHtml += `
                    <div class="flex items-center bg-claude-dark-button text-claude-dark-subtle px-2 py-1 rounded text-xs">
                        <span class="material-icons text-xs mr-1">${this.getFileIcon(file.type)}</span>
                        <span>${file.name}</span>
                    </div>
                `;
            });
            attachmentHtml += '</div>';
        }
        
        userMessageEl.innerHTML = `
            <div class="w-8 h-8 rounded-full bg-orange-500 flex items-center justify-center text-white font-bold flex-shrink-0 text-sm">
                L
            </div>
            <div class="flex-1">
                <p class="font-semibold mb-2">You</p>
                <div class="text-claude-dark-text">
                    ${message ? `<p>${message.replace(/\n/g, '<br>')}</p>` : ''}
                    ${attachmentHtml}
                </div>
            </div>
        `;
        this.elements.chatMessages.appendChild(userMessageEl);
    }

    createBotMessageElement() {
        const botMessageEl = document.createElement('div');
        botMessageEl.classList.add('flex', 'items-start', 'gap-4', 'chat-message');
        botMessageEl.innerHTML = `
            <div class="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
               <span class="material-symbols-outlined text-primary">gavel</span>
            </div>
             <div class="flex-1">
                <p class="font-semibold mb-2">ILA</p>
                <div class="text-claude-dark-text space-y-4">
                    <p class="bot-response-text"></p>
                </div>
            </div>
        `;
        this.elements.chatMessages.appendChild(botMessageEl);
        return botMessageEl;
    }

    addBotMessage(message) {
        const botMessageEl = this.createBotMessageElement();
        const responseTextEl = botMessageEl.querySelector('.bot-response-text');
        responseTextEl.innerHTML = message;
    }

    addTypingIndicator() {
        const typingEl = document.createElement('div');
        typingEl.id = 'typing-indicator';
        typingEl.classList.add('flex', 'items-start', 'gap-4', 'mb-4');
        typingEl.innerHTML = `
            <div class="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center flex-shrink-0">
               <span class="material-symbols-outlined text-primary">gavel</span>
            </div>
            <div class="flex-1">
                <p class="font-semibold mb-2">ILA</p>
                <div class="flex items-center space-x-1 text-claude-dark-subtle">
                    <div class="flex space-x-1">
                        <div class="w-2 h-2 bg-claude-dark-subtle rounded-full animate-bounce"></div>
                        <div class="w-2 h-2 bg-claude-dark-subtle rounded-full animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-2 h-2 bg-claude-dark-subtle rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    </div>
                    <span class="ml-2 text-sm">Thinking...</span>
                </div>
            </div>
        `;
        this.elements.chatMessages.appendChild(typingEl);
        this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
    }

    removeTypingIndicator() {
        const typingEl = document.getElementById('typing-indicator');
        if (typingEl) {
            typingEl.remove();
        }
    }

    // UI utility methods
    showStatus() {
        this.elements.statusIndicator.classList.remove('hidden');
        this.elements.statusText.textContent = "Analyzing your legal query...";
    }

    hideStatus() {
        this.elements.statusIndicator.classList.add('hidden');
    }

    autoResizeTextarea() {
        this.elements.messageInput.style.height = 'auto';
        const maxHeight = 200;
        if (this.elements.messageInput.scrollHeight > maxHeight) {
            this.elements.messageInput.style.height = maxHeight + 'px';
            this.elements.messageInput.style.overflowY = 'scroll';
        } else {
            this.elements.messageInput.style.height = (this.elements.messageInput.scrollHeight) + 'px';
            this.elements.messageInput.style.overflowY = 'hidden';
        }
    }

    handleKeyboard(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.elements.chatForm.dispatchEvent(new Event('submit'));
        }
    }

    updateSendButtonState() {
        if (this.elements.messageInput.value.trim() || this.uploadedFiles.length > 0) {
            this.elements.sendBtn.classList.remove('disabled:bg-opacity-50', 'disabled:cursor-not-allowed');
            this.elements.sendBtn.disabled = false;
        } else {
            this.elements.sendBtn.classList.add('disabled:bg-opacity-50', 'disabled:cursor-not-allowed');
            this.elements.sendBtn.disabled = true;
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new LegalAssistantChat();
});