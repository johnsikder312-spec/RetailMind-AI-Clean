import { useState, useEffect, useCallback } from 'react'
import { useTheme } from '../context/ThemeContext'
import { Volume2, Play, Clock, Square, Megaphone, FileAudio, RefreshCw, Globe, Music, Download, Sliders, Loader2 } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function Announcements() {
  const { dark } = useTheme()
  const [announcements, setAnnouncements] = useState([])
  const [loading, setLoading] = useState(true)
  const [playingId, setPlayingId] = useState(null)
  const [musicTracks, setMusicTracks] = useState([])
  const [previewing, setPreviewing] = useState(false)

  // Per-announcement music settings
  const [musicSettings, setMusicSettings] = useState({})

  const fetchAnnouncements = useCallback(async () => {
    try {
      const res = await api.get('/api/tts/list')
      const list = res.data.announcements || []
      setAnnouncements(list)
      // Initialize music settings from saved data
      const settings = {}
      list.forEach(a => {
        settings[a.id] = {
          background_music: a.background_music || '',
          music_volume: a.music_volume ?? 15,
        }
      })
      setMusicSettings(settings)
    } catch (err) { toast.error('Failed to load announcements') }
    finally { setLoading(false) }
  }, [])

  const fetchMusicTracks = useCallback(async () => {
    try {
      const res = await api.get('/api/tts/music-tracks')
      setMusicTracks(res.data.tracks || [])
    } catch (err) { /* silent */ }
  }, [])

  useEffect(() => { fetchAnnouncements(); fetchMusicTracks() }, [fetchAnnouncements, fetchMusicTracks])

  useEffect(() => {
    const handleVisibility = () => { if (document.visibilityState === 'visible') fetchAnnouncements() }
    const handleFocus = () => fetchAnnouncements()
    document.addEventListener('visibilitychange', handleVisibility)
    window.addEventListener('focus', handleFocus)
    return () => {
      document.removeEventListener('visibilitychange', handleVisibility)
      window.removeEventListener('focus', handleFocus)
    }
  }, [fetchAnnouncements])

  const updateSetting = (id, key, value) => {
    setMusicSettings(prev => ({
      ...prev,
      [id]: { ...prev[id], [key]: value }
    }))
  }

  const handlePlay = async (id) => {
    setPlayingId(id)
    try {
      const res = await api.post(`/api/tts/announce/${id}`)
      if (res.data.audio_url) {
        const audio = new Audio(res.data.audio_url)
        audio.onended = () => setPlayingId(null)
        audio.onerror = () => { setPlayingId(null); toast.error('Audio playback failed') }
        await audio.play()
        toast.success('Playing announcement')
        fetchAnnouncements()
      } else {
        toast.error('No audio URL available')
        setPlayingId(null)
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Playback failed')
      setPlayingId(null)
    }
  }

  const handlePreview = async (announcement) => {
    if (!announcement.announcement_text) { toast.error('No text to preview'); return }
    const settings = musicSettings[announcement.id] || {}
    setPreviewing(announcement.id)
    try {
      const res = await api.post('/api/tts/preview', {
        text: announcement.announcement_text,
        language: announcement.language || 'english',
        background_music: settings.background_music || '',
        music_volume: settings.music_volume ?? 15,
      })
      if (res.data.audio_url) {
        const audio = new Audio(res.data.audio_url)
        audio.play()
        toast.success(res.data.message || 'Preview playing')
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'Preview failed')
    } finally { setPreviewing(null) }
  }

  const handleApplyMusic = async (id) => {
    const settings = musicSettings[id] || {}
    try {
      const res = await api.post(`/api/tts/mix/${id}`, {
        background_music: settings.background_music || '',
        music_volume: settings.music_volume ?? 15,
      })
      toast.success(res.data.message || 'Music applied and saved')
      fetchAnnouncements()
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to apply music')
    }
  }

  const handleDownload = async (id) => {
    try {
      const token = localStorage.getItem('token')
      const res = await fetch(`/api/tts/download/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!res.ok) { toast.error('Download failed'); return }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `announcement_${id}.mp3`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Download started')
    } catch (err) { toast.error('Download failed') }
  }

  const handleSchedule = async (id, interval) => {
    try {
      await api.post(`/api/tts/schedule/${id}`, { interval })
      toast.success(`Scheduled every ${interval} minutes`)
      fetchAnnouncements()
    } catch (err) { toast.error('Scheduling failed') }
  }

  const handleStop = async (id) => {
    try {
      await api.post(`/api/tts/stop/${id}`)
      toast.success('Announcement stopped')
      fetchAnnouncements()
    } catch (err) { toast.error('Failed to stop') }
  }

  const cardBg = dark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200'
  const mutedText = dark ? 'text-gray-400' : 'text-gray-500'
  const inputCls = `px-3 py-2 rounded-lg border text-sm ${dark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2"><Volume2 className="w-6 h-6 text-indigo-500" /> Announcements</h1>
          <p className={`text-sm ${mutedText}`}>Manage voice announcements with optional background music</p>
        </div>
        <button onClick={() => { setLoading(true); fetchAnnouncements() }}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm transition ${dark ? 'bg-gray-700 text-gray-300 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'}`}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {announcements.length === 0 ? (
        <div className={`text-center py-16 rounded-xl border ${cardBg}`}>
          <Megaphone className="w-12 h-12 mx-auto text-gray-500 mb-3" />
          <p className={`font-medium mb-1 ${dark ? 'text-gray-300' : 'text-gray-700'}`}>No announcements yet</p>
          <p className={`text-sm ${mutedText}`}>Generate and save an offer from the <strong>AI Generator</strong> page — an announcement with audio will be created automatically.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {announcements.map(a => {
            const settings = musicSettings[a.id] || {}
            return (
              <div key={a.id} className={`rounded-xl p-5 border ${cardBg} transition hover:shadow-md`}>
                {/* Header */}
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Megaphone className="w-4 h-4 text-indigo-500 flex-shrink-0" />
                      <h3 className="font-semibold truncate">{a.offer_title || 'Announcement'}</h3>
                    </div>
                    {a.announcement_text && (
                      <p className={`text-sm mt-2 leading-relaxed ${dark ? 'text-gray-300' : 'text-gray-600'}`}>
                        {a.announcement_text}
                      </p>
                    )}
                    <div className="flex items-center gap-3 mt-3 text-xs flex-wrap">
                      <span className={`px-2 py-0.5 rounded-full font-medium ${a.is_active ? 'bg-green-500/10 text-green-500' : 'bg-gray-500/10 text-gray-500'}`}>
                        {a.is_active ? 'Active' : 'Stopped'}
                      </span>
                      <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full ${a.audio_url ? 'bg-blue-500/10 text-blue-500' : 'bg-yellow-500/10 text-yellow-500'}`}>
                        <FileAudio className="w-3 h-3" />{a.audio_url ? 'Audio ready' : 'No audio'}
                      </span>
                      {a.language && (
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-500">
                          <Globe className="w-3 h-3" />{a.language.charAt(0).toUpperCase() + a.language.slice(1)}
                        </span>
                      )}
                      {a.background_music && (
                        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-500">
                          <Music className="w-3 h-3" />{musicTracks.find(t => t.id === a.background_music)?.name || a.background_music}
                        </span>
                      )}
                      <span className={mutedText}><Clock className="w-3 h-3 inline mr-1" />Every {a.scheduled_interval} min</span>
                      {a.last_played && <span className={mutedText}>Last: {new Date(a.last_played).toLocaleString()}</span>}
                    </div>
                  </div>
                  {/* Play & Stop */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button onClick={() => handlePlay(a.id)} disabled={playingId === a.id || !a.audio_url}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-indigo-500/10 text-indigo-500 hover:bg-indigo-500/20 transition disabled:opacity-40" title="Announce Now">
                      {playingId === a.id ? <div className="w-4 h-4 border-2 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" /> : <Play className="w-4 h-4" />}
                      <span className="text-sm font-medium">Play</span>
                    </button>
                    <button onClick={() => handleDownload(a.id)} disabled={!a.audio_url}
                      className="p-2 rounded-lg bg-green-500/10 text-green-500 hover:bg-green-500/20 transition disabled:opacity-40" title="Download MP3">
                      <Download className="w-4 h-4" />
                    </button>
                    {a.is_active && (
                      <button onClick={() => handleStop(a.id)} className="p-2 rounded-lg bg-red-500/10 text-red-500 hover:bg-red-500/20 transition" title="Stop">
                        <Square className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Background Music Controls */}
                <div className={`mt-4 pt-4 border-t ${dark ? 'border-gray-700/30' : 'border-gray-200'}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <Music className="w-4 h-4 text-purple-500" />
                    <span className="text-sm font-medium">Background Music</span>
                  </div>
                  <div className="flex items-center gap-3 flex-wrap">
                    {/* Music dropdown */}
                    <select
                      value={settings.background_music || ''}
                      onChange={e => updateSetting(a.id, 'background_music', e.target.value)}
                      className={inputCls + ' flex-1 min-w-[180px]'}>
                      <option value="">No Music (Voice Only)</option>
                      {musicTracks.map(t => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                      ))}
                    </select>

                    {/* Volume slider */}
                    <div className="flex items-center gap-2 min-w-[160px]">
                      <Sliders className="w-3.5 h-3.5 text-gray-500" />
                      <input
                        type="range" min="0" max="30" step="1"
                        value={settings.music_volume ?? 15}
                        onChange={e => updateSetting(a.id, 'music_volume', parseInt(e.target.value))}
                        className="flex-1 h-1.5 rounded-full accent-purple-500"
                        disabled={!settings.background_music}
                      />
                      <span className={`text-xs font-mono w-8 text-right ${mutedText}`}>{settings.music_volume ?? 15}%</span>
                    </div>

                    {/* Preview */}
                    <button onClick={() => handlePreview(a)} disabled={previewing === a.id}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-purple-500/10 text-purple-500 hover:bg-purple-500/20 transition text-sm disabled:opacity-50">
                      {previewing === a.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                      Preview
                    </button>

                    {/* Apply & Save */}
                    <button onClick={() => handleApplyMusic(a.id)}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-medium hover:shadow-lg transition">
                      <Music className="w-4 h-4" /> Apply
                    </button>
                  </div>
                </div>

                {/* Schedule */}
                {a.is_active && (
                  <div className={`flex gap-2 mt-3 pt-3 border-t ${dark ? 'border-gray-700/30' : 'border-gray-200'}`}>
                    <span className={`text-xs ${mutedText} mr-2 self-center`}>Schedule:</span>
                    {[15, 30, 60].map(min => (
                      <button key={min} onClick={() => handleSchedule(a.id, min)}
                        className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                          a.scheduled_interval === min
                            ? 'bg-indigo-500 text-white'
                            : dark ? 'bg-gray-700 text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'
                        }`}>
                        <Clock className="w-3 h-3" /> {min} min
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
