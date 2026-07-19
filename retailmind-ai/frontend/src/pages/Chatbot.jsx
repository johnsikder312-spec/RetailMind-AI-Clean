import { useState, useEffect, useRef } from 'react'
import { useTheme } from '../context/ThemeContext'
import { MessageSquare, Send, Trash2, Sparkles } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

const quickActions = [
  "What offers are active today?",
  "What products have low stock?",
  "Generate a Diwali promotion",
  "Show offers expiring tomorrow",
  "Suggest marketing tips",
]

export default function Chatbot() {
  const { dark } = useTheme()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => { fetchHistory() }, [])
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const fetchHistory = async () => {
    try {
      const res = await api.get('/api/chat/history')
      setMessages(res.data.messages || [])
    } catch (err) {}
  }

  const handleSend = async (text) => {
    const msg = text || input.trim()
    if (!msg) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: msg, timestamp: new Date().toISOString() }])
    setLoading(true)
    try {
      const res = await api.post('/api/chat/message', { message: msg })
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response, timestamp: new Date().toISOString() }])
    } catch (err) { toast.error('Failed to get response') }
    finally { setLoading(false) }
  }

  const handleClear = async () => {
    try {
      await api.post('/api/chat/clear')
      setMessages([])
      toast.success('Chat cleared')
    } catch (err) {}
  }

  const cardBg = dark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200'

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><MessageSquare className="w-6 h-6 text-indigo-500" /> AI Chatbot</h1>
          <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Ask anything about your store</p>
        </div>
        <button onClick={handleClear} className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm ${dark ? 'hover:bg-gray-800 text-gray-400' : 'hover:bg-gray-100 text-gray-500'}`}>
          <Trash2 className="w-4 h-4" /> Clear
        </button>
      </div>

      {/* Chat Window */}
      <div className={`rounded-xl border ${cardBg} flex flex-col h-[500px]`}>
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <Sparkles className="w-10 h-10 mx-auto text-indigo-500/50 mb-3" />
              <p className={`text-sm ${dark ? 'text-gray-500' : 'text-gray-400'}`}>Start a conversation with RetailMind AI</p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] px-4 py-3 rounded-2xl text-sm ${
                msg.role === 'user'
                  ? 'bg-indigo-500 text-white rounded-br-sm'
                  : dark ? 'bg-gray-700 text-gray-200 rounded-bl-sm' : 'bg-gray-100 text-gray-800 rounded-bl-sm'
              }`}>
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className={`px-4 py-3 rounded-2xl rounded-bl-sm ${dark ? 'bg-gray-700' : 'bg-gray-100'}`}>
                <div className="flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Actions */}
        <div className={`px-4 py-2 border-t flex gap-2 overflow-x-auto ${dark ? 'border-gray-700' : 'border-gray-200'}`}>
          {quickActions.map((action, i) => (
            <button key={i} onClick={() => handleSend(action)}
              className={`px-3 py-1.5 rounded-full text-xs whitespace-nowrap transition ${dark ? 'bg-gray-700 text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'}`}>
              {action}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className={`p-4 border-t ${dark ? 'border-gray-700' : 'border-gray-200'}`}>
          <div className="flex gap-2">
            <input
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSend()}
              placeholder="Ask a question..."
              className={`flex-1 px-4 py-2.5 rounded-xl border text-sm ${dark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-gray-50 border-gray-300'}`}
            />
            <button onClick={() => handleSend()} disabled={loading || !input.trim()}
              className="px-4 py-2.5 rounded-xl bg-indigo-500 text-white disabled:opacity-50 transition hover:bg-indigo-600">
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
