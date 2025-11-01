(function() {
    const script = document.currentScript || document.querySelector('script[src*="chatbot-widget"]');
    const config = {
        apiUrl: script.getAttribute('data-api-url') || 'http://localhost:5000',
        botName: script.getAttribute('data-bot-name') || 'AI Assistant',
        primaryColor: script.getAttribute('data-primary-color') || '#667eea',
        position: script.getAttribute('data-position') || 'right',
        welcomeMessage: script.getAttribute('data-welcome-message') || '👋 Hi! I can help you with company services, FAQs, compliance, and more. Ask me anything!'
    };

    if (window.ChatbotWidget) return;
    window.ChatbotWidget = true;

    function adjustColor(color, amount) {
        const usePound = color[0] === "#";
        const col = usePound ? color.slice(1) : color;
        const num = parseInt(col, 16);
        let r = (num >> 16) + amount;
        let g = (num >> 8 & 0x00FF) + amount;
        let b = (num & 0x0000FF) + amount;
        r = Math.min(255, Math.max(0, r));
        g = Math.min(255, Math.max(0, g));
        b = Math.min(255, Math.max(0, b));
        return (usePound ? "#" : "") + (r << 16 | g << 8 | b).toString(16).padStart(6, '0');
    }

    const styles = `
        #chatbot-widget { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Inter', sans-serif; 
            position: fixed; 
            z-index: 999999; 
            ${config.position}: 20px; 
            bottom: 20px; 
        }
        
        .chat-toggle { 
            width: 64px; 
            height: 64px; 
            background: linear-gradient(135deg, ${config.primaryColor} 0%, ${adjustColor(config.primaryColor, -30)} 100%); 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            cursor: pointer; 
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08); 
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
            border: none; 
            color: white;
            position: relative;
        }
        
        .chat-toggle::before {
            content: '';
            position: absolute;
            inset: -2px;
            border-radius: 50%;
            padding: 2px;
            background: linear-gradient(135deg, ${config.primaryColor}, ${adjustColor(config.primaryColor, -40)});
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        
        .chat-toggle:hover { 
            transform: translateY(-2px) scale(1.05); 
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.16), 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .chat-toggle:hover::before {
            opacity: 0.6;
        }
        
        .chat-toggle svg { 
            width: 30px; 
            height: 30px; 
            fill: white; 
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1); 
        }
        
        .chat-toggle.active svg { 
            transform: rotate(90deg); 
        }
        
        .chat-container { 
            position: absolute; 
            bottom: 85px; 
            ${config.position}: 0; 
            width: 380px; 
            height: 500px; 
            background: #ffffff;
            border-radius: 24px; 
            box-shadow: 0 24px 64px rgba(0, 0, 0, 0.12), 0 8px 24px rgba(0, 0, 0, 0.08); 
            transform: translateY(20px) scale(0.95); 
            opacity: 0; 
            visibility: hidden; 
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
            border: 1px solid rgba(0, 0, 0, 0.06); 
            overflow: hidden; 
            display: flex; 
            flex-direction: column; 
        }
        
        .chat-container.active { 
            transform: translateY(0) scale(1); 
            opacity: 1; 
            visibility: visible; 
        }
        
        .chat-header { 
            background: linear-gradient(135deg, ${config.primaryColor} 0%, ${adjustColor(config.primaryColor, -30)} 100%); 
            color: white; 
            padding: 24px; 
            display: flex; 
            align-items: center; 
            gap: 14px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            position: relative;
            overflow: hidden;
        }
        
        .chat-header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -10%;
            width: 200px;
            height: 200px;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
            border-radius: 50%;
        }
        
        .chat-avatar { 
            width: 44px; 
            height: 44px; 
            background: rgba(255, 255, 255, 0.25); 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            position: relative;
            z-index: 1;
        }
        
        .chat-info { 
            flex: 1;
            position: relative;
            z-index: 1;
        }
        
        .chat-info h3 { 
            font-size: 17px; 
            font-weight: 600; 
            margin: 0 0 4px 0;
            letter-spacing: -0.2px;
        }
        
        .chat-status { 
            font-size: 13px; 
            opacity: 0.95; 
            display: flex; 
            align-items: center; 
            gap: 7px; 
            margin: 0;
            font-weight: 500;
        }
        
        .status-dot { 
            width: 8px; 
            height: 8px; 
            background: #4ade80; 
            border-radius: 50%; 
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            box-shadow: 0 0 8px rgba(74, 222, 128, 0.6);
        }
        
        @keyframes pulse { 
            0%, 100% { 
                opacity: 1; 
                transform: scale(1);
            } 
            50% { 
                opacity: 0.6; 
                transform: scale(0.9);
            } 
        }
        
        .messages { 
            flex: 1; 
            padding: 24px; 
            overflow-y: auto;
            background: linear-gradient(to bottom, #fafafa 0%, #ffffff 100%);
            scroll-behavior: smooth;
        }
        
        .message { 
            margin-bottom: 18px; 
            animation: slideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1); 
        }
        
        @keyframes slideIn { 
            from { 
                opacity: 0; 
                transform: translateY(12px); 
            } 
            to { 
                opacity: 1; 
                transform: translateY(0); 
            } 
        }
        
        .message.user { 
            display: flex; 
            justify-content: flex-end; 
        }
        
        .message.bot { 
            display: flex; 
            justify-content: flex-start; 
            flex-direction: column; 
            align-items: flex-start; 
        }
        
        .message.system { 
            text-align: center; 
        }
        
        .message-bubble { 
            max-width: 80%; 
            padding: 14px 18px; 
            border-radius: 20px; 
            font-size: 14.5px; 
            line-height: 1.5; 
            word-wrap: break-word;
            position: relative;
        }
        
        .message.user .message-bubble { 
            background: linear-gradient(135deg, ${config.primaryColor} 0%, ${adjustColor(config.primaryColor, -25)} 100%); 
            color: white; 
            border-bottom-right-radius: 6px;
            box-shadow: 0 4px 12px ${config.primaryColor}30;
        }
        
        .message.bot .message-bubble { 
            background: #f8fafc; 
            color: #1e293b; 
            border-bottom-left-radius: 6px; 
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }
        
        .message.system .message-bubble { 
            background: linear-gradient(135deg, ${config.primaryColor}15 0%, ${config.primaryColor}08 100%); 
            color: ${config.primaryColor}; 
            font-size: 13px; 
            padding: 10px 16px; 
            border-radius: 14px; 
            display: inline-block;
            border: 1px solid ${config.primaryColor}20;
            font-weight: 500;
        }
        
        .feedback-container { 
            margin-top: 10px; 
            display: flex; 
            gap: 10px; 
            align-items: center; 
        }
        
        .feedback-button { 
            padding: 0; 
            font-size: 16px; 
            border: none;
            border-radius: 12px; 
            cursor: pointer; 
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.06);
            display: flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            border: 1px solid #e2e8f0;
        }
        
        .feedback-button svg {
            width: 18px;
            height: 18px;
            fill: #64748b;
            transition: fill 0.25s ease;
        }
        
        .feedback-button:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.08);
            border-color: transparent;
        }
        
        .feedback-button.thumbs-up:hover {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            border-color: #10b981;
        }
        
        .feedback-button.thumbs-up:hover svg {
            fill: white;
        }
        
        .feedback-button.thumbs-down:hover {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            border-color: #ef4444;
        }
        
        .feedback-button.thumbs-down:hover svg {
            fill: white;
        }
        
        .feedback-button:active {
            transform: translateY(0);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }
        
        .chat-input { 
            padding: 20px 24px 24px; 
            background: #ffffff;
            border-top: 1px solid #e2e8f0;
        }
        
        .input-group { 
            display: flex; 
            gap: 12px; 
            align-items: flex-end;
            background: #f8fafc;
            border-radius: 20px;
            padding: 6px;
            border: 1px solid #e2e8f0;
            transition: all 0.2s ease;
        }
        
        .input-group:focus-within {
            background: #ffffff;
            border-color: ${config.primaryColor};
            box-shadow: 0 0 0 3px ${config.primaryColor}15;
        }
        
        .message-input { 
            flex: 1; 
            padding: 12px 16px; 
            border: none;
            border-radius: 16px; 
            font-size: 14.5px; 
            resize: none; 
            min-height: 22px; 
            max-height: 100px; 
            background: transparent;
            transition: all 0.2s ease;
            font-family: inherit;
            line-height: 1.5;
        }
        
        .message-input:focus { 
            outline: none;
        }
        
        .message-input::placeholder {
            color: #94a3b8;
        }
        
        .send-button { 
            width: 46px; 
            height: 46px; 
            background: linear-gradient(135deg, ${config.primaryColor} 0%, ${adjustColor(config.primaryColor, -25)} 100%); 
            border: none; 
            border-radius: 50%; 
            color: white; 
            cursor: pointer; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            flex-shrink: 0;
            box-shadow: 0 4px 12px ${config.primaryColor}30;
        }
        
        .send-button:hover:not(:disabled) { 
            transform: scale(1.08); 
            box-shadow: 0 6px 20px ${config.primaryColor}40;
        }
        
        .send-button:active:not(:disabled) {
            transform: scale(0.95);
        }
        
        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .send-button svg { 
            width: 20px; 
            height: 20px; 
            fill: white;
            transform: translateX(1px);
        }
        
        .messages::-webkit-scrollbar { 
            width: 6px; 
        }
        
        .messages::-webkit-scrollbar-track {
            background: transparent;
        }
        
        .messages::-webkit-scrollbar-thumb { 
            background: ${config.primaryColor}30; 
            border-radius: 3px;
            transition: background 0.2s ease;
        }
        
        .messages::-webkit-scrollbar-thumb:hover {
            background: ${config.primaryColor}50;
        }
        
        @media (max-width: 768px) { 
            .chat-container { 
                width: calc(100vw - 40px); 
                height: 500px;
                max-width: 420px;
            }
        }
        
        @media (max-width: 480px) { 
            #chatbot-widget {
                ${config.position}: 16px;
                bottom: 16px;
            }
            
            .chat-toggle {
                width: 60px;
                height: 60px;
            }
            
            .chat-toggle svg {
                width: 28px;
                height: 28px;
            }
            
            .chat-container { 
                width: calc(100vw - 32px); 
                height: calc(100vh - 120px);
                max-height: 600px;
                bottom: 80px;
            }
            
            .chat-header {
                padding: 20px;
            }
            
            .messages {
                padding: 20px;
            }
            
            .chat-input {
                padding: 16px 20px 20px;
            }
            
            .message-bubble {
                font-size: 14px;
                max-width: 85%;
            }
        }
        
        @media (max-width: 360px) {
            .chat-container {
                width: calc(100vw - 24px);
            }
        }
    `;
    
    const styleSheet = document.createElement('style');
    styleSheet.textContent = styles;
    document.head.appendChild(styleSheet);

    const widgetHTML = `
        <div id="chatbot-widget">
            <button class="chat-toggle" onclick="ChatbotWidget.toggle()">
                <svg viewBox="0 0 24 24"><path d="M20 2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/></svg>
            </button>
            <div class="chat-container" id="chat-container">
                <div class="chat-header">
                    <div class="chat-avatar"><svg width="22" height="22" viewBox="0 0 24 24" fill="white"><path d="M12 2C13.1 2 14 2.9 14 4C14 5.1 13.1 6 12 6C10.9 6 10 5.1 10 4C10 2.9 10.9 2 12 2ZM21 9V7L15 1L9 7V9C9 10.1 9.9 11 11 11V16L13 18L15 16V11C16.1 11 17 10.1 17 9H21Z"/></svg></div>
                    <div class="chat-info"><h3>${config.botName}</h3><div class="chat-status"><div class="status-dot"></div>Online</div></div>
                </div>
                <div class="messages" id="messages"></div>
                <div class="chat-input"><div class="input-group"><textarea class="message-input" id="message-input" placeholder="Type your message..." rows="1" onkeypress="ChatbotWidget.handleKeyPress(event)"></textarea><button class="send-button" onclick="ChatbotWidget.sendMessage()"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></button></div></div>
            </div>
        </div>
    `;

    function initWidget() {
        document.body.insertAdjacentHTML('beforeend', widgetHTML);

        window.ChatbotWidget = {
            isOpen: false,

            toggle() {
                const container = document.getElementById('chat-container');
                const toggle = document.querySelector('.chat-toggle');
                this.isOpen = !this.isOpen;
                if (this.isOpen) { container.classList.add('active'); toggle.classList.add('active'); }
                else { container.classList.remove('active'); toggle.classList.remove('active'); }
            },

            handleKeyPress(event) { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); this.sendMessage(); } },

            addMessage(type, content, qid = null) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${type}`;
                
                const bubbleDiv = document.createElement('div');
                bubbleDiv.className = 'message-bubble';
                bubbleDiv.innerHTML = content;
                messageDiv.appendChild(bubbleDiv);

                if (type === 'bot' && qid) {
                    const feedbackDiv = document.createElement('div');
                    feedbackDiv.className = 'feedback-container';
                    feedbackDiv.setAttribute('feedback-added', 'true');

                    const buttons = [
                        { 
                            label: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path d="M235.5 102.8C256.3 68 300.5 54 338 71.6L345.2 75.4C380 96.3 394 140.5 376.4 178L376.4 178L362.3 208L472 208L479.4 208.4C515.7 212.1 544 242.8 544 280C544 293.2 540.4 305.4 534.2 316C540.3 326.6 543.9 338.8 544 352C544 370.3 537.1 386.8 526 399.5C527.3 404.8 528 410.3 528 416C528 441.1 515.1 463 495.8 475.9C493.9 511.4 466.4 540.1 431.4 543.6L424 544L319.9 544C301.9 544 284 540.6 267.3 534.1L260.2 531.1L259.5 530.8L252.9 527.6L252.2 527.3L240 520.8C227.7 514.3 216.7 506.1 207.1 496.7C203 523.6 179.8 544.1 151.8 544.1L119.8 544.1C88.9 544.1 63.8 519 63.8 488.1L64 264C64 233.1 89.1 208 120 208L152 208C162.8 208 172.9 211.1 181.5 216.5L231.6 110L232.2 108.8L234.9 103.8L235.5 102.9zM120 256C115.6 256 112 259.6 112 264L112 488C112 492.4 115.6 496 120 496L152 496C156.4 496 160 492.4 160 488L160 264C160 259.6 156.4 256 152 256L120 256zM317.6 115C302.8 108.1 285.3 113.4 276.9 127L274.7 131L217.9 251.9C214.4 259.4 212.4 267.4 211.9 275.6L211.8 279.8L211.8 392.7L212 400.6C214.4 433.3 233.4 462.7 262.7 478.3L274.2 484.4L280.5 487.5C292.9 493.1 306.3 496 319.9 496L424 496L426.4 495.9C438.5 494.7 448 484.4 448 472L447.8 469.4C447.7 468.5 447.6 467.7 447.4 466.8C444.7 454.7 451.7 442.6 463.4 438.8C473.1 435.7 480 426.6 480 416C480 411.7 478.9 407.8 476.9 404.2C470.6 393.1 474.1 379 484.9 372.2C491.7 367.9 496.1 360.4 496.1 352C496.1 344.9 493 338.5 487.9 334C482.7 329.4 479.7 322.9 479.7 316C479.7 309.1 482.7 302.6 487.9 298C493 293.5 496.1 287.1 496.1 280L496 277.6C494.9 266.3 485.9 257.3 474.6 256.2L472.2 256.1L324.7 256.1C316.5 256.1 308.9 251.9 304.5 245C300.1 238.1 299.5 229.3 303 221.9L333 157.6C340 142.6 334.4 124.9 320.5 116.6L317.6 115z"/></svg>', 
                            value: 'satisfied', 
                            class: 'thumbs-up' 
                        },
                        { 
                            label: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><path d="M424 96L431.4 96.4C466.4 100 493.9 128.6 495.8 164.1C513.6 175.9 525.9 195.5 527.8 218L528 224C528 229.7 527.3 235.2 526 240.5C536.2 252 542.8 266.8 543.8 283.2L544 288C544 301.2 540.4 313.4 534.2 324C539.1 332.4 542.4 341.9 543.5 352L543.9 360C543.9 397.3 515.6 427.9 479.3 431.6L471.9 432L362.2 432L376.3 462L379.4 469.6C391.9 505.3 377.6 545.1 345.2 564.6L338 568.5C300.5 586.1 256.3 572.1 235.4 537.3L234.8 536.4L232.1 531.4L231.5 530.2L201.4 466.2C192 484 173.4 496.1 151.9 496.1L119.9 496.1C89 496.1 63.9 471 63.9 440.1L64 216C64 185.1 89.1 160 120 160L152 160C164.4 160 175.9 164.1 185.2 171C198.4 149.6 217.2 131.6 240.2 119.4L252.4 112.9L253.1 112.6L259.7 109.4L260.4 109.1L267.5 106.1C284.2 99.5 302 96.2 320.1 96.2L424 96zM319.9 144C307.9 144 296 146.3 284.8 150.6L280.1 152.6L274.8 155.2L274.8 155.2L262.6 161.7C233.4 177.2 214.3 206.6 211.9 239.3L211.7 247.3L211.7 360.2L211.8 364.3C212.3 372.5 214.3 380.5 217.8 388L274.6 508.9L276.7 512.7C285.1 526.4 302.7 531.8 317.5 524.9L320.4 523.3C333.4 515.5 339.1 499.6 334.1 485.3L332.9 482.3L302.7 418.1C299.2 410.7 299.8 402 304.2 395C308.6 388 316.2 383.9 324.4 383.9L471.9 383.9L474.3 383.8C485.6 382.7 494.6 373.7 495.7 362.4L495.8 359.9C495.8 352.8 492.7 346.4 487.6 341.9C482.4 337.3 479.4 330.8 479.4 323.9C479.4 317 482.4 310.5 487.6 305.9C492 302 495 296.6 495.6 290.6L495.8 287.9C495.8 279.5 491.4 272 484.6 267.7C473.9 260.8 470.4 246.8 476.6 235.7C478.1 233.1 479.1 230.1 479.5 227.1L479.7 223.9C479.7 213.3 472.8 204.3 463.1 201.1C451.4 197.3 444.4 185.2 447.1 173.1C447.3 172.2 447.4 171.3 447.5 170.5L447.7 167.9C447.7 155.5 438.2 145.3 426.1 144.1L424 144L319.9 144zM120 208C115.6 208 112 211.6 112 216L112 440C112 444.4 115.6 448 120 448L152 448C156.4 448 160 444.4 160 440L160 216C160 211.6 156.4 208 152 208L120 208z"/></svg>', 
                            value: 'not satisfied', 
                            class: 'thumbs-down' 
                        }
                    ];

                    buttons.forEach(btn => {
                        const b = document.createElement('button');
                        b.innerHTML = btn.label;
                        b.className = `feedback-button ${btn.class}`;
                        b.addEventListener('click', (e) => {
                            e.stopPropagation();
                            this.submitFeedback(qid, btn.value);
                            feedbackDiv.remove();
                        });
                        feedbackDiv.appendChild(b);
                    });

                    messageDiv.appendChild(feedbackDiv);
                }

                messagesDiv.appendChild(messageDiv);
                setTimeout(() => { messagesDiv.scrollTop = messagesDiv.scrollHeight; }, 100);
                this.saveHistory();
            },

            updateLastBotMessage(content, qid = null) {
                const messagesDiv = document.getElementById('messages');
                let lastMessage = messagesDiv.querySelector('.message.bot:last-child');
                if (!lastMessage) {
                    this.addMessage('bot', content, qid);
                    return;
                }
                let formattedContent = content
                    .replace(/\n/g, '<br>')
                    .replace(/- ([A-Z])/g, '<br>- $1');
                lastMessage.querySelector('.message-bubble').innerHTML = formattedContent;

                if (qid && !lastMessage.querySelector('.feedback-container[feedback-added]')) {
                    const bubble = lastMessage.querySelector('.message-bubble');
                    this.addMessage('bot', content, qid);
                    lastMessage.remove();
                }

                messagesDiv.scrollTop = messagesDiv.scrollHeight;
                this.saveHistory();
            },

            async submitFeedback(qid, feedback) {
                try {
                    await fetch(`${config.apiUrl}/feedback`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ qid, feedback })
                    });
                    console.log(`Feedback submitted for QID ${qid}: ${feedback}`);
                } catch (err) {
                    console.error('Failed to submit feedback', err);
                }
            },

            saveHistory() {
                const messagesDiv = document.getElementById('messages');
                const allMessages = [...messagesDiv.querySelectorAll('.message')].map(m => ({
                    type: m.classList.contains('user') ? 'user' :
                          m.classList.contains('bot') ? 'bot' : 'system',
                    content: m.querySelector('.message-bubble').innerHTML
                }));
                localStorage.setItem('chatHistory', JSON.stringify(allMessages));
            },

            loadHistory() {
                const saved = localStorage.getItem('chatHistory');
                if (!saved) {
                    this.addMessage('system', config.welcomeMessage);
                    return;
                }
                const messages = JSON.parse(saved);
                const messagesDiv = document.getElementById('messages');
                messagesDiv.innerHTML = "";
                for (let m of messages) {
                    this.addMessage(m.type, m.content);
                }
            },

            async sendMessage() {
                const input = document.getElementById("message-input");
                const message = input.value.trim();
                if (!message) return;

                const saved = localStorage.getItem('chatHistory');
                let lastThree = [];
                if (saved) {
                    const messages = JSON.parse(saved);
                    const qaPairs = [];
                    for (let i = 0; i < messages.length - 1; i++) {
                        if (messages[i].type === "user" && messages[i + 1]?.type === "bot") {
                            const ans = messages[i + 1].content.trim();
                            if (ans && ans !== "💭 ...") {
                                qaPairs.push({
                                    question: messages[i].content,
                                    answer: ans
                                });
                            }
                        }
                    }
                    lastThree = qaPairs.slice(-3);
                }

                this.addMessage('user', message);
                input.value = "";
                input.style.height = 'auto';

                this.updateLastBotMessage("💭 ...");

                try {
                    const response = await fetch(`${config.apiUrl}/chat`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ 
                            question: message,
                            history: lastThree
                        })
                    });

                    const qid = response.headers.get('X-QID') || null;

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder("utf-8");
                    let botMessage = "";

                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        const chunk = decoder.decode(value, { stream: true });
                        const lines = chunk.split("\n");
                        for (let line of lines) {
                            if (line.startsWith("data: ")) {
                                const token = line.slice(6);
                                if (token) {
                                    botMessage += token;
                                    this.updateLastBotMessage(botMessage, qid);
                                }
                            }
                        }
                    }

                } catch (err) {
                    console.error("Chat error:", err);
                    this.updateLastBotMessage("❌ Failed to reach server.");
                }
            }
        };

        document.addEventListener('click', function(event) {
            const chatContainer = document.getElementById('chat-container');
            const chatWidget = document.getElementById('chatbot-widget');
            
            if (event.target.closest('.feedback-container')) {
                return;
            }
            
            if (window.ChatbotWidget.isOpen && !chatWidget.contains(event.target)) {
                window.ChatbotWidget.toggle();
            }
        });

        const messageInput = document.getElementById('message-input');
        messageInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });

        window.ChatbotWidget.loadHistory();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWidget);
    } else {
        initWidget();
    }
})();
