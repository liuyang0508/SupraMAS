import { useEffect, useState } from 'react'
import { ExternalLink } from 'lucide-react'

interface Skill {
  skill_id: string
  name: string
  display_name: string
  version: string
  description: string
  tags: string[]
  trigger_conditions?: {
    intent?: string[]
    keywords?: string[]
  }
  author?: string
}

const SKILL_ICONS: Record<string, string> = {
  price_compare: '🔍',
  meeting_summary: '📋',
  code_review: '🔒',
  data_report: '📊',
  xiaohongshu_copywriter: '✍️'
}

const SKILL_COLORS: Record<string, string> = {
  price_compare: 'from-orange-400 to-red-500',
  meeting_summary: 'from-blue-400 to-indigo-500',
  code_review: 'from-purple-400 to-pink-500',
  data_report: 'from-green-400 to-teal-500',
  xiaohongshu_copywriter: 'from-pink-400 to-rose-500'
}

export function SkillMarket() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/v1/skills/installed')
      .then(res => res.json())
      .then(data => {
        const skillList: Skill[] = []
        for (const skill_id of data.skills || []) {
          const manifest = getSkillManifest(skill_id)
          if (manifest) skillList.push(manifest)
        }
        setSkills(skillList)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">🧩</div>
          <p className="text-gray-500">加载中...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <p className="text-red-500">加载失败: {error}</p>
        </div>
      </div>
    )
  }

  if (skills.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">🧩</div>
          <h2 className="text-xl font-semibold text-gray-900">技能市场</h2>
          <p className="text-gray-500 mt-2 max-w-md mx-auto">
            暂无已安装技能
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-xl font-bold text-gray-900">技能市场</h2>
            <p className="text-gray-500 text-sm mt-1">已安装 {skills.length} 个技能</p>
          </div>
          <button className="px-4 py-2 bg-wukong-600 text-white rounded-lg text-sm hover:bg-wukong-700 transition-colors">
            浏览更多
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {skills.map(skill => {
            const icon = SKILL_ICONS[skill.skill_id] || '🔧'
            const colorClass = SKILL_COLORS[skill.skill_id] || 'from-gray-400 to-gray-500'

            return (
              <div
                key={skill.skill_id}
                className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow cursor-pointer group"
              >
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorClass} flex items-center justify-center text-2xl flex-shrink-0`}>
                    {icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="font-semibold text-gray-900">{skill.display_name}</h3>
                      <span className="text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">v{skill.version}</span>
                    </div>
                    <p className="text-sm text-gray-500 mt-1 line-clamp-2">{skill.description}</p>
                    <div className="flex items-center gap-2 mt-3">
                      {skill.tags?.slice(0, 3).map(tag => (
                        <span key={tag} className="text-xs bg-wukong-50 text-wukong-700 px-2 py-0.5 rounded-full">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-gray-100 flex items-center justify-between">
                  <span className="text-xs text-gray-400">by {skill.author || 'Wukong Team'}</span>
                  <button className="text-xs text-wukong-600 hover:text-wukong-800 font-medium flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    使用 <ExternalLink size={12} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function getSkillManifest(skillId: string): Skill | null {
  const manifests: Record<string, Skill> = {
    'price_compare': {
      skill_id: 'price_compare',
      name: '全网比价助手',
      display_name: '全网比价',
      version: '1.0.0',
      description: '支持京东、淘宝、拼多多、抖音等主流电商平台的价格比对，提供历史价格走势和全网最低价提示',
      tags: ['电商', '比价', '购物助手', '全网最低价'],
      author: 'Wukong Team'
    },
    'meeting_summary': {
      skill_id: 'meeting_summary',
      name: '会议纪要生成助手',
      display_name: '会议纪要',
      version: '1.0.0',
      description: '将会议内容整理成结构化纪要，包含待办事项、决策点、关键讨论内容，支持多角色识别',
      tags: ['效率工具', '会议', '纪要', '团队协作'],
      author: 'Wukong Team'
    },
    'code_review': {
      skill_id: 'code_review',
      name: '代码审查助手',
      display_name: 'Code Review',
      version: '1.0.0',
      description: '对代码进行安全和最佳实践审查，检查潜在bug、安全漏洞、代码规范问题，提供改进建议',
      tags: ['开发者工具', '代码审查', '质量保障', '安全'],
      author: 'Wukong Team'
    },
    'data_report': {
      skill_id: 'data_report',
      name: '数据分析报告生成',
      display_name: '数据报告',
      version: '1.0.0',
      description: '根据数据生成结构化的分析报告，支持趋势分析、异常检测、对比分析，自动生成业务洞察',
      tags: ['数据分析', '报告', 'BI', '商业智能'],
      author: 'Wukong Team'
    },
    'xiaohongshu_copywriter': {
      skill_id: 'xiaohongshu_copywriter',
      name: '小红书文案生成助手',
      display_name: '小红书爆款文案',
      version: '1.0.0',
      description: '生成小红书风格的种草文案，支持好物推荐、产品测评、探店打卡等，使用流行爆款语言风格',
      tags: ['内容创作', '小红书', '种草', '文案'],
      author: 'Wukong Team'
    }
  }
  return manifests[skillId] || null
}