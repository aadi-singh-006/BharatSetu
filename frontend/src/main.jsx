import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

class ErrorBoundary extends React.Component {
  state = { hasError: false }
  static getDerivedStateFromError() { return { hasError: true } }
  componentDidCatch(error) { console.error('BharatSetu UI error', error) }
  render() {
    if (!this.state.hasError) return this.props.children
    return <div className="grid min-h-screen place-items-center bg-slate-50 p-6 text-center"><div className="max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl"><h1 className="text-xl font-bold text-slate-900">BharatSetu needs a refresh</h1><p className="mt-2 text-sm leading-6 text-slate-500">Something unexpected happened. Reload the page to continue your conversation.</p><button className="mt-6 rounded-xl bg-blue-600 px-4 py-3 text-sm font-bold text-white" onClick={() => window.location.reload()}>Reload BharatSetu</button></div></div>
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary><App /></ErrorBoundary>
  </React.StrictMode>,
)