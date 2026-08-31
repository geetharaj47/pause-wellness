import React, { createContext, useState, useEffect, useContext } from 'react'
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate, useLocation } from 'react-router-dom'
import { Heart, Activity, BookOpen, BarChart2, ShieldAlert, LogOut, Settings as SettingsIcon, Menu, X, User } from 'lucide-react'

// ==========================================
# 1. AUTHENTICATION CONTEXT & STATE
// ==========================================

export const AuthContext = createContext(null)

export const AuthProvider = ({ children }) => {
  const [token, setToken] = useState(localStorage.getItem('token') || '')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      localStorage.setItem('token', token)
      // Mock validation/profile loading for UI skeleton (real request in follow-up)
      setUser({
        email: localStorage.getItem('email') || 'user@mindtrace.org',
        hasConsented: localStorage.getItem('consented') === 'true'
      })
    } else {
      localStorage.removeItem('token')
      localStorage.removeItem('email')
      localStorage.removeItem('consented')
      setUser(null)
    }
    setLoading(false)
  }, [token])

  const login = (jwtToken, email, consented) => {
    localStorage.setItem('email', email)
    localStorage.setItem('consented', consented ? 'true' : 'false')
    setToken(jwtToken)
  }

  const logout = () => {
    setToken('')
  }

  const updateConsent = (status) => {
    localStorage.setItem('consented', status ? 'true' : 'false')
    setUser(prev => prev ? { ...prev, hasConsented: status } : null)
  }

  return (
    <AuthContext.Provider value={{ token, user, loading, login, logout, updateConsent }}>
      {children}
    </AuthContext.Provider>
  )
}

// ==========================================
# 2. ROUTE PROTECTIONS (GUARDS)
// ==========================================

const RequireAuth = ({ children }) => {
  const { token, loading } = useContext(AuthContext)
  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  return token ? children : <Navigate to="/login" replace />
}

const RequireConsent = ({ children }) => {
  const { user, loading } = useContext(AuthContext)
  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return user.hasConsented ? children : <Navigate to="/onboarding" replace />
}

// ==========================================
# 3. ROOT SHELL & LAYOUT
// ==========================================

const Layout = () => {
  const { logout, user } = useContext(AuthContext)
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: Activity },
    { name: 'Journal & Check-in', path: '/journal', icon: BookOpen },
    { name: 'History', path: '/history', icon: Heart },
    { name: 'Trends', path: '/trends', icon: BarChart2 },
    { name: 'Support Library', path: '/support', icon: ShieldAlert },
  ]

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-wellness-50">
      {/* Mobile Header */}
      <div className="md:hidden bg-wellness-700 text-white flex items-center justify-between p-4 shadow-md">
        <Link to="/dashboard" className="flex items-center space-x-2 font-bold text-lg">
          <span>🌱 MindTrace</span>
        </Link>
        <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Navigation Sidebar */}
      <aside className={`bg-wellness-800 text-white w-full md:w-64 flex flex-col justify-between shrink-0 shadow-lg transition-all duration-300 md:block ${mobileMenuOpen ? 'block' : 'hidden'}`}>
        <div>
          {/* Header */}
          <div className="hidden md:flex items-center space-x-3 p-6 bg-wellness-900 border-b border-wellness-700">
            <span className="text-xl font-bold tracking-wide">🌱 MindTrace</span>
          </div>

          {/* User profile brief */}
          <div className="p-4 bg-wellness-850 flex items-center space-x-3 border-b border-wellness-700">
            <div className="bg-wellness-600 p-2 rounded-full">
              <User size={18} />
            </div>
            <div className="truncate">
              <p className="text-xs text-wellness-200">Personal space</p>
              <p className="text-sm font-semibold truncate">{user?.email}</p>
            </div>
          </div>

          {/* Nav Links */}
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = location.pathname === item.path
              return (
                <Link
                  key={item.name}
                  to={item.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-all ${
                    isActive
                      ? 'bg-wellness-600 text-white shadow-sm'
                      : 'hover:bg-wellness-700 text-wellness-100 hover:text-white'
                  }`}
                >
                  <Icon size={18} />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Footer actions */}
        <div className="p-4 space-y-1 border-t border-wellness-700 bg-wellness-900/50">
          <Link
            to="/settings"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center space-x-3 px-4 py-2 rounded-lg text-wellness-200 hover:text-white hover:bg-wellness-700/50 transition"
          >
            <SettingsIcon size={16} />
            <span className="text-sm">Privacy & Settings</span>
          </Link>
          <button
            onClick={handleLogout}
            className="flex items-center space-x-3 w-full px-4 py-2 rounded-lg text-wellness-200 hover:text-rose-200 hover:bg-rose-950/20 transition text-left"
          >
            <LogOut size={16} />
            <span className="text-sm">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-h-0 bg-wellness-50">
        <div className="flex-1 overflow-y-auto p-6 md:p-10 max-w-6xl w-full mx-auto">
          <Routes>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/journal" element={<JournalPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/trends" element={<TrendsPage />} />
            <Route path="/support" element={<SupportPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}

// ==========================================
# 4. MOCKED PAGE VIEWS (IMPORTS PLACEHOLDERS)
// ==========================================

import LandingPage from './pages/Landing'
import LoginPage from './pages/Login'
import RegisterPage from './pages/Register'
import OnboardingPage from './pages/Onboarding'
import DashboardPage from './pages/Dashboard'
import JournalPage from './pages/Journal'
import HistoryPage from './pages/History'
import TrendsPage from './pages/Trends'
import SupportPage from './pages/Support'
import SettingsPage from './pages/Settings'

// ==========================================
# 5. CORE ROUTING
// ==========================================

const App = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Views */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Onboarding Consent Gate */}
          <Route path="/onboarding" element={
            <RequireAuth>
              <OnboardingPage />
            </RequireAuth>
          } />

          {/* Secure App Shell */}
          <Route path="/*" element={
            <RequireAuth>
              <RequireConsent>
                <Layout />
              </RequireConsent>
            </RequireAuth>
          } />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
