import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Send, Bot, User, Loader2, Zap, Target, ChevronDown, ChevronRight, CheckCircle, XCircle, Clock, Network } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  metadata?: Record<string, any>
}

interface ExecutionChain {
  intent: string
  intent_confidence: number
  routing_decision: any
  optimized_query: string
  task_plan: any
  subtasks: Array<{
    task_id: string
    agent_type: string
    action: string
    params: any
    depends_on: string[]
    priority: number
    status: string
  }>
  completed_subtasks: Array<any>
  failed_subtasks: Array<any>
  security_decisions: Record<string, boolean>
  execution_metrics: {
    total_subtasks: number
    success_count: number
    fail_count: number
    success_rate: number
  }
  total_execution_time: number
}

interface ChatInterfaceProps {
  messages: Message[]
  onSendMessage: (content: string) => void
  isProcessing: boolean
  selectedDomain: string | null
}

export function ChatInterface({ messages, onSendMessage, isProcessing, selectedDomain }: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState('')
  const [expandedChain, setExpandedChain] = useState<Record<string, boolean>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const toggleChain = (messageId: string) => {
    setExpandedChain(prev => ({ ...prev, [messageId]: !prev[messageId] }))
  }

  const renderExecutionChain = (chain: ExecutionChain, messageId: string) => {
    const isExpanded = expandedChain[messageId]
    const { subtasks, completed_subtasks, failed_subtasks, execution_metrics, intent, intent_confidence, total_execution_time } = chain

    return (
      <div className="mt-3 border border-gray-200 rounded-lg overflow-hidden">
        {/* Chain Header */}
        <button
          onClick={() => toggleChain(messageId)}
          className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
        >
          <div className="flex items-center gap-3">
            <Network size={14} className="text-wukong-600" />
            <span className="text-xs font-medium text-gray-700">执行链路</span>
            <span className={`text-xs px-1.5 py-0.5 rounded ${
              intent_confidence >= 0.8 ? 'bg-green-100 text-green-700' :
              intent_confidence >= 0.6 ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-700'
            }`}>
              {intent} ({Math.round(intent_confidence * 100)}%)
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-gray-500">
              {completed_subtasks.length}/{subtasks.length} 成功 · {total_execution_time.toFixed(2)}s
            </span>
            {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </div>
        </button>

        {/* Chain Details */}
        {isExpanded && (
          <div className="p-3 bg-white space-y-2">
            {/* Intent Info */}
            <div className="text-xs text-gray-500 mb-2">
              优化查询: <span className="text-gray-700">{chain.optimized_query}</span>
            </div>

            {/* Subtasks List */}
            <div className="space-y-1">
              {subtasks.map((task, idx) => {
                const completed = completed_subtasks.find(s => s.task_id === task.task_id)
                const failed = failed_subtasks.find(s => s.task_id === task.task_id)
                const status = completed ? 'success' : failed ? 'failed' : 'pending'

                return (
                  <div key={task.task_id} className="flex items-center gap-2 text-xs">
                    <span className="w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] font-bold"
                          style={{ background: idx === 0 ? '#8B5CF6' : '#6366F1' }}>
                      {idx + 1}
                    </span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                      task.agent_type === 'rag' ? 'bg-blue-100 text-blue-700' :
                      task.agent_type === 'skill' ? 'bg-purple-100 text-purple-700' :
                      task.agent_type === 'file' ? 'bg-orange-100 text-orange-700' :
                      task.agent_type === 'mcp' ? 'bg-green-100 text-green-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {task.agent_type}
                    </span>
                    <span className="text-gray-700">{task.action}</span>
                    <span className="flex-1" />
                    {status === 'success' && <CheckCircle size={12} className="text-green-500" />}
                    {status === 'failed' && <XCircle size={12} className="text-red-500" />}
                    {status === 'pending' && <Clock size={12} className="text-gray-400" />}
                  </div>
                )
              })}
            </div>

            {/* Success Rate Bar */}
            <div className="mt-3 pt-2 border-t border-gray-100">
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="text-gray-500">成功率</span>
                <span className={`font-medium ${execution_metrics.success_rate >= 0.8 ? 'text-green-600' : execution_metrics.success_rate >= 0.5 ? 'text-yellow-600' : 'text-red-600'}`}>
                  {Math.round(execution_metrics.success_rate * 100)}%
                </span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    execution_metrics.success_rate >= 0.8 ? 'bg-green-500' :
                    execution_metrics.success_rate >= 0.5 ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{ width: `${execution_metrics.success_rate * 100}%` }}
                />
              </div>
            </div>

            {/* Failed Tasks Detail */}
            {failed_subtasks.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-100">
                <div className="text-xs text-red-500 font-medium mb-1">失败详情</div>
                {failed_subtasks.map(failed => (
                  <div key={failed.task_id} className="text-xs text-gray-600 pl-2 border-l-2 border-red-200">
                    <span className="font-mono text-red-600">{failed.task_id}</span>: {failed.error}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

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
    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, className, children, ...props }) {
            const inline = !className
            if (inline) {
              return <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-red-600" {...props}>{children}</code>
            }
            return (
              <code className="bg-gray-900 text-gray-100 px-4 py-3 rounded-lg text-sm font-mono block overflow-x-auto" {...props}>
                {children}
              </code>
            )
          },
          pre({ children }) {
            return <pre className="bg-gray-900 rounded-lg p-4 overflow-x-auto my-2">{children}</pre>
          },
          a({ href, children }) {
            return <a href={href} target="_blank" rel="noopener noreferrer" className="text-wukong-600 hover:text-wukong-800 underline">{children}</a>
          },
          ul({ children }) {
            return <ul className="list-disc list-inside space-y-1 my-2">{children}</ul>
          },
          ol({ children }) {
            return <ol className="list-decimal list-inside space-y-1 my-2">{children}</ol>
          },
          li({ children }) {
            return <li className="text-gray-700">{children}</li>
          },
          p({ children }) {
            return <p className="mb-2 last:mb-0">{children}</p>
          },
          h1({ children }) {
            return <h1 className="text-xl font-bold mb-2 text-gray-900">{children}</h1>
          },
          h2({ children }) {
            return <h2 className="text-lg font-bold mb-2 text-gray-900">{children}</h2>
          },
          h3({ children }) {
            return <h3 className="text-base font-bold mb-1 text-gray-900">{children}</h3>
          },
          blockquote({ children }) {
            return <blockquote className="border-l-4 border-wukong-300 pl-4 italic text-gray-600 my-2">{children}</blockquote>
          },
          table({ children }) {
            return <table className="min-w-full border border-gray-200 my-2">{children}</table>
          },
          th({ children }) {
            return <th className="border border-gray-200 bg-gray-50 px-3 py-1 text-left text-sm font-semibold">{children}</th>
          },
          td({ children }) {
            return <td className="border border-gray-200 px-3 py-1 text-sm">{children}</td>
          }
        }}
      >
        {content}
      </ReactMarkdown>
    )
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
                  {message.metadata.execution_chain && (
                    <span className="ml-auto text-xs px-1.5 py-0.5 bg-wukong-50 text-wukong-700 rounded font-medium">
                      {message.metadata.execution_chain.completed_subtasks?.length || 0}/{message.metadata.execution_chain.subtasks?.length || 0} 步骤
                    </span>
                  )}
                </div>
              )}

              {/* Message Content */}
              <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                {renderMessageContent(message.content)}
              </div>

              {/* Execution Chain (collapsible) */}
              {message.role === 'assistant' && message.metadata?.execution_chain && (
                renderExecutionChain(message.metadata.execution_chain, message.id)
              )}

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
