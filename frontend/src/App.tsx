import React, { useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { ChatInterface } from './components/chat/ChatInterface'
import { SkillMarket } from './components/skills/SkillMarket'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  metadata?: {
    domain?: string
    intent?: string
    subtasks?: number
    executionTime?: number
  }
}

function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: '🐵 你好！我是 **Wukong AI**，你的企业级AI工作助手。\n\n我可以帮你：\n- 🛒 **电商运营** - 选品分析、Listing生成、竞品调研\n- 🎨 **设计创意** - 品牌VI、营销物料、UI方案\n- 💰 **财税管理** - 发票处理、报表生成、合规检查\n- 💻 **软件开发** - 代码生成、Bug修复、部署上线\n- ✍️ **内容创作** - 文案撰写、SEO优化、社媒运营\n- 🎧 **智能客服** - 工单处理、FAQ匹配、情感分析\n\n请告诉我你需要什么帮助？',
      timestamp: new Date()
    }
  ])
  
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [activeView, setActiveView] = useState<'chat' | 'skills' | 'tasks'>('chat')

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }

    // Build the messages array for API including the new user message
    const messagesForApi = [...messages, userMessage]

    // Add user message to UI immediately
    setMessages(messagesForApi)
    setIsProcessing(true)

    try {
      const response = await fetch('/api/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: messagesForApi.map(m => ({ role: m.role, content: m.content })),
          stream: false,
          user_id: "demo-user",
          conversation_id: "session-demo"
        })
      })

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`)
      }

      const data = await response.json()
      const responseContent = data.choices?.[0]?.message?.content || ''

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseContent || '抱歉，处理您的请求时出现了问题。',
        timestamp: new Date(),
        metadata: data.metadata || {}
      }

      setMessages(prev => [...prev, assistantMessage])

    } catch (error) {
      console.error('Error:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `⚠️ 连接服务失败: ${error instanceof Error ? error.message : 'Unknown error'}\n\n请确保后端服务已启动。运行以下命令启动后端：\n\n\`\`\`bash\ncd /Users/liuyang/Desktop/AIAgent/wukongbox/wukong/backend\npip install -r requirements.txt\npython main.py\n\`\`\``,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar 
        activeView={activeView}
        onViewChange={setActiveView}
        selectedDomain={selectedDomain}
        onDomainSelect={setSelectedDomain}
        messageCount={messages.length}
      />
      
      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                🐵 Wukong AI
                <span className="text-sm font-normal text-wukong-600 bg-wukong-50 px-2 py-0.5 rounded-full">
                  v1.0.0
                </span>
              </h1>
              <p className="text-sm text-gray-500 mt-1">
                企业级AI原生工作平台 · Supervisor+SubAgent架构
              </p>
            </div>
            
            <div className="flex items-center gap-3">
              {selectedDomain && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-wukong-100 text-wukong-700 text-sm font-medium">
                  <span>🎯</span>
                  {getDomainDisplayName(selectedDomain)}
                </span>
              )}
              
              <div className={`w-2 h-2 rounded-full ${isProcessing ? 'bg-yellow-500 animate-pulse' : 'bg-green-500'}`} 
                   title={isProcessing ? '处理中...' : '就绪'} />
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {activeView === 'chat' && (
            <ChatInterface 
              messages={messages}
              onSendMessage={handleSendMessage}
              isProcessing={isProcessing}
              selectedDomain={selectedDomain}
            />
          )}
          
          {activeView === 'skills' && <SkillMarket onUseSkill={(skillId) => {
            const promptMap: Record<string, string> = {
              'price_compare': '帮我查一下iPhone17Promax的全网最低价',
              'meeting_summary': '帮我生成一份会议纪要：讨论产品上线计划，张三负责前端，李四负责后端',
              'code_review': '帮我审查一下这段代码：def login(password): eval(password)',
              'data_report': '帮我分析一下销售数据：本周比上周增长了20%',
              'xiaohongshu_copywriter': '帮我写一篇小红书种草文案，推荐一款精华液'
            }
            const prompt = promptMap[skillId] || `使用${skillId}技能`
            setActiveView('chat')
            handleSendMessage(prompt)
          }} />}
          
          {activeView === 'tasks' && (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">📋</div>
                <h2 className="text-xl font-semibold text-gray-900">任务中心</h2>
                <p className="text-gray-500 mt-2 max-w-md mx-auto">
                  查看历史任务执行状态、性能指标和执行日志
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

function getDomainDisplayName(domain: string): string {
  const names: Record<string, string> = {
    ecommerce: '电商运营专家',
    design: '设计创意专家',
    finance: '财税管理专家',
    development: '软件开发专家',
    content: '内容创作专家',
    'customer-service': '智能客服专家'
  }
  return names[domain] || domain
}

export default App
