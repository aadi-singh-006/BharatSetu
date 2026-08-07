import { useEffect, useRef, useState } from 'react'
import { ArrowRight, Bot, Building2, ChevronRight, FileText, GraduationCap, HeartPulse, Landmark, Languages, Lightbulb, Menu, MessageCircle, Mic, Moon, Send, ShieldCheck, Sparkles, Sun, UserRound, Volume2, VolumeX, X } from 'lucide-react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const categories = [
  { title: 'Identity & Documents', copy: 'Aadhaar, PAN, passports and more', icon: FileText, color: 'blue' },
  { title: 'Government Schemes', copy: 'Benefits and public services', icon: Landmark, color: 'violet' },
  { title: 'Health & Wellness', copy: 'Care made easier to understand', icon: HeartPulse, color: 'rose' },
  { title: 'Education & Careers', copy: 'Scholarships and opportunities', icon: GraduationCap, color: 'amber' },
]
const suggestions = ['How do I apply for an Aadhaar card?', 'What documents are needed for a passport?', 'Am I eligible for PM Kisan?', 'Tell me about scholarships for students']

function GovernmentIllustration() {
  return <div className="relative mx-auto aspect-[1.15] w-full max-w-md overflow-hidden rounded-3xl border border-blue-100 bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-6 shadow-2xl shadow-blue-900/10"><div className="absolute right-7 top-7 h-16 w-16 rounded-full border-4 border-dashed border-blue-200" /><div className="absolute bottom-0 left-0 right-0 h-1/3 bg-blue-100/60" /><div className="relative flex h-full flex-col items-center justify-center"><div className="mb-3 grid h-14 w-14 place-items-center rounded-2xl bg-blue-600 text-white shadow-xl shadow-blue-600/30"><Building2 size={29} /></div><div className="flex items-end gap-2 text-blue-700"><span className="h-16 w-3 rounded-t-md bg-blue-200" /><span className="h-24 w-4 rounded-t-md bg-blue-600" /><span className="h-16 w-3 rounded-t-md bg-blue-200" /></div><div className="h-2 w-48 rounded-full bg-blue-800" /><div className="mt-1 h-1.5 w-56 rounded-full bg-blue-300" /><div className="mt-5 flex items-center gap-2 text-xs font-bold text-blue-700"><Landmark size={14} /> Services within reach</div></div></div>
}

function EmptyState({ language, onPrompt }) {
  return <div className="rounded-3xl border border-dashed border-blue-200 bg-blue-50/50 p-6 text-center dark:border-slate-700 dark:bg-slate-900/60"><div className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-white text-blue-600 shadow-sm dark:bg-slate-800"><Bot size={22} /></div><h2 className="font-bold text-slate-900 dark:text-white">{language === 'hi' ? 'बातचीत शुरू करें' : 'Start with a simple question'}</h2><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">{language === 'hi' ? 'किसी सरकारी सेवा या योजना के बारे में पूछें।' : 'Ask about a government service, document, scheme, or opportunity.'}</p><div className="mt-5 flex flex-wrap justify-center gap-2">{suggestions.slice(0, 3).map((prompt) => <button key={prompt} onClick={() => onPrompt(prompt)} className="rounded-full border border-blue-200 bg-white px-3 py-2 text-xs font-medium text-blue-700 transition hover:-translate-y-0.5 hover:border-blue-400 dark:border-slate-600 dark:bg-slate-800 dark:text-blue-300">{prompt}</button>)}</div></div>
}

function NotFound({ onHome }) {
  return <div className="grid min-h-[calc(100vh-73px)] place-items-center px-6 text-center"><div><div className="mx-auto mb-6 grid h-20 w-20 place-items-center rounded-3xl bg-blue-50 text-blue-600 dark:bg-slate-800"><Landmark size={36} /></div><p className="text-sm font-bold uppercase tracking-[.2em] text-blue-600">404</p><h1 className="mt-2 text-3xl font-bold text-slate-950 dark:text-white">This bridge is under construction.</h1><p className="mx-auto mt-3 max-w-md text-sm leading-6 text-slate-500">That page does not exist in this prototype. Return to BharatSetu and start a new conversation.</p><button onClick={onHome} className="mt-7 inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white hover:bg-blue-700">Back to home <ArrowRight size={16} /></button></div></div>
}

function InlineMarkdown({ text }) {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`|\[.*?\]\(https?:\/\/[^)]+\))/g)
  return parts.map((part, index) => {
    if (part.startsWith('**') && part.endsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>
    if (part.startsWith('`') && part.endsWith('`')) return <code className="rounded bg-slate-100 px-1.5 py-0.5 text-[.9em]" key={index}>{part.slice(1, -1)}</code>
    const link = part.match(/^\[(.*?)\]\((https?:\/\/[^)]+)\)$/)
    if (link) return <a className="font-semibold text-blue-600 underline" href={link[2]} key={index} target="_blank" rel="noreferrer">{link[1]}</a>
    return <span key={index}>{part}</span>
  })
}

function MarkdownText({ text }) {
  const lines = text.split('\n')
  const blocks = []
  let list = []
  const flushList = () => { if (list.length) { blocks.push(<ul className="my-2 list-disc space-y-1 pl-5" key={`list-${blocks.length}`}>{list}</ul>); list = [] } }
  lines.forEach((line, index) => {
    const bullet = line.match(/^\s*[-*]\s+(.*)$/)
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/)
    if (bullet || numbered) { list.push(<li key={index}><InlineMarkdown text={(bullet || numbered)[1]} /></li>); return }
    flushList()
    if (!line.trim()) { blocks.push(<div className="h-2" key={index} />); return }
    if (line.startsWith('### ')) blocks.push(<h4 className="mt-3 font-bold text-slate-900" key={index}><InlineMarkdown text={line.slice(4)} /></h4>)
    else if (line.startsWith('## ')) blocks.push(<h3 className="mt-3 text-base font-bold text-slate-900" key={index}><InlineMarkdown text={line.slice(3)} /></h3>)
    else if (line.startsWith('# ')) blocks.push(<h2 className="mt-3 text-lg font-bold text-slate-900" key={index}><InlineMarkdown text={line.slice(2)} /></h2>)
    else blocks.push(<p key={index}><InlineMarkdown text={line} /></p>)
  })
  flushList()
  return <div className="markdown-content">{blocks}</div>
}

function Brand() {
  return <a href="#top" className="flex items-center gap-2.5 text-base font-bold text-slate-950"><span className="grid h-9 w-9 place-items-center rounded-xl bg-blue-600 text-white shadow-lg shadow-blue-600/20"><Languages size={19} /></span>BharatSetu <span className="text-blue-600">AI</span></a>
}

function Navbar({ onChat, darkMode, setDarkMode, language, setLanguage }) {
  const [open, setOpen] = useState(false)
  return <nav className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/85 backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/85"><div className="mx-auto flex h-[72px] max-w-7xl items-center justify-between px-5 sm:px-8"><Brand /><div className="hidden items-center gap-8 text-sm font-medium text-slate-500 md:flex"><a className="text-blue-600" href="#top">Home</a><a className="hover:text-slate-900 dark:hover:text-white" href="#categories">Explore services</a><a className="hover:text-slate-900 dark:hover:text-white" href="#about">About us</a></div><div className="flex items-center gap-2"><button title="Switch language" onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')} className="rounded-lg px-2.5 py-2 text-xs font-bold text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">{language === 'en' ? 'हिन्दी' : 'English'}</button><button title={darkMode ? 'Use light mode' : 'Use dark mode'} aria-label="Toggle dark mode" onClick={() => setDarkMode(!darkMode)} className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">{darkMode ? <Sun size={17} /> : <Moon size={17} />}</button><button onClick={onChat} className="hidden items-center gap-2 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-600/20 hover:bg-blue-700 sm:flex">Ask BharatSetu <ArrowRight size={16} /></button><button aria-label="Toggle menu" onClick={() => setOpen(!open)} className="rounded-lg p-2 text-slate-600 dark:text-slate-300 md:hidden">{open ? <X size={22} /> : <Menu size={22} />}</button></div></div>{open && <div className="border-t border-slate-100 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-950 md:hidden"><div className="flex flex-col gap-4 text-sm font-medium text-slate-600 dark:text-slate-300"><a href="#top" onClick={() => setOpen(false)}>Home</a><a href="#categories" onClick={() => setOpen(false)}>Explore services</a><a href="#about" onClick={() => setOpen(false)}>About us</a><button onClick={() => { setOpen(false); onChat() }} className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 font-semibold text-white">Ask BharatSetu <ArrowRight size={16} /></button></div></div>}</nav>
}

function HomePage({ onChat, onSuggestion }) {
  return <><section className="relative overflow-hidden bg-white" id="top"><div className="hero-grid absolute inset-0 opacity-60" /><div className="absolute -right-24 top-20 h-72 w-72 rounded-full bg-blue-100/60 blur-3xl" /><div className="relative mx-auto grid max-w-7xl gap-16 px-5 pb-20 pt-16 sm:px-8 lg:grid-cols-[1.05fr_.95fr] lg:items-center lg:pb-28 lg:pt-24"><div className="animate-rise"><div className="mb-7 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3.5 py-2 text-xs font-bold uppercase tracking-[.15em] text-blue-700"><Sparkles size={14} /> Your guide to public services</div><h1 className="max-w-3xl text-5xl font-bold leading-[1.08] tracking-tight text-slate-950 sm:text-6xl lg:text-[72px]">The bridge to a <span className="text-blue-600">better tomorrow.</span></h1><p className="mt-7 max-w-xl text-base leading-7 text-slate-500 sm:text-lg">Understand government services, discover opportunities, and get things done - simply, clearly, and in your language.</p><button onClick={onChat} className="mt-9 inline-flex items-center gap-3 rounded-xl bg-blue-600 px-5 py-3.5 text-sm font-bold text-white shadow-xl shadow-blue-600/20 transition hover:-translate-y-0.5 hover:bg-blue-700">Start a conversation <ArrowRight size={18} /></button><div className="mt-9 flex items-center gap-3 text-sm text-slate-400"><span className="flex -space-x-2">{['bg-blue-200 text-blue-700', 'bg-indigo-200 text-indigo-700', 'bg-sky-200 text-sky-700'].map((style) => <span key={style} className={`grid h-7 w-7 place-items-center rounded-full border-2 border-white ${style}`}><UserRound size={13} /></span>)}</span> Made for every Indian</div></div><div className="animate-float"><GovernmentIllustration /></div></div></section><section className="bg-slate-50/70 py-20" id="categories"><div className="mx-auto max-w-7xl px-5 sm:px-8"><div className="mb-9 flex items-end justify-between"><div><p className="mb-2 text-xs font-bold uppercase tracking-[.16em] text-blue-600">Explore</p><h2 className="text-3xl font-bold tracking-tight text-slate-950">How can we help?</h2></div><button onClick={onChat} className="hidden items-center gap-1 text-sm font-bold text-blue-600 sm:flex">View all <ArrowRight size={16} /></button></div><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{categories.map(({ title, copy, icon: Icon, color }) => <button key={title} onClick={onChat} className="group rounded-2xl border border-slate-200 bg-white p-5 text-left transition duration-300 hover:-translate-y-1 hover:border-blue-200 hover:shadow-xl hover:shadow-blue-900/5"><span className={`icon-${color} mb-10 grid h-11 w-11 place-items-center rounded-xl transition group-hover:rotate-6`}><Icon size={21} /></span><h3 className="font-bold text-slate-900">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-500">{copy}</p><span className="mt-5 inline-flex items-center gap-1 text-xs font-bold text-blue-600 opacity-0 transition group-hover:opacity-100">Ask about it <ArrowRight size={13} /></span></button>)}</div></div></section><section className="bg-white py-20" id="about"><div className="mx-auto grid max-w-7xl gap-10 px-5 sm:px-8 lg:grid-cols-2 lg:items-end"><div><p className="mb-2 text-xs font-bold uppercase tracking-[.16em] text-blue-600">Start with a question</p><h2 className="text-3xl font-bold tracking-tight text-slate-950">No jargon. No confusion.</h2><p className="mt-4 max-w-lg leading-7 text-slate-500">Ask in English, Hindi, or the language you are most comfortable with. BharatSetu finds the right path forward.</p></div><div className="grid gap-3 sm:grid-cols-2">{suggestions.map((question) => <button key={question} onClick={() => onSuggestion(question)} className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 text-left text-sm font-medium text-slate-600 transition hover:-translate-y-0.5 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"><span>{question}</span><ChevronRight className="ml-3 shrink-0" size={16} /></button>)}</div></div></section></>
}

function EnhancedChatPage({ initialMessage, language }) {
  const [input, setInput] = useState(initialMessage)
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)
  const [speaking, setSpeaking] = useState(false)
  const [speechError, setSpeechError] = useState('')
  const bottomRef = useRef(null)
  const recognitionRef = useRef(null)
  const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window
  const canListen = typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, loading])
  useEffect(() => () => { recognitionRef.current?.stop(); window.speechSynthesis?.cancel() }, [])

  const toggleListening = () => {
    if (!canListen) { setSpeechError(language === 'hi' ? 'इस ब्राउज़र में आवाज़ इनपुट उपलब्ध नहीं है।' : 'Voice input is not supported in this browser.'); return }
    if (listening) { recognitionRef.current?.stop(); setListening(false); return }
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new Recognition()
    recognition.lang = language === 'hi' ? 'hi-IN' : 'en-IN'
    recognition.interimResults = false
    recognition.onstart = () => { setSpeechError(''); setListening(true) }
    recognition.onresult = (event) => setInput((value) => `${value}${value ? ' ' : ''}${event.results[0][0].transcript}`)
    recognition.onerror = () => { setListening(false); setSpeechError(language === 'hi' ? 'आवाज़ समझ नहीं आई। कृपया फिर कोशिश करें।' : 'I could not hear that. Please try again.') }
    recognition.onend = () => setListening(false)
    recognitionRef.current = recognition
    try { recognition.start() } catch { setListening(false); setSpeechError('Voice input could not start. Please try again.') }
  }

  const speak = (text) => {
    if (!canSpeak) { setSpeechError('Voice output is not supported in this browser.'); return }
    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text.replace(/[*#`]/g, ''))
    utterance.lang = language === 'hi' ? 'hi-IN' : 'en-IN'
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => { setSpeaking(false); setSpeechError('Voice output could not be played.') }
    setSpeaking(true)
    window.speechSynthesis.speak(utterance)
  }

  const sendMessage = async (event, suggestedMessage) => {
    event?.preventDefault()
    const message = (suggestedMessage || input).trim()
    if (!message || loading) return
    setInput(''); setSpeechError(''); setMessages((items) => [...items, { role: 'user', text: message }]); setLoading(true)
    try {
      const response = await fetch(`${API_URL}/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message }) })
      let data = null
      try { data = await response.json() } catch { throw new Error('Invalid server response') }
      if (!response.ok) throw new Error(data?.error?.message || data?.detail || 'The assistant is temporarily unavailable.')
      setMessages((items) => [...items, { role: 'assistant', text: typeof data.reply === 'string' ? data.reply : 'I received an empty response.' }])
    } catch (error) { setMessages((items) => [...items, { role: 'assistant', text: `**Sorry, I could not answer that.**\n\n${error.message || 'Please try again.'}` }]) }
    finally { setLoading(false) }
  }

  return <div className="mx-auto flex min-h-[calc(100vh-73px)] max-w-7xl bg-white dark:bg-slate-950"><aside className="hidden w-64 shrink-0 border-r border-slate-200 px-5 py-7 dark:border-slate-800 lg:block"><div className="mb-8 flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white"><MessageCircle className="text-blue-600" size={18} /> {language === 'hi' ? 'नई बातचीत' : 'New conversation'}</div><p className="mb-3 text-[10px] font-bold uppercase tracking-[.15em] text-slate-400">{language === 'hi' ? 'श्रेणियां' : 'Categories'}</p><div className="space-y-1">{categories.map(({ title, icon: Icon }) => <button key={title} onClick={() => setInput(`Tell me about ${title}`)} className="flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm text-slate-500 hover:bg-blue-50 hover:text-blue-700 dark:hover:bg-slate-800"><Icon size={16} /> {title}</button>)}</div></aside><section className="flex min-w-0 flex-1 flex-col px-4 py-6 sm:px-10 sm:py-8"><div className="mx-auto flex w-full max-w-3xl flex-1 flex-col"><div className="mb-6 sm:mb-8"><div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[.14em] text-blue-600"><ShieldCheck size={14} /> BharatSetu AI</div><h1 className="text-2xl font-bold tracking-tight text-slate-950 dark:text-white sm:text-3xl">{language === 'hi' ? 'आज मैं आपकी कैसे मदद कर सकता हूं?' : 'How can I help you today?'}</h1><p className="mt-2 text-sm text-slate-500">{language === 'hi' ? 'जानकारी सभी के लिए आसान।' : 'Information made simple, for everyone.'}</p></div><div className="flex-1 space-y-5">{messages.length === 0 && <EmptyState language={language} onPrompt={(prompt) => sendMessage(null, prompt)} />}{messages.map((message, index) => <div key={`${message.role}-${index}`} className={`animate-rise flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>{message.role === 'assistant' && <span className="mt-1 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-blue-600 text-white"><Bot size={16} /></span>}<div className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 sm:max-w-[85%] ${message.role === 'user' ? 'rounded-tr-sm bg-blue-600 text-white' : 'rounded-tl-sm border border-slate-200 bg-white text-slate-600 shadow-sm dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300'}`}>{message.role === 'assistant' ? <><MarkdownText text={message.text} /><button title={speaking ? 'Stop speaking' : 'Read aloud'} onClick={() => speaking ? (window.speechSynthesis.cancel(), setSpeaking(false)) : speak(message.text)} className="mt-2 rounded-lg p-1 text-slate-400 hover:bg-blue-50 hover:text-blue-600">{speaking ? <VolumeX size={15} /> : <Volume2 size={15} />}</button></> : message.text}</div></div>)}{loading && <div className="flex items-center gap-3"><span className="grid h-8 w-8 place-items-center rounded-xl bg-blue-50 text-blue-600"><Bot size={16} /></span><div className="space-y-2"><div className="skeleton-line w-40" /><div className="skeleton-line w-24" /></div></div>}<div ref={bottomRef} /></div><form onSubmit={sendMessage} className="sticky bottom-2 mt-8 flex items-center gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-lg shadow-slate-900/10 focus-within:border-blue-400 focus-within:ring-4 focus-within:ring-blue-50 dark:border-slate-700 dark:bg-slate-900"><button type="button" title={listening ? 'Stop listening' : 'Voice input'} aria-label="Voice input" onClick={toggleListening} className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl ${listening ? 'bg-rose-100 text-rose-600' : 'text-slate-400 hover:bg-blue-50 hover:text-blue-600'}`}><Mic size={17} /></button><input value={input} onChange={(event) => setInput(event.target.value)} placeholder={language === 'hi' ? 'सरकारी सेवा के बारे में पूछें...' : 'Ask about a government service...'} className="min-w-0 flex-1 bg-transparent px-1 py-2 text-sm outline-none placeholder:text-slate-400 dark:text-white" /><button aria-label="Send message" disabled={loading} className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"><Send size={17} /></button></form>{speechError && <p role="status" className="mt-2 text-center text-xs text-rose-600">{speechError}</p>}<p className="mt-3 text-center text-[11px] text-slate-400">{language === 'hi' ? 'AI की जानकारी में गलतियां हो सकती हैं।' : 'BharatSetu AI can make mistakes. Always verify details on official websites.'}</p></div></section></div>
}

function App() {
  const [page, setPage] = useState('home')
  const [initialMessage, setInitialMessage] = useState('')
  const [darkMode, setDarkMode] = useState(() => localStorage.getItem('bharatsetu-theme') === 'dark')
  const [language, setLanguage] = useState(() => localStorage.getItem('bharatsetu-language') || 'en')
  useEffect(() => { document.documentElement.classList.toggle('dark', darkMode); localStorage.setItem('bharatsetu-theme', darkMode ? 'dark' : 'light') }, [darkMode])
  useEffect(() => { localStorage.setItem('bharatsetu-language', language) }, [language])
  const openChat = (message = '') => { setInitialMessage(message); setPage('chat'); window.scrollTo({ top: 0, behavior: 'smooth' }) }
  const isNotFound = window.location.pathname !== '/' && window.location.pathname !== '/chat'
  return <main className="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100"><Navbar onChat={() => openChat()} darkMode={darkMode} setDarkMode={setDarkMode} language={language} setLanguage={setLanguage} />{isNotFound ? <NotFound onHome={() => { window.history.pushState({}, '', '/'); setPage('home') }} /> : page === 'home' ? <HomePage onChat={() => openChat()} onSuggestion={openChat} /> : <EnhancedChatPage initialMessage={initialMessage} language={language} />}</main>
}

export default App