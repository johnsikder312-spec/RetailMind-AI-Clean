import { useState, useEffect } from 'react'
import { useTheme } from '../context/ThemeContext'
import { Settings as SettingsIcon, Sun, Moon, Activity } from 'lucide-react'
import api from '../services/api'

export default function Settings() {
  const { dark, toggleTheme } = useTheme()
  const [logs, setLogs] = useState([])

  useEffect(() => { fetchLogs() }, [])

  const fetchLogs = async () => {
    try {
      const res = await api.get('/api/auth/logs?per_page=30')
      setLogs(res.data.logs || [])
    } catch (err) {}
  }

  const cardBg = dark ? 'bg-gray-800/60 border-gray-700/50' : 'bg-white border-gray-200'

  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2"><SettingsIcon className="w-6 h-6 text-indigo-500" /> Settings</h1>
        <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>Manage your preferences</p>
      </div>

      {/* Theme */}
      <div className={`rounded-xl p-6 border ${cardBg}`}>
        <h3 className="font-semibold mb-4">Appearance</h3>
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Theme</p>
            <p className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>Choose between light and dark mode</p>
          </div>
          <button onClick={toggleTheme}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition ${dark ? 'bg-gray-700 text-yellow-400 hover:bg-gray-600' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>
            {dark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
            {dark ? 'Light Mode' : 'Dark Mode'}
          </button>
        </div>
      </div>

      {/* Activity Logs */}
      <div className={`rounded-xl p-6 border ${cardBg}`}>
        <h3 className="font-semibold mb-4 flex items-center gap-2">
          <Activity className="w-5 h-5 text-indigo-500" /> Activity Logs
        </h3>
        {logs.length === 0 ? (
          <p className={`text-sm ${dark ? 'text-gray-500' : 'text-gray-400'}`}>No activity logs yet.</p>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {logs.map(log => (
              <div key={log.id} className={`flex items-center justify-between p-3 rounded-lg text-sm ${dark ? 'bg-gray-700/30' : 'bg-gray-50'}`}>
                <div>
                  <p className="font-medium text-xs">{log.action}</p>
                  <p className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>{log.details}</p>
                </div>
                <div className="text-right">
                  <p className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>{log.username}</p>
                  <p className={`text-xs ${dark ? 'text-gray-600' : 'text-gray-300'}`}>{new Date(log.timestamp).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
