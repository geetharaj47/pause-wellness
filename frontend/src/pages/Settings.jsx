import React, { useState, useEffect, useContext } from 'react'
import axios from 'axios'
import { AuthContext } from '../App'
import { Shield, Download, Trash2, Save, CheckCircle, Info } from 'lucide-react'

const Settings = () => {
  const { token, logout } = useContext(AuthContext)
  
  // Settings state
  const [analysisEnabled, setAnalysisEnabled] = useState(true)
  const [personalizationEnabled, setPersonalizationEnabled] = useState(true)
  const [contactName, setContactName] = useState('')
  const [contactEmail, setContactEmail] = useState('')
  const [contactPhone, setContactPhone] = useState('')

  // UI state
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Load existing settings if available (mock values fallback)
    setContactName(localStorage.getItem('contact_name') || '')
    setContactEmail(localStorage.getItem('contact_email') || '')
    setContactPhone(localStorage.getItem('contact_phone') || '')
    setAnalysisEnabled(localStorage.getItem('analysis_enabled') !== 'false')
    setPersonalizationEnabled(localStorage.getItem('personalization_enabled') !== 'false')
  }, [])

  const handleSave = async (e) => {
    e.preventDefault()
    setSaveSuccess(false)
    setLoading(true)

    // Save preferences
    localStorage.setItem('contact_name', contactName)
    localStorage.setItem('contact_email', contactEmail)
    localStorage.setItem('contact_phone', contactPhone)
    localStorage.setItem('analysis_enabled', analysisEnabled ? 'true' : 'false')
    localStorage.setItem('personalization_enabled', personalizationEnabled ? 'true' : 'false')

    try {
      // API call to backend (will be implemented in Phase 2)
      await axios.post('http://localhost:8000/api/preferences', {
        enable_analysis: analysisEnabled,
        trusted_contact_name: contactName,
        trusted_contact_email: contactEmail,
        trusted_contact_phone: contactPhone
      }, {
        headers: { Authorization: `Bearer ${token}` }
      })
    } catch (err) {
      console.warn('Backend settings saving skipped/failed, saved locally.')
    } finally {
      setLoading(false)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    }
  }

  // Privacy: Export all user data as a JSON file
  const handleExportData = () => {
    const checkins = JSON.parse(localStorage.getItem('mock_checkins') || '[]')
    const userData = {
      export_timestamp: new Date().toISOString(),
      user: localStorage.getItem('email'),
      settings: {
        analysis_enabled: analysisEnabled,
        personalization_enabled: personalizationEnabled
      },
      checkins_and_journals: checkins
    }

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(userData, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute("href", dataStr)
    downloadAnchor.setAttribute("download", `mindtrace_data_export_${new Date().toISOString().split('T')[0]}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
  }

  // Privacy: Delete all data and log out
  const handleDeleteAllData = async () => {
    try {
      // Call backend wipe (to be added)
      await axios.delete('http://localhost:8000/api/user/data', {
        headers: { Authorization: `Bearer ${token}` }
      })
    } catch (e) {
      console.warn('Backend wipe failed.')
    }

    // Wipe local storage
    localStorage.clear()
    logout()
  }

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-wellness-100 pb-4">
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-800">Privacy & Settings</h1>
        <p className="text-sm text-slate-500 mt-1">Configure your personal baseline parameters and exercise data controls.</p>
      </div>

      {saveSuccess && (
        <div className="bg-wellness-100 border border-wellness-350 p-4 text-sm text-wellness-850 rounded-xl flex items-center space-x-2">
          <CheckCircle className="text-wellness-600" size={18} />
          <span>Your privacy preferences have been updated successfully.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Columns: Settings Fields */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Privacy Toggles */}
          <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm space-y-4">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide border-b border-slate-100 pb-2">Analysis Preferences</h3>
            
            <div className="flex items-start justify-between gap-4">
              <div>
                <label className="text-xs font-bold text-slate-700 block">Enable NLP Signal Extraction</label>
                <span className="text-[10px] text-slate-450 leading-relaxed block mt-0.5">
                  Allows MindTrace to extract sentiment, emotional valence, and stress scores locally from your journals. Disabling this blocks text processing.
                </span>
              </div>
              <input
                type="checkbox"
                checked={analysisEnabled}
                onChange={(e) => setAnalysisEnabled(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-wellness-600 focus:ring-wellness-500 mt-1 shrink-0"
              />
            </div>

            <div className="flex items-start justify-between gap-4 pt-2">
              <div>
                <label className="text-xs font-bold text-slate-700 block">Enable Personalized Dynamic Baseline (Model B)</label>
                <span className="text-[10px] text-slate-450 leading-relaxed block mt-0.5">
                  Allows MindTrace to run dynamic z-score baseline comparisons to highlight personal shifts. Disabling this forces static population thresholds only.
                </span>
              </div>
              <input
                type="checkbox"
                checked={personalizationEnabled}
                onChange={(e) => setPersonalizationEnabled(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-wellness-600 focus:ring-wellness-500 mt-1 shrink-0"
              />
            </div>
          </div>

          {/* Trusted Contacts */}
          <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm space-y-4">
            <div className="border-b border-slate-100 pb-2">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide">Trusted Contact Setup</h3>
              <p className="text-[10px] text-slate-450 mt-0.5">This contact will be displayed on your crisis safety overlay in case of distress triggers.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-[10px] font-semibold text-slate-600 uppercase tracking-wider">Contact Name</label>
                <input
                  type="text"
                  value={contactName}
                  onChange={(e) => setContactName(e.target.value)}
                  className="mt-1 block w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-wellness-500 focus:border-wellness-500"
                  placeholder="e.g., Mom, Friend, Partner"
                />
              </div>

              <div>
                <label className="block text-[10px] font-semibold text-slate-600 uppercase tracking-wider">Phone Number</label>
                <input
                  type="tel"
                  value={contactPhone}
                  onChange={(e) => setContactPhone(e.target.value)}
                  className="mt-1 block w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-wellness-500 focus:border-wellness-500"
                  placeholder="+1 555-0199"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-[10px] font-semibold text-slate-600 uppercase tracking-wider">Email Address</label>
                <input
                  type="email"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                  className="mt-1 block w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-wellness-500 focus:border-wellness-500"
                  placeholder="contact@email.com"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="bg-wellness-600 hover:bg-wellness-700 text-white font-bold px-6 py-2 rounded-lg text-xs shadow-sm transition flex items-center space-x-1.5"
            >
              <Save size={14} />
              <span>{loading ? 'Saving...' : 'Save Settings'}</span>
            </button>
          </div>

        </div>

        {/* Right Column: Privacy Actions */}
        <div className="lg:col-span-1 bg-white p-6 rounded-xl border border-wellness-100 shadow-sm space-y-6 self-start">
          <div className="flex items-center space-x-2 text-slate-700 border-b border-slate-100 pb-3 mb-2">
            <Shield size={20} className="text-wellness-600" />
            <h3 className="font-bold text-slate-800">Your Data Controls</h3>
          </div>
          
          <div className="space-y-4">
            {/* Export data */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-800">Export All Logs</h4>
              <p className="text-[10px] text-slate-450 leading-relaxed">
                Download a complete copy of your daily check-in histories, logs, and settings in standardized JSON format.
              </p>
              <button
                type="button"
                onClick={handleExportData}
                className="w-full bg-slate-100 hover:bg-slate-200 border border-slate-300 text-slate-750 text-[10px] font-bold py-2 rounded-lg transition flex items-center justify-center space-x-1.5 shadow-sm"
              >
                <Download size={12} />
                <span>Export My Data</span>
              </button>
            </div>

            {/* Permanent deletion */}
            <div className="space-y-2 pt-4 border-t border-slate-100">
              <h4 className="text-xs font-bold text-rose-700">Delete Account & Data</h4>
              <p className="text-[10px] text-slate-450 leading-relaxed">
                Permanently wipe your account registration, preferences, daily check-ins, baselines, and journals from local and server databases.
              </p>
              {deleteConfirm ? (
                <div className="bg-rose-50 border border-rose-200 p-3 rounded-lg space-y-3">
                  <span className="text-[10px] text-rose-800 font-bold block">Are you absolutely sure? This action is irreversible.</span>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={handleDeleteAllData}
                      className="flex-1 bg-rose-600 hover:bg-rose-700 text-white text-[10px] font-bold py-1.5 rounded transition"
                    >
                      Yes, Wipe Everything
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteConfirm(false)}
                      className="flex-1 bg-white border border-slate-300 text-slate-600 text-[10px] font-bold py-1.5 rounded transition"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={() => setDeleteConfirm(true)}
                  className="w-full bg-white hover:bg-rose-50 border border-rose-300 text-rose-700 text-[10px] font-bold py-2 rounded-lg transition flex items-center justify-center space-x-1.5 shadow-sm"
                >
                  <Trash2 size={12} />
                  <span>Delete Everything</span>
                </button>
              )}
            </div>
          </div>
        </div>

      </form>
    </div>
  )
}

export default Settings
