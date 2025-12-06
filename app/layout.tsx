import type React from "react"
import type { Metadata } from "next"
import { Analytics } from "@vercel/analytics/next"
import { Suspense } from "react"
import "./globals.css"

export const metadata: Metadata = {
  title: "MCP-BD Explorer - Comprehensive Database of Bangladeshi Websites",
  description:
    "Discover and explore the digital landscape of Bangladesh. A comprehensive database of Bangladeshi websites, domains, and digital presence.",
  generator: "MCP-BD Explorer",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased">
        <Suspense fallback={<div>Loading...</div>}>{children}</Suspense>
        <Analytics />
      </body>
    </html>
  )
}
