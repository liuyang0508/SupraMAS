import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, Zap, Target } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  metadata?: Record<string, any>
}

interface ChatInterfaceProps {
  messages: Message[]
  onSendMessage: (content: string) => void
  isProcessing: boolean
  selectedDomain: string | null
}

export function ChatInterface({ messages, onSendMessage, isProcessing, selectedDomain }: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault()
    
    if (!inputValue.trim() || isProcessing) return
    
    onSendMessage(inputValue.trim())
    setInputValue('')
    
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const renderMessageContent = (content: string) => {
    // 简单的Markdown渲染（粗体、代码块）
    const parts = content.split(/(\*\*[^*]+\*\*)/g)
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i}>{part.slice(2, -2)}</strong>
      }
      // 处理代码块
      if (part.includes('```')) {
        const lines = part.split('```')
        return (
          <span key={i}>
            {lines[0]}
            <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-red-600 block my-1 overflow-x-auto">
              {lines[1]}
            </code>
            {lines[2]}
          </span>
        )
      }
      return <span key={i} dangerouslySetInnerHTML={{ __html: part.replace(/\n/g, '<br/>') }} />
    })
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((message) => (
          <div 
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              message.role === 'user' 
                ? 'bg-blue-500 text-white' 
                : message.metadata?.domain
                  ? 'bg-wukong-500 text-white'
                  : 'bg-gray-200 text-gray-600'
            }`}>
              {message.role === 'user' ? (
                <User size={16} />
              ) : (
                <Bot size={16} />
              )}
            </div>

            {/* Content Bubble */}
            <div className={`max-w-[75%] rounded-2xl px-4 py-3 ${
              message.role === 'user'
                ? 'bg-blue-500 text-white rounded-tr-none rounded-br-sm'
                : 'bg-white border border-gray-200 shadow-sm text-gray-800 rounded-tl-none rounded-bl-sm'
            }`}>
              {/* Metadata Header for Assistant */}
              {message.role === 'assistant' && message.metadata && Object.keys(message.metadata).length > 0 && (
                <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-100">
                  {message.metadata.domain && (
                    <span className="inline-flex items-center gap-1 text-xs bg-wukong-50 text-wukong-700 px-2 py-0.5 rounded-full font-medium">
                      <Target size={10} />
                      {message.metadata.domain}
                    </span>
                  )}
                  {message.metadata.intent && (
                    <span className="text-xs text-gray-400">
                      Intent: {message.metadata.intent}
                    </span>
                  )}
                </div>
              )}

              {/* Message Content */}
              <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                {renderMessageContent(message.content)}
              </div>

              {/* Timestamp */}
              <div className={`text-[10px] mt-2 ${message.role === 'user' ? 'text-right text-blue-100' : 'text-left text-gray-400'}`}>
                {message.timestamp.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        ))}

        {/* Processing Indicator */}
        {isProcessing && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-wukong-100 text-wukong-600 flex items-center justify-center animate-pulse">
              <Zap size={16} />
            </div>
            <div className="bg-white border border-wukong-200 rounded-2xl rounded-tl-none rounded-bl-sm px-4 py-3 shadow-sm">
              <div className="flex items-center gap-2 text-sm text-wukong-700">
                <Loader2 size={14} className="animate-spin" />
                <span>正在思考中...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        {/* Quick Actions */}
        {selectedDomain && (
          <div className="mb-3 flex items-center gap-2 text-xs text-wukong-600">
            <Zap size={12} />
            <span>当前模式：强制路由到 {selectedDomain} 专家</span>
            <button 
              onClick={() => onSendMessage('')}
              className="ml-auto underline hover:text-wukong-800"
            >
              切换为自动路由
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex gap-2 items-end">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={selectedDomain ? `向${selectedDomain}专家提问...` : "输入你的需求，AI将自动匹配最合适的专家..."}
              rows={1}
              className="w-full resize-none rounded-xl border border-gray-300 focus:border-wukong-500 focus:ring-2 focus:ring-wukong/20 px-4 py-3 pr-12 text-sm transition-all"
              disabled={isProcessing}
            />
            
            {/* Suggestion Chips */}
            {!inputValue && (
              <div className="absolute bottom-full left-0 mb-2 flex gap-1 flex-wrap">
                {['帮我分析市场趋势', '生成一份报告', '修复这个Bug'].slice(0, 3).map(suggestion => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setInputValue(suggestion)}
                    className="text-xs bg-gray-100 hover:bg-wukong-50 text-gray-600 hover:text-wukong-700 px-2 py-1 rounded-full transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <button
            type="submit"
            disabled={!inputValue.trim() || isProcessing}
            className="p-3 rounded-xl bg-wukong-600 text-white hover:bg-wukong-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            <Send size={18} />
          </button>
        </form>

        {/* Footer Hint */}
        <p className="mt-2 text-[11px] text-gray-400 text-center">
          Wukong AI 基于 Supervisor+SubAgent 多智能体架构 · 按 Enter 发送，Shift+Enter 换行
        </p>
      </div>
    </div>
  )
}
