import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { CopilotKit } from "@copilotkit/react-core"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "DeepMind × Gemini - Advanced AI Research Platform",
  description: "Powered by Google's most advanced AI models for comprehensive research and analysis",
  generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <CopilotKit runtimeUrl="/api/copilotkit" agent="post_generation_agent">
        <body className={inter.className}>{children}</body>
      </CopilotKit>
    </html>
  )
}
