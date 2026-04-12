import React from 'react'
import { 
  MessageSquare, 
  Puzzle, 
  ClipboardList, 
  Settings,
  Sparkles,
  Bot
} from 'lucide-react'

interface SidebarProps {
  activeView: 'chat' | 'skills' | 'tasks'
  onViewChange: (view: 'chat' | 'skills' | 'tasks') => void
  selectedDomain: string | null
  onDomainSelect: (domain: string | null) => void
  messageCount: number
}

const DOMAIN_LIST = [
  { id: 'ecommerce', name: '电商运营', icon: '🛒', color: 'bg-orange-100 text-orange-700' },
  { id: 'design', name: '设计创意', icon: '🎨', color: 'bg-pink-100 text-pink-700' },
  { id: 'finance', name: '财税管理', icon: '💰', color: 'bg-green-100 text-green-700' },
  { id: 'development', name: '软件开发', icon: '💻', color: 'bg-blue-100 text-blue-700' },
  { id: 'content', name: '内容创作', icon: '✍️', color: 'bg-purple-100 text-purple-700' },
  { id: 'customer-service', name: '智能客服', icon: '🎧', color: 'bg-yellow-100 text-yellow-700' },
]

export function Sidebar({ activeView, onViewChange, selectedDomain, onDomainSelect, messageCount }: SidebarProps) {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
      {/* Logo Area */}
      <div className="p-4 border-b border-gray-100">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-gradient-to-r from-wukong-50 to-purple-50">
          <span className="text-2xl">🐵</span>
          <div>
            <h2 className="font-bold text-gray-900 leading-tight">Wukong</h2>
            <p className="text-xs text-wukong-600">AI Workspace</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        <p className="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          主导航
        </p>
        
        <button
          onClick={() => onViewChange('chat')}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeView === 'chat' 
              ? 'bg-wukong-600 text-white shadow-md shadow-wukong/20' 
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
          }`}
        >
          <MessageSquare size={18} />
          <span>对话</span>
          {messageCount > 1 && (
            <span className={`ml-auto text-xs px-1.5 py-0.5 rounded-full ${
              activeView === 'chat' ? 'bg-white/20' : 'bg-gray-200 text-gray-600'
            }`}>
              {messageCount - 1}
            </span>
          )}
        </button>

        <button
          onClick={() => onViewChange('skills')}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeView === 'skills' 
              ? 'bg-wukong-600 text-white shadow-md' 
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
          }`}
        >
          <Puzzle size={18} />
          <span>技能市场</span>
        </button>

        <button
          onClick={() => onViewChange('tasks')}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            activeView === 'tasks' 
              ? 'bg-wukong-600 text-white shadow-md' 
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
          }`}
        >
          <ClipboardList size={18} />
          <span>任务中心</span>
        </button>

        {/* Domain Selector */}
        <p className="px-3 pt-4 mt-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
          🎯 业务领域专家
        </p>

        <div className="space-y-0.5">
          {/* All Domains */}
          <button
            onClick={() => onDomainSelect(null)}
            className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
              selectedDomain === null 
                ? 'bg-gray-100 text-gray-900 ring-2 ring-gray-300' 
                : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
            }`}
          >
            <Bot size={16} />
            <span>自动路由</span>
            {!selectedDomain && (
              <span className="ml-auto w-1.5 h-1.5 bg-wukong-500 rounded-full" />
            )}
          </button>

          {DOMAIN_LIST.map(domain => (
            <button
              key={domain.id}
              onClick={() => onDomainSelect(selectedDomain === domain.id ? null : domain.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                selectedDomain === domain.id 
                  ? `${domain.color} ring-2 ring-offset-1 ring-current` 
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
              }`}
            >
              <span>{domain.icon}</span>
              <span>{domain.name}</span>
            </button>
          ))}
        </div>
      </nav>

      {/* Bottom */}
      <div className="p-3 border-t border-gray-100 space-y-1">
        <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-gray-500 hover:bg-gray-100 hover:text-gray-700 transition-colors">
          <Settings size={16} />
          <span>设置</span>
        </button>
        
        <div className="flex items-center gap-2 px-3 py-2 text-xs text-gray-400">
          <Sparkles size={12} />
          <span>Powered by LangGraph + MCP</span>
        </div>
      </div>
    </aside>
  )
}
