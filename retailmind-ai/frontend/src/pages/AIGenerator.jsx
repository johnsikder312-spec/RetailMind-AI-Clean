import { useState } from 'react'
import { useTheme } from '../context/ThemeContext'
import { Sparkles, Save, Volume2, Globe } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function AIGenerator() {
  const { dark } = useTheme()
  const [inputText, setInputText] = useState('')
  const [language, setLanguage] = useState('english')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [saving, setSaving] = useState(false)

  const handleGenerate = async () => {
    if (!inputText.trim()) { toast.error('Please enter offer text'); return }
    setLoading(true)
    try {
      const res = await api.post('/api/ai/generate-offer', { input_text: inputText, language })
      setResult(res.data.offer_data)
      toast.success('Offer generated!')
    } catch (err) { toast.error(err.response?.data?.error || 'Generation failed') }
    finally { setLoading(false) }
  }

  const handleSave = async () => {
    if (!result) return
    setSaving(true)
    try {
      const res = await api.post('/api/offers', {
        title: result.title,
        description: result.description,
        announcement_text: result.announcement_text,
        discount_percent: result.discount_percent,
        start_date: result.start_date,
        end_date: result.end_date,
        language: result.language || language,
        is_active: true
      })
      const msg = res.data.announcement
        ? 'Offer saved! Announcement created with audio.'
        : 'Offer saved!'
      toast.success(msg)
    } catch (err) { toast.error('Failed to save offer') }
    finally { setSaving(false) }
  }

  const handlePlaySpeech = async () => {
    if (!result?.announcement_text) return
    try {
      const lang = result.language || language
      const res = await api.post('/api/tts/generate', { text: result.announcement_text, language: lang })
      if (res.data.audio_url) {
        const audio = new Audio(res.data.audio_url)
        audio.play()
        toast.success('Playing announcement')
      }
    } catch (err) { toast.error('TTS failed') }
  }

  const cardBg = dark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200'
  const inputCls = `w-full px-4 py-3 rounded-xl border text-sm ${dark ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-500' : 'bg-white border-gray-300 text-gray-900'}`

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><Sparkles className="w-6 h-6 text-indigo-500" /> AI Offer Generator</h1>
        <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Type a natural language description and AI will create a complete offer</p>
      </div>

      {/* Input Section */}
      <div className={`rounded-xl p-6 border ${cardBg}`}>
        <textarea
          className={`${inputCls} mb-4`}
          rows="3"
          placeholder='e.g., "Rice 20% off till Sunday" or "Basmati Rice buy 2 get 1 free this week"'
          value={inputText}
          onChange={e => setInputText(e.target.value)}
        />
        <div className="flex items-center gap-3 flex-wrap">
          <select value={language} onChange={e => setLanguage(e.target.value)} className={inputCls + ' w-auto'}>
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
            <option value="bengali">Bengali</option>
          </select>
          <button onClick={handleGenerate} disabled={loading}
            className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium hover:shadow-lg transition disabled:opacity-50">
            {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Sparkles className="w-5 h-5" />}
            Generate Offer
          </button>
        </div>
      </div>

      {/* Result */}
      {result && (
        <div className={`rounded-xl p-6 border ${cardBg} space-y-4`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <h3 className="text-lg font-bold">Generated Offer</h3>
              {result.language && (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-500 text-xs font-medium">
                  <Globe className="w-3 h-3" /> {result.language.charAt(0).toUpperCase() + result.language.slice(1)}
                </span>
              )}
            </div>
            <div className="flex gap-2">
              <button onClick={handlePlaySpeech} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-purple-500/10 text-purple-500 text-sm hover:bg-purple-500/20 transition">
                <Volume2 className="w-4 h-4" /> Play Audio
              </button>
              <button onClick={handleSave} disabled={saving}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-medium disabled:opacity-50">
                <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save Offer'}
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div><label className="text-xs text-gray-500">Title</label><input className={inputCls} value={result.title || ''} onChange={e => setResult({ ...result, title: e.target.value })} /></div>
            <div><label className="text-xs text-gray-500">Discount %</label><input className={inputCls} type="number" value={result.discount_percent || 0} onChange={e => setResult({ ...result, discount_percent: parseFloat(e.target.value) })} /></div>
            <div><label className="text-xs text-gray-500">Start Date</label><input className={inputCls} type="date" value={result.start_date || ''} onChange={e => setResult({ ...result, start_date: e.target.value })} /></div>
            <div><label className="text-xs text-gray-500">End Date</label><input className={inputCls} type="date" value={result.end_date || ''} onChange={e => setResult({ ...result, end_date: e.target.value })} /></div>
          </div>

          <div>
            <label className="text-xs text-gray-500">Description</label>
            <input className={inputCls} value={result.description || ''} onChange={e => setResult({ ...result, description: e.target.value })} />
          </div>

          <div>
            <label className="text-xs text-gray-500">Announcement Text (editable)</label>
            <textarea className={inputCls} rows="4" value={result.announcement_text || ''} onChange={e => setResult({ ...result, announcement_text: e.target.value })} />
          </div>
        </div>
      )}
    </div>
  )
}
