import React, { useState, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { AuthContext } from '../App'
import { Sparkles, Save, ShieldAlert, Heart, PhoneCall } from 'lucide-react'

const Journal = () => {
  const { token } = useContext(AuthContext)
  const navigate = useNavigate()

  // Form State
  const [mood, setMood] = useState(3) // default: 3 (Neutral)
  const [sleep, setSleep] = useState(3) // default: 3 (Average)
  const [academicWork, setAcademicWork] = useState(false)
  const [relationships, setRelationships] = useState(false)
  const [socialLife, setSocialLife] = useState(false)
  const [health, setHealth] = useState(false)
  const [journalText, setJournalText] = useState('')

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [safetyTriggered, setSafetyTriggered] = useState(false)

  // Client-side Safety Scanner (Regex matching critical phrases)
  const scanSafety = (text) => {
    const riskKeywords = /\b(suicide|self-harm|kill myself|want to die|end my life|ending my life|hurt myself|cut myself)\b/i
    return riskKeywords.test(text)
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    // Run Safety Scanner
    if (scanSafety(journalText)) {
      setSafetyTriggered(true)
      // Save a safety event locally/backend audit
      try {
        await axios.post('http://localhost:8000/api/safety/event', 
          { triggered_keyword: 'Crisis Keyword Match', action_taken: 'Helpline Modal Displayed' },
          { headers: { Authorization: `Bearer ${token}` } }
        )
      } catch (e) {
        console.warn('Safety logging skipped or backend not running.')
      }
      return
    }

    setLoading(true)

    // Compile check-in data
    const entryData = {
      mood,
      sleep,
      academic_work: academicWork,
      relationships,
      social_life: socialLife,
      health,
      journal_text: journalText,
      created_at: new Date().toISOString()
    }

    try {
      // API call to backend (will be implemented in Phase 2)
      // For Phase 1 validation, we attempt the API request, and fallback to LocalStorage
      await axios.post('http://localhost:8000/api/journal', entryData, {
        headers: { Authorization: `Bearer ${token}` }
      })
      
      setSuccess(true)
      // Redirect to history after short delay
      setTimeout(() => navigate('/history'), 1500)
    } catch (err) {
      console.warn('Backend journal submission failed, saving to local mock storage:', err.message)
      
      // Fallback: Save to LocalStorage so the UI works without the backend in early demos
      const existing = JSON.parse(localStorage.getItem('mock_checkins') || '[]')
      existing.unshift(entryData)
      localStorage.setItem('mock_checkins', JSON.stringify(existing))

      setSuccess(true)
      setTimeout(() => navigate('/history'), 1500)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Safety Intercept Modal */}
      {safetyTriggered && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex justify-center items-center p-4 z-50">
          <div className="bg-white max-w-lg w-full rounded-2xl p-6 md:p-8 shadow-2xl border-t-8 border-rose-600 space-y-4 animate-in fade-in zoom-in duration-200">
            <div className="flex items-center space-x-3 text-rose-600">
              <ShieldAlert size={36} />
              <h2 className="text-xl font-extrabold">Support is Available</h2>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed">
              You mentioned feeling in distress. Please know that you are not alone, and there are people who want to listen and help.
            </p>
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
              <div className="flex items-start space-x-3">
                <PhoneCall className="text-wellness-600 mt-0.5" size={18} />
                <div>
                  <h4 className="text-sm font-bold text-slate-800">National Suicide & Crisis Lifeline</h4>
                  <p className="text-xs text-slate-500">Free, confidential support available 24/7.</p>
                  <p className="text-sm font-bold text-wellness-700 mt-1">Call or Text: 988</p>
                </div>
              </div>
            </div>
            <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-slate-100">
              <button
                onClick={() => setSafetyTriggered(false)}
                className="flex-1 px-4 py-2 border border-slate-350 rounded-lg text-sm text-slate-600 font-semibold hover:bg-slate-50 transition"
              >
                Close Window
              </button>
              <Link
                to="/support"
                className="flex-1 text-center bg-wellness-600 hover:bg-wellness-700 text-white px-4 py-2 rounded-lg text-sm font-bold transition shadow-sm"
              >
                Explore Coping Tools
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Title */}
      <div className="border-b border-wellness-100 pb-4">
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-800">Daily Journal & Check-in</h1>
        <p className="text-sm text-slate-500 mt-1">Reflect on your day. All text is scanned locally and kept private.</p>
      </div>

      {success && (
        <div className="bg-wellness-100 border border-wellness-350 p-4 text-sm text-wellness-850 rounded-xl flex items-center space-x-2">
          <Heart className="text-wellness-600 fill-wellness-600" size={18} />
          <span>Your daily reflection has been securely saved. Redirecting to history...</span>
        </div>
      )}

      <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Mood & Ratings Checkin */}
        <div className="lg:col-span-1 bg-white p-6 rounded-xl border border-wellness-100 shadow-sm space-y-6">
          <div>
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide border-b border-slate-100 pb-2">1. Mood Check-in</h3>
            <div className="mt-4 flex justify-between gap-1">
              {[
                { val: 1, label: '😢', name: 'Very Difficult' },
                { val: 2, label: '🙁', name: 'Difficult' },
                { val: 3, label: '😐', name: 'Neutral' },
                { val: 4, label: '🙂', name: 'Good' },
                { val: 5, label: '😊', name: 'Very Good' },
              ].map((m) => (
                <button
                  key={m.val}
                  type="button"
                  onClick={() => setMood(m.val)}
                  className={`flex-1 flex flex-col items-center p-2 rounded-lg border text-xl transition-all ${
                    mood === m.val
                      ? 'bg-wellness-100 border-wellness-400 scale-105 shadow-sm'
                      : 'border-slate-200 hover:bg-slate-50 text-slate-400'
                  }`}
                  title={m.name}
                >
                  <span>{m.label}</span>
                  <span className="text-[9px] text-slate-500 mt-1 text-center font-medium leading-none">{m.name.split(' ')[0]}</span>
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide border-b border-slate-100 pb-2">2. Sleep Quality</h3>
            <div className="mt-3">
              <input
                type="range"
                min="1"
                max="5"
                value={sleep}
                onChange={(e) => setSleep(parseInt(e.target.value))}
                className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-wellness-600"
              />
              <div className="flex justify-between text-[10px] text-slate-450 mt-1 font-semibold">
                <span>Poor Sleep</span>
                <span>Average</span>
                <span>Restful Sleep</span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide border-b border-slate-100 pb-2">3. Life Factors</h3>
            <p className="text-xs text-slate-450 mt-1">Select factors active in your day:</p>
            <div className="mt-3 space-y-2.5">
              {[
                { id: 'work', label: 'Academic & Work pressure', val: academicWork, setVal: setAcademicWork },
                { id: 'rel', label: 'Relationship factors', val: relationships, setVal: setRelationships },
                { id: 'social', label: 'Social interactions', val: socialLife, setVal: setSocialLife },
                { id: 'health', label: 'Health & physical wellness', val: health, setVal: setHealth },
              ].map((f) => (
                <label key={f.id} className="flex items-center space-x-3 text-xs text-slate-700 font-semibold cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={f.val}
                    onChange={(e) => f.setVal(e.target.checked)}
                    className="h-4 w-4 rounded border-slate-300 text-wellness-600 focus:ring-wellness-500"
                  />
                  <span>{f.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Journal Entry Textarea */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-wellness-100 shadow-sm flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide">4. Write Freely</h3>
              <span className="text-xs text-slate-400">{journalText.length} characters</span>
            </div>
            <textarea
              required
              rows="12"
              value={journalText}
              onChange={(e) => setJournalText(e.target.value)}
              className="w-full p-4 border border-slate-350 rounded-xl text-sm focus:outline-none focus:ring-1 focus:ring-wellness-500 focus:border-wellness-500 resize-none leading-relaxed"
              placeholder="How are you doing today? What is on your mind? Feel free to write about your workload, your thoughts, or your sleep..."
            />
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-between mt-6 gap-4">
            <div className="flex items-center space-x-2 text-xs text-slate-450">
              <Sparkles size={16} className="text-wellness-500" />
              <span>PII scrubber will redact names and contacts automatically.</span>
            </div>
            <button
              type="submit"
              disabled={loading || journalText.trim().length === 0}
              className="w-full sm:w-auto bg-wellness-600 hover:bg-wellness-700 disabled:bg-wellness-400 text-white font-bold px-6 py-2.5 rounded-lg text-sm shadow-sm transition flex items-center justify-center space-x-2"
            >
              <Save size={16} />
              <span>{loading ? 'Saving...' : 'Save Entry'}
              </span>
            </button>
          </div>
        </div>

      </form>
    </div>
  )
}

export default Journal
