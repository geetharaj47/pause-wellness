import React, { useState, useContext } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { AuthContext } from '../App'
import { ArrowLeft } from 'lucide-react'

const Register = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [timezone, setTimezone] = useState(Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const { login } = useContext(AuthContext)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)
    try {
      const response = await axios.post('http://localhost:8000/api/auth/register', {
        email,
        password,
        timezone
      })
      
      const { access_token, email: userEmail } = response.data
      
      // Since it's a new account, they definitely haven't consented yet.
      login(access_token, userEmail, false)
      navigate('/onboarding')
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || 'Failed to register account. Ensure email is valid and unique.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-wellness-50 flex flex-col justify-center items-center px-4">
      <Link to="/" className="mb-6 flex items-center space-x-2 text-sm text-wellness-600 hover:text-wellness-800 font-medium">
        <ArrowLeft size={16} />
        <span>Return to Home</span>
      </Link>

      <div className="bg-white p-8 rounded-xl shadow-md border border-wellness-100 max-w-md w-full">
        <h2 className="text-2xl font-bold text-center text-slate-800">Create Private Space</h2>
        <p className="text-center text-sm text-slate-500 mt-1">Begin monitoring your wellness patterns</p>

        {error && (
          <div className="bg-rose-50 border-l-4 border-rose-500 p-3 mt-4 text-xs text-rose-700 rounded-r">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-wellness-500 focus:border-wellness-500"
              placeholder="you@email.com"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">Password (Min 6 chars)</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-wellness-500 focus:border-wellness-500"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">Confirm Password</label>
            <input
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-1 focus:ring-wellness-500 focus:border-wellness-500"
              placeholder="••••••••"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider">Timezone</label>
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="mt-1 block w-full px-3 py-2 border border-slate-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-1 focus:ring-wellness-500 focus:border-wellness-500"
            >
              <option value="UTC">UTC (Universal Coordinated Time)</option>
              <option value="America/New_York">EST (Eastern Standard Time)</option>
              <option value="Europe/London">GMT (Greenwich Mean Time)</option>
              <option value="Asia/Kolkata">IST (Indian Standard Time)</option>
              <option value="Asia/Tokyo">JST (Japan Standard Time)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-wellness-600 hover:bg-wellness-700 disabled:bg-wellness-400 text-white py-2 rounded-lg font-semibold shadow-sm transition mt-6"
          >
            {loading ? 'Creating Account...' : 'Register Account'}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-slate-500">
          Already registered?{' '}
          <Link to="/login" className="text-wellness-600 hover:underline font-semibold">Log in</Link>
        </p>
      </div>
    </div>
  )
}

export default Register
