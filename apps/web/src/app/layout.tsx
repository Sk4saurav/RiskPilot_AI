import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'RiskPilot',
  description: 'AI Risk Management Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <nav className="nav-sidebar">
          <div className="nav-brand">RiskPilot</div>
          <a href="/" className="nav-item">Case Queue</a>
          <a href="/integrations" className="nav-item">Integrations</a>
          <a href="/validation" className="nav-item">Alpha 0.6 Scorecard</a>
          <a href="/settings" className="nav-item">Settings</a>
          <a href="/onboarding" className="nav-item text-secondary">Onboarding (Debug)</a>
          <a href="/quickstart" className="nav-item text-secondary">Quickstart (Debug)</a>
          <div style={{ flex: 1 }}></div>
          <a href="/login" className="nav-item" style={{ marginTop: "auto" }}>Login / Switch Org</a>
        </nav>
        <main className="main-content">
          {children}
        </main>
      </body>
    </html>
  )
}
