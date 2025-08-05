"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { CopilotChat, useCopilotChatSuggestions } from "@copilotkit/react-ui"
import "@copilotkit/react-ui/styles.css";
import { TextMessage, Role } from "@copilotkit/runtime-client-gql";
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
import { useCoAgent, useCoAgentStateRender, useCopilotAction, useCopilotChat } from "@copilotkit/react-core"
import { ToolLogs } from "@/components/ui/tool-logs"
import { XPost, XPostPreview, XPostCompact } from "@/components/ui/x-post"
import { LinkedInPost, LinkedInPostPreview, LinkedInPostCompact } from "@/components/ui/linkedin-post"
import { Button } from "@/components/ui/button"
import { initialPrompt, suggestionPrompt } from "./prompts/prompts"
import { Textarea } from "@/components/ui/textarea"


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
  { label: "Recent Research", icon: Search, color: "text-blue-600", prompt: "Generate a post about recent research on String Theory" },
  { label: "Recent News", icon: FileText, color: "text-green-600", prompt: "Generate a post about recent news in United States" },
  { label: "Post about Social Media", icon: Twitter, color: "text-purple-600", prompt: "Generate a post about Instagram" },
  { label: "Post about Stocks", icon: TrendingUp, color: "text-orange-600", prompt: "Generate a post about Nvidia" },
]

interface PostInterface {
  tweet: {
    title: string
    content: string
  }
  linkedIn: {
    title: string
    content: string
  }
}


export default function GoogleDeepMindChatUI() {
  const [selectedAgent, setSelectedAgent] = useState(agents[0])
  const [showColumns, setShowColumns] = useState(false)
  const [posts, setPosts] = useState<PostInterface>({ tweet: { title: "", content: "" }, linkedIn: { title: "", content: "" } })
  const [isAgentActive, setIsAgentActive] = useState(false)
  const { setState, running } = useCoAgent({
    name: "post_generation_agent",
    initialState: {
      tool_logs: []
    }
  })

  const { appendMessage } = useCopilotChat()


  useCoAgentStateRender({
    name: "post_generation_agent",
    render: (state) => {
      return <ToolLogs logs={state?.state?.tool_logs || []} />
    }
  })

  useCopilotAction({
    name: "generate_post",
    description: "Render a post",
    parameters: [
      {
        name: "tweet",
        type: "object",
        description: "The tweet to be rendered",
        attributes: [
          {
            name: "title",
            type: "string",
            description: "The title of the post"
          },
          {
            name: "content",
            type: "string",
            description: "The content of the post"
          }
        ]
      },
      {
        name: "linkedIn",
        type: "object",
        description: "The linkedIn post to be rendered",
        attributes: [
          {
            name: "title",
            type: "string",
            description: "The title of the post"
          },
          {
            name: "content",
            type: "string",
            description: "The content of the post"
          }
        ]
      }
    ],
    render: ({ args }) => {
      console.log("Rendering posts with args:", args)
      return <>
        <div className="px-2 mb-3">
          <XPostCompact title={args.tweet?.title || ""} content={args.tweet?.content || ""} />
        </div>
        <div className="px-2">
          <LinkedInPostCompact title={args.linkedIn?.title || ""} content={args.linkedIn?.content || ""} />
        </div>
      </>
    },
    handler: (args) => {
      console.log(args, "args")
      setShowColumns(true)
      setPosts({ tweet: args.tweet, linkedIn: args.linkedIn })
      setState((prevState) => ({
        ...prevState,
        tool_logs: []
      }))
    }
  })

  useCopilotChatSuggestions({
    available: "enabled",
    instructions: suggestionPrompt,
  })


  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 overflow-hidden">
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


        <CopilotChat className="h-[58vh]" labels={{
          initial: initialPrompt
        }}
          Input={({ onSend, inProgress }) => {
            useEffect(() => {
              if(inProgress) {
                setIsAgentActive(true)
              } else {
                setIsAgentActive(false)
              }
            }, [inProgress])
            const [input, setInput] = useState("")
            return (<>
              <div className="space-y-5 px-4 py-2">

                <form className="flex flex-col gap-3">
                  <Textarea
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Type your message..."
                    className="min-h-[80px] resize-none rounded-xl border-muted-foreground/20 p-3"
                  />
                  <Button disabled={inProgress}
                    onClick={(e) => {
                      e.preventDefault()
                      if(input.trim() === "") return
                      console.log("sending message")
                      onSend(input)
                      setInput("")
                    }} className="self-end rounded-xl px-5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 text-white">
                    <Send className="mr-2 h-4 w-4" />
                    Send
                  </Button>
                </form>
              </div>
            </>)
          }}
        />

      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-white/80 backdrop-blur-xl border-b border-gray-200/50 p-6 shadow-sm flex-shrink-0">
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
              {isAgentActive && <Badge className="bg-gradient-to-r from-green-500 to-emerald-500 text-white border-0 shadow-sm">
                <div className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></div>
                Live Research
              </Badge>}
              {/* <div className="w-8 h-8 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div> */}
            </div>
          </div>
        </div>

        {/* Main Canvas */}
        <div className="flex-1 p-6 overflow-y-auto">
          {showColumns ? (
            <div className="grid grid-cols-2 gap-6 min-h-full">
              {/* Left Column */}
              <div className="bg-white/60 backdrop-blur-sm rounded-xl border border-gray-200/50 shadow-sm p-6">
                <XPostPreview title={posts.tweet.title || ""} content={posts.tweet.content || ""} />
              </div>

              {/* Right Column */}
              <div className="bg-white/60 backdrop-blur-sm rounded-xl border border-gray-200/50 shadow-sm p-6">
                <LinkedInPostPreview title={posts.linkedIn.title || ""} content={posts.linkedIn.content || ""} />
              </div>
            </div>
          ) : (
            <div className="text-center py-16">
              <div className="relative mb-8">
                <div className="w-20 h-20 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center mx-auto shadow-2xl">
                  <Brain className="w-10 h-10 text-white" />
                </div>
              </div>
              <h3 className="text-2xl font-bold bg-gradient-to-r from-gray-900 via-blue-800 to-purple-800 bg-clip-text text-transparent mb-3">
                Ready to Explore
              </h3>
              <p className="text-gray-600 mb-8 max-w-md mx-auto leading-relaxed">
                Harness the power of Google's most advanced AI models for comprehensive research and analysis.
              </p>
              <div className="grid grid-cols-2 gap-4 max-w-lg mx-auto">
                {quickActions.slice(0, 4).map((action, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    disabled={running}
                    className="h-auto p-6 flex flex-col items-center gap-3 bg-white/50 backdrop-blur-sm border-gray-200/50 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 rounded-xl transition-all duration-300 group"
                    onClick={() => appendMessage(new TextMessage({
                      role: Role.User,
                      content: action.prompt
                    }))}
                  >
                    <action.icon
                      className={`w-6 h-6 ${action.color} group-hover:scale-110 transition-transform duration-200`}
                    />
                    <span className="text-sm font-medium">{action.label}</span>
                  </Button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div >
  )
}
