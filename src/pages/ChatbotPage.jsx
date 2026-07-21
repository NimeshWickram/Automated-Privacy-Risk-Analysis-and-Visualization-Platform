import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, Loader2, MessageSquare } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';

const INITIAL_SUGGESTIONS = [
  "What personal data does Google Classroom collect?",
  "What happens if someone uses a stolen card on Duolingo?",
  "Is Khan Academy Kids safe for my child?",
  "Compare all apps — which is safest?",
  "Tell me about student marks security",
  "What security breaches has Photomath had?",
];

export default function ChatbotPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState(INITIAL_SUGGESTIONS);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const [hasStarted, setHasStarted] = useState(false);
  const [searchParams] = useSearchParams();
  const appId = searchParams.get('appId');

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (text) => {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    setHasStarted(true);
    setInput('');

    // Add user message
    const userMsg = { role: 'user', content: messageText, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);

    try {
      const body = { message: messageText };
      if (appId) {
        body.app_id = parseInt(appId, 10);
      }
      const res = await fetch('/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!res.ok) throw new Error('Failed to get response');
      const data = await res.json();

      const botMsg = {
        role: 'bot',
        content: data.response,
        suggestions: data.suggestions || [],
        intent: data.intent,
        appDetected: data.app_detected,
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, botMsg]);
      setSuggestions(data.suggestions || []);
    } catch (err) {
      const errorMsg = {
        role: 'bot',
        content: '❌ Sorry, I encountered an error. Please make sure the backend server is running and try again.',
        suggestions: [],
        timestamp: Date.now(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="responsive-container max-w-4xl! py-4 sm:py-6 flex flex-col" style={{ height: 'calc(100vh - 7rem)' }}>
      {/* Header */}
      <div className="mb-4 sm:mb-6 animate-fade-in-up">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight mb-1">
          AI Privacy <span className="gradient-text">Advisor</span>
        </h1>
        <p className="text-sm text-slate-400 font-medium">
          Ask questions about app privacy, payment security, student data safety, and more.
        </p>
      </div>

      {/* Chat Area */}
      <div className="bento-card flex-1 flex flex-col overflow-hidden animate-fade-in-up stagger-2">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {!hasStarted ? (
            /* Welcome State */
            <div className="flex flex-col items-center justify-center h-full text-center py-8">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-6 shadow-lg shadow-indigo-500/20">
                <Bot className="w-10 h-10 text-white" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Privacy Analysis Assistant</h2>
              <p className="text-sm text-slate-400 max-w-md mb-8">
                I can help you understand privacy risks, payment security, personal data collection,
                and security incidents for educational Android apps.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
                {INITIAL_SUGGESTIONS.map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(suggestion)}
                    className="text-left px-4 py-3 rounded-xl bg-slate-800/40 border border-slate-700/30 text-sm text-slate-300 hover:bg-slate-800/70 hover:border-indigo-500/30 hover:text-white transition-all group"
                  >
                    <span className="text-indigo-400 mr-2 group-hover:text-indigo-300">→</span>
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Message History */
            <>
              {messages.map((msg, i) => (
                <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.role === 'bot' && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0 mt-1">
                      <Bot size={16} className="text-white" />
                    </div>
                  )}
                  <div className={`max-w-[85%] sm:max-w-[75%] ${msg.role === 'user' ? 'order-first' : ''}`}>
                    <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-indigo-600 text-white rounded-tr-md'
                        : 'bg-slate-800/60 text-slate-200 rounded-tl-md border border-slate-700/30'
                    }`}>
                      {msg.role === 'bot' ? (
                        <FormattedBotMessage content={msg.content} />
                      ) : (
                        msg.content
                      )}
                    </div>

                    {/* Suggestions after bot messages */}
                    {msg.role === 'bot' && msg.suggestions && msg.suggestions.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {msg.suggestions.map((s, j) => (
                          <button
                            key={j}
                            onClick={() => sendMessage(s)}
                            className="text-[11px] px-2.5 py-1.5 rounded-lg bg-slate-800/40 border border-slate-700/30 text-slate-400 hover:text-indigo-300 hover:border-indigo-500/30 transition-all"
                          >
                            {s}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  {msg.role === 'user' && (
                    <div className="w-8 h-8 rounded-xl bg-slate-700 flex items-center justify-center shrink-0 mt-1">
                      <User size={16} className="text-slate-300" />
                    </div>
                  )}
                </div>
              ))}

              {/* Loading indicator */}
              {loading && (
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shrink-0">
                    <Bot size={16} className="text-white" />
                  </div>
                  <div className="bg-slate-800/60 rounded-2xl rounded-tl-md px-4 py-3 border border-slate-700/30">
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                      <Loader2 size={14} className="animate-spin" />
                      <span>Analyzing...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input Area */}
        <div className="p-4 border-t border-slate-700/30 bg-slate-900/30">
          {/* Quick suggestions when in conversation */}
          {hasStarted && suggestions.length > 0 && !loading && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {suggestions.slice(0, 3).map((s, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(s)}
                  className="text-[10px] px-2 py-1 rounded-lg bg-slate-800/40 border border-slate-700/30 text-slate-500 hover:text-indigo-300 hover:border-indigo-500/30 transition-all"
                >
                  <Sparkles size={9} className="inline mr-1" />
                  {s}
                </button>
              ))}
            </div>
          )}
          <div className="flex items-center gap-3">
            <div className="flex-1 relative">
              <MessageSquare size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about app privacy, payment security, student data..."
                className="w-full bg-slate-800/50 border border-slate-700/50 rounded-xl pl-11 pr-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 transition-all placeholder:text-slate-600 font-medium"
                disabled={loading}
              />
            </div>
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || loading}
              className="p-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:from-indigo-400 hover:to-purple-500 transition-all hover:shadow-lg hover:shadow-indigo-500/25 disabled:hover:shadow-none shrink-0"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

/* Render bot messages with basic markdown-like formatting */
function FormattedBotMessage({ content }) {
  const lines = content.split('\n');
  return (
    <div className="space-y-1">
      {lines.map((line, i) => {
        // Bold text
        let formatted = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white font-semibold">$1</strong>');
        // Italic
        formatted = formatted.replace(/_(.*?)_/g, '<em class="text-slate-400 italic">$1</em>');

        if (line.startsWith('# ')) {
          return <h3 key={i} className="text-base font-bold text-white mt-2">{line.slice(2)}</h3>;
        }
        if (line.startsWith('## ')) {
          return <h4 key={i} className="text-sm font-bold text-slate-200 mt-2">{line.slice(3)}</h4>;
        }
        if (line.startsWith('- ') || line.startsWith('  - ')) {
          const indent = line.startsWith('  ') ? 'ml-4' : '';
          return (
            <div key={i} className={`flex items-start gap-1.5 ${indent}`}>
              <span className="text-indigo-400 mt-0.5 shrink-0">•</span>
              <span dangerouslySetInnerHTML={{ __html: formatted.replace(/^-\s*/, '').replace(/^\s*-\s*/, '') }} />
            </div>
          );
        }
        if (line.startsWith('|') && line.includes('|')) {
          // Simple table row rendering
          const cells = line.split('|').filter(c => c.trim());
          if (cells.every(c => c.trim().match(/^[-]+$/))) return null; // Skip separator rows
          return (
            <div key={i} className="flex gap-2 text-xs font-mono">
              {cells.map((cell, j) => (
                <span key={j} className="flex-1 px-1" dangerouslySetInnerHTML={{ __html: cell.trim().replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>') }} />
              ))}
            </div>
          );
        }
        if (line.trim() === '') return <div key={i} className="h-1" />;
        return <p key={i} dangerouslySetInnerHTML={{ __html: formatted }} />;
      })}
    </div>
  );
}
