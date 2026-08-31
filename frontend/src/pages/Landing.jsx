import React from 'react'
import { Link } from 'react-router-dom'
import { EyeOff, UserCheck, Shield } from 'lucide-react'

const Landing = () => {
  return (
    <div className="min-h-screen bg-wellness-50 flex flex-col justify-between">
      {/* Header Bar */}
      <header className="px-6 py-4 flex items-center justify-between bg-white border-b border-wellness-100 shadow-sm">
        <div className="flex items-center space-x-2 font-bold text-xl text-wellness-800">
          <span>🌱 MindTrace</span>
        </div>
        <div className="space-x-4">
          <Link to="/login" className="text-wellness-600 hover:text-wellness-800 font-medium">Log In</Link>
          <Link to="/register" className="bg-wellness-600 hover:bg-wellness-700 text-white px-4 py-2 rounded-lg font-medium transition">Get Started</Link>
        </div>
      </header>

      {/* Hero section */}
      <main className="max-w-4xl mx-auto px-6 py-16 flex-1 flex flex-col items-center justify-center text-center">
        <h1 className="text-4xl md:text-5xl font-extrabold text-slate-800 tracking-tight leading-tight">
          A personalized, private mirror for your <span className="text-wellness-600">wellness patterns</span>.
        </h1>
        <p className="mt-6 text-lg md:text-xl text-slate-600 max-w-2xl">
          MindTrace logs daily check-ins and journal entries to dynamically learn your unique wellness baseline, helping you notice and reflect on meaningful changes over time.
        </p>

        <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/register" className="bg-wellness-600 hover:bg-wellness-700 text-white px-8 py-3 rounded-lg text-lg font-semibold shadow-md transition">
            Create Your Private Space
          </Link>
          <Link to="/login" className="bg-white border border-slate-350 hover:bg-slate-50 text-slate-700 px-8 py-3 rounded-lg text-lg font-semibold shadow-sm transition">
            Log In
          </Link>
        </div>

        {/* Feature Highlights */}
        <section className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 text-left w-full">
          <div className="p-6 bg-white rounded-xl shadow-sm border border-wellness-100/50">
            <div className="p-3 bg-wellness-100 rounded-lg text-wellness-700 inline-block">
              <EyeOff size={24} />
            </div>
            <h3 className="mt-4 text-lg font-bold text-slate-800">Privacy by Design</h3>
            <p className="mt-2 text-sm text-slate-600">
              Your journal texts are encrypted. All NLP analysis runs locally. Your personal data is never shared or sold.
            </p>
          </div>

          <div className="p-6 bg-white rounded-xl shadow-sm border border-wellness-100/50">
            <div className="p-3 bg-wellness-100 rounded-lg text-wellness-700 inline-block">
              <UserCheck size={24} />
            </div>
            <h3 className="mt-4 text-lg font-bold text-slate-800">Personalized Baseline</h3>
            <p className="mt-2 text-sm text-slate-600">
              No generic thresholds. MindTrace models your individual trends, recognizing deviations relative only to your own normal history.
            </p>
          </div>

          <div className="p-6 bg-white rounded-xl shadow-sm border border-wellness-100/50">
            <div className="p-3 bg-wellness-100 rounded-lg text-wellness-700 inline-block">
              <Shield size={24} />
            </div>
            <h3 className="mt-4 text-lg font-bold text-slate-800">Clinical Safety Boundary</h3>
            <p className="mt-2 text-sm text-slate-600">
              Not a diagnostic tool or therapist. We provide a space for quiet self-reflection alongside secure pathways to human care.
            </p>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-wellness-100 py-6 text-center text-xs text-slate-500 bg-white">
        &copy; {new Date().getFullYear()} MindTrace Mental Wellness Monitoring. Built for final-year CS project and research.
      </footer>
    </div>
  )
}

export default Landing
