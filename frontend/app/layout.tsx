import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { CopilotKit } from "@copilotkit/react-core"
import { LayoutProvider } from "./contexts/LayoutContext"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "DeepMind × Gemini",
  description: "Powered by Google's most advanced AI models for generating LinkedIn and X posts",
  generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <CopilotKit runtimeUrl="/api/copilotkit" agent="stack_analysis_agent">
        <body className={inter.className}>
          <LayoutProvider>
            {children}
          </LayoutProvider>
        </body>
      </CopilotKit>
    </html>
  )
}
