"use client"

import { useState } from "react"
import { useChat } from "@ai-sdk/react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { CopilotChat } from "@copilotkit/react-ui"
import "@copilotkit/react-ui/styles.css";
import {
  Search,
  Sparkles,
  FileText,
  Twitter,
  TrendingUp,
  Send,
  User,
  ExternalLink,
  Globe,
  Brain,
  Zap,
  Star,
} from "lucide-react"
import { useCoAgent, useCoAgentStateRender } from "@copilotkit/react-core"
import { ToolLogs } from "@/components/ui/tool-logs"

const agents = [
  {
    id: "research",
    name: "Gemini Research",
    description: "Advanced multimodal research and analysis capabilities",
    icon: Search,
    gradient: "from-blue-500 to-purple-600",
    active: true,
  },
  {
    id: "content",
    name: "DeepMind Writer",
    description: "Scientific content generation with reasoning",
    icon: FileText,
    gradient: "from-green-500 to-teal-600",
    active: false,
  },
  {
    id: "social",
    name: "Gemini Social",
    description: "Intelligent social media content creation",
    icon: Twitter,
    gradient: "from-purple-500 to-pink-600",
    active: false,
  },
  {
    id: "trends",
    name: "DeepMind Analytics",
    description: "Advanced pattern recognition and trend analysis",
    icon: TrendingUp,
    gradient: "from-orange-500 to-red-600",
    active: false,
  },
]

const quickActions = [
  { label: "Research with Gemini", icon: Search, color: "text-blue-600" },
  { label: "Generate Analysis", icon: FileText, color: "text-green-600" },
  { label: "Create Social Thread", icon: Twitter, color: "text-purple-600" },
  { label: "Analyze Patterns", icon: TrendingUp, color: "text-orange-600" },
]

export default function GoogleDeepMindChatUI() {
  const [selectedAgent, setSelectedAgent] = useState(agents[0])
  

  const { state }  = useCoAgent({
    name : "post_generation_agent",
    initialState : {
      tool_logs : []
    }
  })

  useCoAgentStateRender({
    name : "post_generation_agent",
    render : (state) => {
      return <ToolLogs logs={state?.state?.tool_logs || []} />
    }
  })

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Sidebar */}
      <div className="w-80 bg-white/80 backdrop-blur-xl border-r border-gray-200/50 flex flex-col shadow-xl">
        {/* Header */}
        <div className="p-6 border-b border-gray-100/50">
          <div className="flex items-center gap-3 mb-4">
            <div className="relative">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg">
                <Brain className="w-6 h-6 text-white" />
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
                <Star className="w-2 h-2 text-white" />
              </div>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                DeepMind × Gemini
              </h1>
              <p className="text-sm text-gray-600">Advanced AI Research Platform</p>
            </div>
          </div>

          {/* Agent Selector */}
          <div className="space-y-3">
            <label className="text-sm font-semibold text-gray-700">Active Agent</label>
            <div className="relative">
              <select
                className="w-full p-4 border border-gray-200/50 rounded-xl bg-white/50 backdrop-blur-sm text-sm focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all duration-200 shadow-sm"
                value={selectedAgent.id}
                onChange={(e) => setSelectedAgent(agents.find((a) => a.id === e.target.value) || agents[0])}
              >
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id}>
                    {agent.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Agent Info */}
        <div className="p-6 border-b border-gray-100/50">
          <div className="flex items-start gap-4">
            <div
              className={`w-12 h-12 bg-gradient-to-r ${selectedAgent.gradient} rounded-xl flex items-center justify-center shadow-lg`}
            >
              <selectedAgent.icon className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <h3 className="font-semibold text-gray-900">{selectedAgent.name}</h3>
                <Badge className="bg-gradient-to-r from-blue-500 to-purple-500 text-white border-0 text-xs">
                  AI Agent
                </Badge>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">{selectedAgent.description}</p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        {/* <div className="p-6 flex-1">
          <h4 className="text-sm font-semibold text-gray-700 mb-4">Quick Actions</h4>
          <div className="space-y-3">
            {quickActions.map((action, index) => (
              <Button
                key={index}
                variant="ghost"
                className="w-full justify-start text-left h-auto p-4 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 rounded-xl transition-all duration-200 group"
                onClick={() => handleInputChange({ target: { value: action.label } } as any)}
              >
                <action.icon
                  className={`w-5 h-5 mr-3 ${action.color} group-hover:scale-110 transition-transform duration-200`}
                />
                <span className="text-sm font-medium">{action.label}</span>
              </Button>
            ))}
          </div>
        </div> */}
        <CopilotChat className="h-[420px]"/>
        {/* Input Form */}
        {/* <div className="p-6 border-t border-gray-100/50 bg-gradient-to-r from-blue-50/50 to-purple-50/50">
          <form onSubmit={handleSubmit} className="flex gap-3">
            <Input
              value={input}
              onChange={handleInputChange}
              placeholder="Ask your AI agent..."
              className="flex-1 border-gray-200/50 bg-white/70 backdrop-blur-sm focus:ring-2 focus:ring-blue-500/50 rounded-xl"
              disabled={isLoading}
            />
            <Button
              type="submit"
              size="icon"
              disabled={isLoading}
              className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 rounded-xl shadow-lg"
            >
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div> */}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent">
                  Research Workspace
                </h2>
                <p className="text-sm text-gray-600">Powered by Google DeepMind & Gemini AI</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge className="bg-gradient-to-r from-green-500 to-emerald-500 text-white border-0 shadow-sm">
                <div className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></div>
                Live Research
              </Badge>
              <div className="w-8 h-8 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
            </div>
          </div>
        </div>

        {/* Messages */}
        
      </div>
    </div>
  )
}
