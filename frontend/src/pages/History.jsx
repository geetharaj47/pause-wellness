import React, { useState, useEffect, useContext } from 'react'
import axios from 'axios'
import { AuthContext } from '../App'
import { Trash2, Calendar, Smile, AlertTriangle, Eye, EyeOff } from 'lucide-react'

const History = () => {
  const { token } = useContext(AuthContext)
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [deleteConfirmId, setDeleteConfirmId] = useState(null)
  const [expandedId, setExpandedId] = useState(null)

  const fetchEntries = async () => {
    setLoading(true)
    try {
      // Hitting the FastAPI backend (real endpoint)
      const response = await axios.get('http://localhost:8000/api/journal', {
        headers: { Authorization: `Bearer ${token}` }
      })
      setEntries(response.data)
    } catch (err) {
      console.warn('Backend fetch failed, reading from local mock storage.')
      // Fallback local storage
      const mockData = JSON.parse(localStorage.getItem('mock_checkins') || '[]')
      setEntries(mockData)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEntries()
  }, [])

  const handleDelete = async (indexOrId) => {
    try {
      // Try backend deletion
      await axios.delete(`http://localhost:8000/api/journal/${indexOrId}`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      fetchEntries()
    } catch (err) {
      console.warn('Backend deletion failed, removing from local mock storage.')
      
      // Local storage fallback (remove entry at index)
      const mockData = JSON.parse(localStorage.getItem('mock_checkins') || '[]')
      mockData.splice(indexOrId, 1)
      localStorage.setItem('mock_checkins', JSON.stringify(mockData))
      setEntries(mockData)
    } finally {
      setDeleteConfirmId(null)
    }
  }

  const getMoodEmoji = (score) => {
    switch (score) {
      case 1: return { emoji: '😢', style: 'bg-rose-100 text-rose-800 border-rose-200' }
      case 2: return { emoji: '🙁', style: 'bg-amber-100 text-amber-800 border-amber-250' }
      case 4: return { emoji: '🙂', style: 'bg-emerald-50 text-emerald-800 border-emerald-200' }
      case 5: return { emoji: '😊', style: 'bg-emerald-100 text-emerald-850 border-emerald-300' }
      default: return { emoji: '😐', style: 'bg-slate-100 text-slate-800 border-slate-200' }
    }
  }

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-wellness-100 pb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-800">Reflection History</h1>
          <p className="text-sm text-slate-500 mt-1">Review your past daily check-ins and personal journals.</p>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-500 text-xs">Loading reflection history...</div>
      ) : entries.length === 0 ? (
        <div className="text-center py-16 bg-white border border-dashed border-slate-300 rounded-2xl p-6">
          <Calendar size={48} className="text-slate-400 mx-auto" />
          <h3 className="mt-4 text-base font-bold text-slate-700">No entries recorded yet</h3>
          <p className="text-xs text-slate-500 mt-1">Complete a daily check-in to start mapping your path.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {entries.map((entry, index) => {
            const moodMeta = getMoodEmoji(entry.mood)
            const isExpanded = expandedId === index
            const isConfirming = deleteConfirmId === index
            
            return (
              <div key={index} className="bg-white rounded-xl border border-wellness-100 shadow-sm overflow-hidden transition-all duration-200">
                {/* Entry Header */}
                <div className="p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-50">
                  <div className="flex items-center space-x-3">
                    {/* Mood bubble */}
                    <div className={`w-10 h-10 rounded-full border flex items-center justify-center text-xl shadow-inner ${moodMeta.style}`}>
                      {moodMeta.emoji}
                    </div>
                    <div>
                      <p className="text-xs font-bold text-slate-850">
                        {new Date(entry.created_at).toLocaleDateString('en-US', {
                          weekday: 'long',
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                      <p className="text-[10px] text-slate-400 font-semibold mt-0.5">
                        Logged at {new Date(entry.created_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>

                  {/* Rating Tags */}
                  <div className="flex flex-wrap gap-1.5 items-center">
                    {entry.sleep && (
                      <span className="px-2 py-0.5 bg-slate-100 text-[10px] text-slate-650 rounded border border-slate-200 font-semibold">
                        Sleep: {entry.sleep}/5
                      </span>
                    )}
                    {entry.academic_work && <span className="px-2 py-0.5 bg-amber-50 text-[10px] text-amber-700 rounded border border-amber-200 font-semibold">Academic</span>}
                    {entry.relationships && <span className="px-2 py-0.5 bg-indigo-50 text-[10px] text-indigo-700 rounded border border-indigo-200 font-semibold">Relationships</span>}
                    {entry.social_life && <span className="px-2 py-0.5 bg-emerald-50 text-[10px] text-emerald-700 rounded border border-emerald-250 font-semibold">Social</span>}
                    {entry.health && <span className="px-2 py-0.5 bg-rose-50 text-[10px] text-rose-700 rounded border border-rose-200 font-semibold">Health</span>}
                  </div>
                </div>

                {/* Entry Text Content */}
                <div className="p-5 bg-slate-50/50">
                  <div className="text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">
                    {isExpanded ? entry.journal_text : `${entry.journal_text.substring(0, 160)}${entry.journal_text.length > 160 ? '...' : ''}`}
                  </div>
                  
                  {/* Expand/Read control */}
                  {entry.journal_text.length > 160 && (
                    <button
                      onClick={() => setExpandedId(isExpanded ? null : index)}
                      className="mt-3 flex items-center space-x-1.5 text-[10px] font-bold text-wellness-600 hover:text-wellness-850"
                    >
                      {isExpanded ? (
                        <>
                          <EyeOff size={12} />
                          <span>Show Less</span>
                        </>
                      ) : (
                        <>
                          <Eye size={12} />
                          <span>Read Full Entry</span>
                        </>
                      )}
                    </button>
                  )}
                </div>

                {/* Action Footer */}
                <div className="px-5 py-3 border-t border-slate-50 flex justify-between items-center text-xs bg-white">
                  <div>
                    {isConfirming ? (
                      <div className="flex items-center space-x-2 text-[10px] text-rose-600 font-bold bg-rose-50 p-1.5 px-3 rounded-lg border border-rose-205">
                        <AlertTriangle size={14} />
                        <span>Confirm Deletion? This cannot be undone.</span>
                        <button onClick={() => handleDelete(index)} className="underline hover:text-rose-800 ml-2">Delete</button>
                        <button onClick={() => setDeleteConfirmId(null)} className="underline text-slate-500 hover:text-slate-700 ml-1">Cancel</button>
                      </div>
                    ) : (
                      <button
                        onClick={() => setDeleteConfirmId(index)}
                        className="flex items-center space-x-1.5 text-[10px] font-bold text-slate-400 hover:text-rose-600 transition"
                      >
                        <Trash2 size={12} />
                        <span>Delete Entry</span>
                      </button>
                    )}
                  </div>
                  <span className="text-[10px] text-slate-400 font-semibold">Local Copy</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export default History
