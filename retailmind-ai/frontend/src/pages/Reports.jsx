import { useState } from 'react'
import { useTheme } from '../context/ThemeContext'
import { FileText, Download, Calendar, Sparkles } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

export default function Reports() {
  const { dark } = useTheme()
  const [period, setPeriod] = useState('daily')
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchReport = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/api/reports/${period}`)
      setReport(res.data)
    } catch (err) { toast.error('Failed to generate report') }
    finally { setLoading(false) }
  }

  const handleExport = async (format) => {
    try {
      const res = await api.get(`/api/reports/${period}/export/${format}`, { responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `retailmind_${period}_report.${format === 'excel' ? 'xlsx' : 'pdf'}`
      link.click()
      toast.success('Report downloaded!')
    } catch (err) { toast.error('Export failed') }
  }

  const cardBg = dark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200'

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><FileText className="w-6 h-6 text-indigo-500" /> Reports</h1>
        <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Generate AI-powered business reports</p>
      </div>

      {/* Controls */}
      <div className={`rounded-xl p-6 border ${cardBg}`}>
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex gap-2">
            {['daily', 'weekly', 'monthly'].map(p => (
              <button key={p} onClick={() => setPeriod(p)}
                className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition ${period === p ? 'bg-indigo-500 text-white' : dark ? 'bg-gray-700 text-gray-400' : 'bg-gray-100 text-gray-600'}`}>
                {p}
              </button>
            ))}
          </div>
          <button onClick={fetchReport} disabled={loading}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-sm font-medium hover:shadow-lg transition disabled:opacity-50">
            {loading ? <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Calendar className="w-4 h-4" />}
            Generate Report
          </button>
        </div>
      </div>

      {/* Report Content */}
      {report && (
        <div className={`rounded-xl p-6 border ${cardBg} space-y-6`}>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-bold">{period.charAt(0).toUpperCase() + period.slice(1)} Report</h3>
            <div className="flex gap-2">
              <button onClick={() => handleExport('pdf')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-red-500/10 text-red-500 text-sm hover:bg-red-500/20 transition">
                <Download className="w-4 h-4" /> PDF
              </button>
              <button onClick={() => handleExport('excel')} className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-green-500/10 text-green-500 text-sm hover:bg-green-500/20 transition">
                <Download className="w-4 h-4" /> Excel
              </button>
            </div>
          </div>

          <p className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            Period: {report.start_date} to {report.end_date}
          </p>

          {/* AI Summary */}
          {report.ai_summary && (
            <div className={`p-4 rounded-xl ${dark ? 'bg-indigo-500/5 border border-indigo-500/20' : 'bg-indigo-50 border border-indigo-100'}`}>
              <h4 className="text-sm font-semibold flex items-center gap-1.5 mb-2"><Sparkles className="w-4 h-4 text-indigo-500" /> AI Summary</h4>
              <p className="text-sm">{report.ai_summary}</p>
            </div>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`p-4 rounded-xl text-center ${dark ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <p className="text-2xl font-bold text-blue-500">{report.new_products_count}</p>
              <p className="text-xs text-gray-500">New Products</p>
            </div>
            <div className={`p-4 rounded-xl text-center ${dark ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <p className="text-2xl font-bold text-green-500">{report.new_offers_count}</p>
              <p className="text-xs text-gray-500">New Offers</p>
            </div>
            <div className={`p-4 rounded-xl text-center ${dark ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <p className="text-2xl font-bold text-indigo-500">{report.active_offers_count}</p>
              <p className="text-xs text-gray-500">Active Offers</p>
            </div>
            <div className={`p-4 rounded-xl text-center ${dark ? 'bg-gray-700/50' : 'bg-gray-50'}`}>
              <p className="text-2xl font-bold text-red-500">{report.low_stock_count}</p>
              <p className="text-xs text-gray-500">Low Stock</p>
            </div>
          </div>

          {/* Activity */}
          {report.activity_logs?.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2">Recent Activity ({report.activity_count} events)</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {report.activity_logs.slice(0, 10).map(log => (
                  <div key={log.id} className={`flex justify-between items-center p-2 rounded-lg text-xs ${dark ? 'bg-gray-700/30' : 'bg-gray-50'}`}>
                    <span>{log.action}</span>
                    <span className={dark ? 'text-gray-500' : 'text-gray-400'}>{new Date(log.timestamp).toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
