import React, { useState, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { AuthContext } from '../App'
import { ShieldCheck, Eye, Database, FileText } from 'lucide-react'

const Onboarding = () => {
  const { token, updateConsent, logout } = useContext(AuthContext)
  const [agreed, setAgreed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleAgree = async () => {
    if (!agreed) return
    
    setLoading(true)
    setError('')

    try {
      await axios.post('http://localhost:8000/api/auth/consent', 
        { consent_given: true, consent_version: '1.0' },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      
      updateConsent(true)
      navigate('/dashboard')
    } catch (err) {
      console.error(err)
      setError('An error occurred while logging your consent. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleDecline = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen bg-wellness-50 flex flex-col justify-center items-center px-4 py-8">
      <div className="bg-white p-8 rounded-xl shadow-md border border-wellness-100 max-w-2xl w-full">
        <div className="flex items-center space-x-3 text-wellness-600 border-b border-wellness-100 pb-4 mb-6">
          <ShieldCheck size={36} />
          <div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-800">Privacy & Consent Agreement</h1>
            <p className="text-xs text-slate-500">MindTrace Wellness Monitor (Version 1.0)</p>
          </div>
        </div>

        {error && (
          <div className="bg-rose-50 border-l-4 border-rose-500 p-3 mb-6 text-xs text-rose-700 rounded-r">
            {error}
          </div>
        )}

        <div className="space-y-6 text-sm text-slate-600 leading-relaxed max-h-[300px] overflow-y-auto pr-2 border border-slate-100 p-4 bg-slate-50 rounded-lg">
          <section>
            <h3 className="font-semibold text-slate-800 flex items-center gap-2 mb-1">
              <Eye size={16} /> 1. Data Analysis Protocol
            </h3>
            <p>
              MindTrace extracts text features (e.g., emotional tone, stress signals) from your journal entries. Before these texts are processed, we run a local PII scrubber to strip names, email addresses, and phone numbers.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-slate-800 flex items-center gap-2 mb-1">
              <Database size={16} /> 2. Secure Local Storage
            </h3>
            <p>
              Your journal texts are treated as highly sensitive data. Numeric anomaly scores and check-ins are stored separately in database tables. No data is sent to third-party commercial advertisements.
            </p>
          </section>

          <section>
            <h3 className="font-semibold text-slate-800 flex items-center gap-2 mb-1">
              <FileText size={16} /> 3. Consent & Right to Delete
            </h3>
            <p>
              You have the right to request a full download of all stored information or delete your account permanently. Choosing to delete your account will erase your user identity, check-ins, baselines, and journals from our servers.
            </p>
          </section>

          <section className="bg-amber-50 p-3 border border-amber-250 text-slate-700 text-xs rounded">
            <strong>Safety Warning:</strong> MindTrace is a self-reflection mirror, not a therapist. It does not provide medical diagnoses, psychiatric predictions, or clinical advice. If you are experiencing distress, you will find options to consult local resources in our Support Library.
          </section>
        </div>

        {/* Checkbox */}
        <div className="mt-8 flex items-start space-x-3 bg-wellness-50 p-4 rounded-lg border border-wellness-200">
          <input
            type="checkbox"
            id="consent"
            checked={agreed}
            onChange={(e) => setAgreed(e.target.checked)}
            className="mt-1 h-4 w-4 text-wellness-600 border-slate-350 rounded focus:ring-wellness-500"
          />
          <label htmlFor="consent" className="text-xs text-slate-700 font-medium select-none">
            I consent to the collection, local processing, and storage of my daily check-in ratings and journal entries as outlined in the privacy terms above.
          </label>
        </div>

        {/* Actions */}
        <div className="mt-6 flex flex-col sm:flex-row gap-4 justify-end border-t border-wellness-100 pt-6">
          <button
            onClick={handleDecline}
            className="px-6 py-2 border border-slate-300 rounded-lg text-sm text-slate-700 font-medium hover:bg-slate-50 transition"
          >
            Decline & Exit
          </button>
          <button
            onClick={handleAgree}
            disabled={!agreed || loading}
            className="px-6 py-2 bg-wellness-600 hover:bg-wellness-700 disabled:bg-wellness-400 text-white font-medium rounded-lg text-sm transition shadow-sm"
          >
            {loading ? 'Processing...' : 'Agree & Continue'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Onboarding
