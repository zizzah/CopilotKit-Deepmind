"use client"

import { usePathname } from 'next/navigation'
import React, { createContext, useContext, useState, ReactNode } from 'react'

interface LayoutState {
  title: string
  description: string
  showHeader: boolean
  headerContent?: ReactNode
  sidebarContent?: ReactNode
  theme: 'light' | 'dark' | 'auto'
  agent: string
}

interface LayoutContextType {
  layoutState: LayoutState
  updateLayout: (updates: Partial<LayoutState>) => void
  resetLayout: () => void 
}

const defaultLayoutState: LayoutState = {
  title: "DeepMind × Gemini",
  description: "Powered by Google's most advanced AI models for generating LinkedIn and X posts",
  showHeader: true,
  theme: 'light',
  agent: "post_generation_agent"
}

const LayoutContext = createContext<LayoutContextType | undefined>(undefined)

export function LayoutProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname()
  const [layoutState, setLayoutState] = useState<LayoutState>({...defaultLayoutState, agent: pathname.includes("post-generator") ? "post_generation_agent" : "stack_analysis_agent"})

  const updateLayout = (updates: Partial<LayoutState>) => {
    setLayoutState(prev => ({ ...prev, ...updates }))
  }

  const resetLayout = () => {
    setLayoutState(defaultLayoutState)
  }

  return (
    <LayoutContext.Provider value={{ layoutState, updateLayout, resetLayout }}>
      {children}
    </LayoutContext.Provider>
  )
}

export function useLayout() {
  const context = useContext(LayoutContext)
  if (context === undefined) {
    throw new Error('useLayout must be used within a LayoutProvider')
  }
  return context
} 