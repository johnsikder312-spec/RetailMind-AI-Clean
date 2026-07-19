import { useState, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend } from 'chart.js'
import { Bar, Doughnut } from 'react-chartjs-2'
import { Package, Tag, AlertTriangle, Volume2, TrendingUp, Clock } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

export default function Dashboard() {
  const { dark } = useTheme()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const res = await api.get('/api/dashboard/stats')
      setData(res.data)
    } catch (err) {
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    )
  }

  const stats = data?.stats || {}
  const cardBg = dark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200'

  const statCards = [
    { label: 'Total Products', value: stats.total_products || 0, icon: Package, color: 'from-blue-500 to-cyan-500' },
    { label: 'Active Offers', value: stats.active_offers || 0, icon: Tag, color: 'from-green-500 to-emerald-500' },
    { label: 'Expired Offers', value: stats.expired_offers || 0, icon: Clock, color: 'from-orange-500 to-red-500' },
    { label: 'Low Stock', value: stats.low_stock_products || 0, icon: AlertTriangle, color: 'from-red-500 to-pink-500' },
    { label: 'Announcements Today', value: stats.announcements_today || 0, icon: Volume2, color: 'from-purple-500 to-indigo-500' },
  ]

  const barData = {
    labels: (data?.monthly_trends || []).map(t => t.month),
    datasets: [{
      label: 'Offers Created',
      data: (data?.monthly_trends || []).map(t => t.offers),
      backgroundColor: 'rgba(99, 102, 241, 0.6)',
      borderColor: 'rgba(99, 102, 241, 1)',
      borderWidth: 1,
      borderRadius: 8,
    }]
  }

  const doughnutData = {
    labels: (data?.category_distribution || []).map(c => c.name),
    datasets: [{
      data: (data?.category_distribution || []).map(c => c.count),
      backgroundColor: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#06b6d4', '#f43f5e', '#84cc16'],
      borderWidth: 0,
    }]
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Welcome back! Here's your store overview.</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((card, i) => (
          <div key={i} className={`rounded-xl p-5 border ${cardBg} backdrop-blur-sm`}>
            <div className="flex items-center justify-between mb-3">
              <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center`}>
                <card.icon className="w-5 h-5 text-white" />
              </div>
            </div>
            <p className="text-2xl font-bold">{card.value}</p>
            <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>{card.label}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className={`lg:col-span-2 rounded-xl p-6 border ${cardBg}`}>
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-500" />
            Monthly Offer Trends
          </h3>
          <Bar
            data={barData}
            options={{
              responsive: true,
              plugins: { legend: { display: false } },
              scales: {
                y: { beginAtZero: true, ticks: { color: dark ? '#9ca3af' : '#6b7280' } },
                x: { ticks: { color: dark ? '#9ca3af' : '#6b7280' } }
              }
            }}
          />
        </div>

        <div className={`rounded-xl p-6 border ${cardBg}`}>
          <h3 className="font-semibold mb-4">Category Distribution</h3>
          {(data?.category_distribution || []).length > 0 ? (
            <Doughnut data={doughnutData} options={{ plugins: { legend: { position: 'bottom', labels: { color: dark ? '#9ca3af' : '#6b7280' } } } }} />
          ) : (
            <div className="flex items-center justify-center h-48 text-gray-500">No data yet</div>
          )}
        </div>
      </div>

      {/* Low Stock & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className={`rounded-xl p-6 border ${cardBg}`}>
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-500" />
            Low Stock Alerts
          </h3>
          {(data?.low_stock_items || []).length > 0 ? (
            <div className="space-y-3">
              {data.low_stock_items.map(item => (
                <div key={item.id} className={`flex items-center justify-between p-3 rounded-lg ${dark ? 'bg-gray-700/30' : 'bg-gray-50'}`}>
                  <span className="font-medium text-sm">{item.name}</span>
                  <span className="text-sm text-red-500 font-semibold">{item.stock_quantity} units</span>
                </div>
              ))}
            </div>
          ) : (
            <p className={`text-sm ${dark ? 'text-gray-500' : 'text-gray-400'}`}>All products are well-stocked!</p>
          )}
        </div>

        <div className={`rounded-xl p-6 border ${cardBg}`}>
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-indigo-500" />
            Recent Activity
          </h3>
          {(data?.recent_activity || []).length > 0 ? (
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {data.recent_activity.map(log => (
                <div key={log.id} className={`p-3 rounded-lg text-sm ${dark ? 'bg-gray-700/30' : 'bg-gray-50'}`}>
                  <p className="font-medium">{log.action}</p>
                  <p className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>{log.details}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className={`text-sm ${dark ? 'text-gray-500' : 'text-gray-400'}`}>No recent activity</p>
          )}
        </div>
      </div>
    </div>
  )
}
