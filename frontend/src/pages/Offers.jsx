import { useState, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'
import { Plus, Tag, Trash2, ToggleLeft, ToggleRight, Clock } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function Offers() {
  const { dark } = useTheme()
  const [offers, setOffers] = useState([])
  const [tab, setTab] = useState('active')
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState({ title: '', description: '', announcement_text: '', discount_percent: '', start_date: '', end_date: '', language: 'english' })

  useEffect(() => { fetchOffers() }, [tab])

  const fetchOffers = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/api/offers?status=${tab}`)
      setOffers(res.data.offers || [])
    } catch (err) { toast.error('Failed to load offers') }
    finally { setLoading(false) }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/offers', form)
      toast.success('Offer created')
      setShowModal(false)
      setForm({ title: '', description: '', announcement_text: '', discount_percent: '', start_date: '', end_date: '', language: 'english' })
      fetchOffers()
    } catch (err) { toast.error(err.response?.data?.error || 'Failed to create offer') }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this offer?')) return
    try { await api.delete(`/api/offers/${id}`); toast.success('Deleted'); fetchOffers() }
    catch (err) { toast.error('Failed to delete') }
  }

  const handleToggle = async (id) => {
    try { await api.post(`/api/offers/${id}/toggle`); fetchOffers() }
    catch (err) { toast.error('Failed to toggle') }
  }

  const cardBg = dark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200'
  const inputCls = `w-full px-3 py-2 rounded-lg border text-sm ${dark ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'}`

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Offers</h1>
          <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Manage promotional offers</p>
        </div>
        <button onClick={() => setShowModal(true)} className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-medium hover:shadow-lg transition">
          <Plus className="w-4 h-4" /> Create Offer
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        {['active', 'expired', 'all'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${tab === t ? 'bg-indigo-500 text-white' : dark ? 'bg-gray-800 text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'}`}>
            {t}
          </button>
        ))}
      </div>

      {/* Offers List */}
      {loading ? (
        <div className="flex items-center justify-center h-48"><div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500"></div></div>
      ) : offers.length === 0 ? (
        <div className={`text-center py-16 rounded-xl border ${cardBg}`}>
          <Tag className="w-12 h-12 mx-auto text-gray-500 mb-3" />
          <p className="text-gray-500">No {tab} offers found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {offers.map(offer => (
            <div key={offer.id} className={`rounded-xl p-5 border ${cardBg} hover:shadow-lg transition`}>
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-lg">{offer.title}</h3>
                  <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{offer.product_name || 'General Offer'}</p>
                </div>
                <span className="px-3 py-1 rounded-full text-sm font-bold bg-green-500/10 text-green-500">{offer.discount_percent}% OFF</span>
              </div>
              {offer.announcement_text && (
                <p className={`text-sm italic mb-3 line-clamp-2 ${dark ? 'text-gray-400' : 'text-gray-500'}`}>"{offer.announcement_text}"</p>
              )}
              <div className="flex items-center gap-3 text-xs">
                <span className={`flex items-center gap-1 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                  <Clock className="w-3.5 h-3.5" /> {offer.end_date ? new Date(offer.end_date).toLocaleDateString() : 'No end date'}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-xs ${offer.is_active ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                  {offer.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              <div className="flex gap-2 mt-3 pt-3 border-t border-gray-700/30">
                <button onClick={() => handleToggle(offer.id)} className={`p-1.5 rounded-lg text-sm ${dark ? 'hover:bg-gray-700' : 'hover:bg-gray-100'}`}>
                  {offer.is_active ? <ToggleRight className="w-5 h-5 text-green-500" /> : <ToggleLeft className="w-5 h-5 text-gray-500" />}
                </button>
                <button onClick={() => handleDelete(offer.id)} className="p-1.5 rounded-lg hover:bg-red-500/10 text-red-500"><Trash2 className="w-4 h-4" /></button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className={`w-full max-w-lg rounded-2xl p-6 border max-h-[90vh] overflow-y-auto ${dark ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <h2 className="text-xl font-bold mb-4">Create Offer</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <input className={inputCls} placeholder="Offer Title *" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required />
              <textarea className={inputCls} placeholder="Description" rows="2" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} />
              <textarea className={inputCls} placeholder="Announcement Text (for speakers)" rows="3" value={form.announcement_text} onChange={e => setForm({ ...form, announcement_text: e.target.value })} />
              <input className={inputCls} type="number" step="0.1" placeholder="Discount %" value={form.discount_percent} onChange={e => setForm({ ...form, discount_percent: e.target.value })} />
              <div className="grid grid-cols-2 gap-3">
                <div><label className="text-xs text-gray-500">Start Date</label><input className={inputCls} type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} /></div>
                <div><label className="text-xs text-gray-500">End Date</label><input className={inputCls} type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} /></div>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className={`flex-1 py-2.5 rounded-xl border ${dark ? 'border-gray-600' : 'border-gray-300'}`}>Cancel</button>
                <button type="submit" className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-medium">Create</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
