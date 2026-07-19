import { useState, useCallback } from 'react'
import { useTheme } from '../context/ThemeContext'
import { ScanLine, Upload, Save, FileText, Sparkles, Volume2 } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function OCRScanner() {
  const { dark } = useTheme()
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [offerData, setOfferData] = useState(null)
  const [saving, setSaving] = useState(false)

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    const f = e.dataTransfer?.files?.[0] || e.target?.files?.[0]
    if (f && f.type.startsWith('image/')) {
      setFile(f)
      setPreview(URL.createObjectURL(f))
      setResult(null)
      setOfferData(null)
    }
  }, [])

  const handleScan = async () => {
    if (!file) { toast.error('Please upload an image first'); return }
    setLoading(true)
    setResult(null)
    setOfferData(null)
    try {
      const formData = new FormData()
      formData.append('image', file)
      const res = await api.post('/api/ocr/scan', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setResult(res.data)

      if (res.data.offer_data) {
        setOfferData(res.data.offer_data)
        toast.success('Image scanned and offer detected!')
      } else if (res.data.extracted_text) {
        // Text was extracted but no structured offer - send to AI generator
        toast.success('Text extracted! Sending to AI for offer generation...')
        try {
          const aiRes = await api.post('/api/ai/generate-offer', {
            input_text: res.data.extracted_text,
            language: 'english'
          })
          if (aiRes.data.offer_data) {
            setOfferData(aiRes.data.offer_data)
            toast.success('AI generated offer from extracted text!')
          }
        } catch (aiErr) {
          toast.error('AI generation failed, but text was extracted')
        }
      } else if (res.data.error) {
        toast.error(res.data.error)
      } else {
        toast.error('No text could be detected in this image')
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Scan failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSaveOffer = async () => {
    if (!offerData) return
    setSaving(true)
    try {
      await api.post('/api/offers', {
        title: offerData.title || 'OCR Scanned Offer',
        description: offerData.description || '',
        announcement_text: offerData.announcement_text || '',
        discount_percent: offerData.discount_percent || 0,
        start_date: offerData.start_date,
        end_date: offerData.end_date,
        is_active: true,
        language: offerData.language || 'english'
      })
      toast.success('Offer saved from scan!')
    } catch (err) { toast.error('Failed to save offer') }
    finally { setSaving(false) }
  }

  const handlePlaySpeech = async () => {
    if (!offerData?.announcement_text) return
    try {
      const res = await api.post('/api/tts/generate', {
        text: offerData.announcement_text,
        language: 'english'
      })
      if (res.data.audio_url) {
        const audio = new Audio(res.data.audio_url)
        audio.play()
        toast.success('Playing announcement')
      }
    } catch (err) { toast.error('TTS playback failed') }
  }

  const cardBg = dark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200'
  const inputCls = `w-full px-3 py-2 rounded-lg border text-sm ${dark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><ScanLine className="w-6 h-6 text-indigo-500" /> OCR Smart Scanner</h1>
        <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Upload posters, flyers, or offer images to auto-extract promotions</p>
      </div>

      {/* Upload Area */}
      <div className={`rounded-xl p-6 border ${cardBg}`}>
        <div
          onDrop={handleDrop}
          onDragOver={e => e.preventDefault()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition ${
            dark ? 'border-gray-600 hover:border-indigo-500' : 'border-gray-300 hover:border-indigo-500'
          }`}
        >
          <input type="file" accept="image/*" onChange={handleDrop} className="hidden" id="file-input" />
          <label htmlFor="file-input" className="cursor-pointer">
            <Upload className="w-12 h-12 mx-auto text-indigo-500 mb-3" />
            <p className="font-medium">Drop image here or click to upload</p>
            <p className={`text-sm mt-1 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>Supports: PNG, JPG, JPEG, GIF, WebP, BMP</p>
          </label>
        </div>

        {preview && (
          <div className="mt-4 flex items-center gap-4">
            <img src={preview} alt="Preview" className="w-24 h-24 rounded-lg object-cover border" />
            <div className="flex-1">
              <p className="text-sm font-medium">{file?.name}</p>
              <p className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>{(file?.size / 1024).toFixed(1)} KB</p>
            </div>
          </div>
        )}

        <button onClick={handleScan} disabled={loading || !file}
          className="mt-4 flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium hover:shadow-lg transition disabled:opacity-50">
          {loading ? <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <ScanLine className="w-5 h-5" />}
          {loading ? 'Scanning...' : 'Scan Image'}
        </button>
      </div>

      {/* Raw OCR Results */}
      {result && result.extracted_text && (
        <div className={`rounded-xl p-6 border ${cardBg} space-y-4`}>
          <h3 className="text-lg font-bold flex items-center gap-2"><FileText className="w-5 h-5" /> Extracted Text</h3>
          <div className={`p-4 rounded-lg text-sm whitespace-pre-wrap ${dark ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
            {result.extracted_text}
          </div>
          <div className="flex items-center gap-4 text-xs">
            <span className={dark ? 'text-gray-500' : 'text-gray-400'}>
              OCR Confidence: <span className="font-semibold text-indigo-500">{Math.round((result.ocr_confidence || 0) * 100)}%</span>
            </span>
          </div>
        </div>
      )}

      {/* Generated Offer Data */}
      {offerData && (
        <div className={`rounded-xl p-6 border ${cardBg} space-y-4`}>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold flex items-center gap-2"><Sparkles className="w-5 h-5 text-indigo-500" /> Detected Offer</h3>
            <div className="flex gap-2">
              {offerData.announcement_text && (
                <button onClick={handlePlaySpeech} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-purple-500/10 text-purple-500 text-sm hover:bg-purple-500/20 transition">
                  <Volume2 className="w-4 h-4" /> Play Audio
                </button>
              )}
              <button onClick={handleSaveOffer} disabled={saving}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-medium disabled:opacity-50">
                <Save className="w-4 h-4" /> {saving ? 'Saving...' : 'Save as Offer'}
              </button>
            </div>
          </div>

          {/* Editable offer fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Product Name</label>
              <input className={inputCls} value={offerData.product_name || ''} onChange={e => setOfferData({...offerData, product_name: e.target.value})} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Brand</label>
              <input className={inputCls} value={offerData.brand || ''} onChange={e => setOfferData({...offerData, brand: e.target.value})} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Category</label>
              <input className={inputCls} value={offerData.category || ''} onChange={e => setOfferData({...offerData, category: e.target.value})} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Discount %</label>
              <input className={inputCls} type="number" value={offerData.discount_percent || 0} onChange={e => setOfferData({...offerData, discount_percent: parseFloat(e.target.value) || 0})} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">Start Date</label>
              <input className={inputCls} type="date" value={offerData.start_date || ''} onChange={e => setOfferData({...offerData, start_date: e.target.value})} />
            </div>
            <div>
              <label className="text-xs text-gray-500 mb-1 block">End Date</label>
              <input className={inputCls} type="date" value={offerData.end_date || ''} onChange={e => setOfferData({...offerData, end_date: e.target.value})} />
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-500 mb-1 block">Title</label>
            <input className={inputCls} value={offerData.title || ''} onChange={e => setOfferData({...offerData, title: e.target.value})} />
          </div>

          <div>
            <label className="text-xs text-gray-500 mb-1 block">Description</label>
            <input className={inputCls} value={offerData.description || ''} onChange={e => setOfferData({...offerData, description: e.target.value})} />
          </div>

          <div>
            <label className="text-xs text-gray-500 mb-1 block">Announcement Text (for in-store speakers)</label>
            <textarea className={inputCls} rows="3" value={offerData.announcement_text || ''} onChange={e => setOfferData({...offerData, announcement_text: e.target.value})} />
          </div>

          <div className="flex items-center gap-3 text-xs pt-2 border-t border-gray-700/30">
            <span className={`px-2 py-1 rounded-full ${
              offerData.confidence === 'high' ? 'bg-green-500/10 text-green-500' :
              offerData.confidence === 'medium' ? 'bg-yellow-500/10 text-yellow-500' :
              'bg-red-500/10 text-red-500'
            }`}>
              Confidence: {offerData.confidence || 'low'}
            </span>
            {offerData.original_price && (
              <span className={dark ? 'text-gray-500' : 'text-gray-400'}>Original: ₹{offerData.original_price}</span>
            )}
            {offerData.offer_price && (
              <span className={dark ? 'text-gray-500' : 'text-gray-400'}>Offer: ₹{offerData.offer_price}</span>
            )}
          </div>
        </div>
      )}

      {/* No result message */}
      {result && !result.extracted_text && !result.error && (
        <div className={`rounded-xl p-6 border ${cardBg} text-center`}>
          <FileText className="w-10 h-10 mx-auto text-gray-500 mb-3" />
          <p className="text-gray-500">{result.message || 'No text detected in the image. Try a clearer image.'}</p>
        </div>
      )}
    </div>
  )
}
