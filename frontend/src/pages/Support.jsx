import React, { useState, useEffect } from 'react'
import { Sparkles, Play, Pause, RotateCcw, Heart, Calendar, ShieldAlert } from 'lucide-react'

const Support = () => {
  const [activeCategory, setActiveCategory] = useState('stress')
  
  // Box Breathing Timer State
  const [breathingActive, setBreathingActive] = useState(false)
  const [breathPhase, setBreathPhase] = useState('Idle') // Inhale, Hold In, Exhale, Hold Out
  const [secondsLeft, setSecondsLeft] = useState(4)

  useEffect(() => {
    let interval = null
    if (breathingActive) {
      if (secondsLeft === 0) {
        // Transition to next phase
        switch (breathPhase) {
          case 'Idle':
          case 'Hold Out':
            setBreathPhase('Inhale')
            setSecondsLeft(4)
            break
          case 'Inhale':
            setBreathPhase('Hold In')
            setSecondsLeft(4)
            break
          case 'Hold In':
            setBreathPhase('Exhale')
            setSecondsLeft(4)
            break
          case 'Exhale':
            setBreathPhase('Hold Out')
            setSecondsLeft(4)
            break
          default:
            setBreathPhase('Inhale')
            setSecondsLeft(4)
        }
      } else {
        interval = setInterval(() => {
          setSecondsLeft(prev => prev - 1)
        }, 1000)
      }
    } else {
      clearInterval(interval)
    }
    return () => clearInterval(interval)
  }, [breathingActive, secondsLeft, breathPhase])

  const startBreathing = () => {
    setBreathPhase('Inhale')
    setSecondsLeft(4)
    setBreathingActive(true)
  }

  const stopBreathing = () => {
    setBreathingActive(false)
    setBreathPhase('Idle')
    setSecondsLeft(4)
  }

  const categories = [
    { id: 'stress', name: 'Stress & Calm' },
    { id: 'academic', name: 'Work & Prioritization' },
    { id: 'sleep', name: 'Wind-Down Routine' },
    { id: 'rumination', name: 'Reframing Thoughts' },
  ]

  // Box Breathing animation details
  const getCircleScale = () => {
    if (!breathingActive) return 'scale-75 bg-wellness-200'
    if (breathPhase === 'Inhale') return 'scale-110 bg-wellness-400 transition-all duration-[4000ms] ease-linear'
    if (breathPhase === 'Hold In') return 'scale-110 bg-wellness-500'
    if (breathPhase === 'Exhale') return 'scale-75 bg-wellness-300 transition-all duration-[4000ms] ease-linear'
    if (breathPhase === 'Hold Out') return 'scale-75 bg-wellness-200'
    return 'scale-75'
  }

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-wellness-100 pb-4">
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-800">Support Library</h1>
        <p className="text-sm text-slate-500 mt-1">Explore controlled, curated exercises designed to help you self-reflect and relax.</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 gap-4 overflow-x-auto pb-1">
        {categories.map((c) => (
          <button
            key={c.id}
            onClick={() => {
              setActiveCategory(c.id)
              stopBreathing()
            }}
            className={`px-4 py-2 text-xs font-bold whitespace-nowrap border-b-2 transition-all ${
              activeCategory === c.id
                ? 'border-wellness-600 text-wellness-700'
                : 'border-transparent text-slate-400 hover:text-slate-650'
            }`}
          >
            {c.name}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Panel Details */}
        <div className="lg:col-span-2 space-y-6">
          {activeCategory === 'stress' && (
            <div className="space-y-6">
              {/* Interactive Widget */}
              <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm flex flex-col items-center justify-center text-center">
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide mb-2">Box Breathing Exercise</h3>
                <p className="text-xs text-slate-500 max-w-sm mb-6">
                  Follow the rhythm: Inhale, hold, exhale, hold. Each phase lasts 4 seconds.
                </p>

                {/* Animated breathing circle */}
                <div className="w-48 h-48 flex items-center justify-center relative mb-6">
                  {/* Outer pulsating ring */}
                  <div className={`w-36 h-36 rounded-full flex flex-col items-center justify-center text-white font-bold text-lg shadow-md transform transition-transform ${getCircleScale()}`}>
                    <span className="text-xs tracking-wider uppercase opacity-80">{breathPhase}</span>
                    {breathingActive && <span className="text-2xl mt-1">{secondsLeft}s</span>}
                  </div>
                </div>

                {/* Controls */}
                <div className="space-x-3">
                  {!breathingActive ? (
                    <button
                      onClick={startBreathing}
                      className="bg-wellness-600 hover:bg-wellness-700 text-white text-xs font-bold px-4 py-2 rounded-lg shadow transition flex items-center gap-1.5 inline-flex"
                    >
                      <Play size={12} /> Start Breathing
                    </button>
                  ) : (
                    <button
                      onClick={stopBreathing}
                      className="bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold px-4 py-2 rounded-lg shadow transition flex items-center gap-1.5 inline-flex"
                    >
                      <Pause size={12} /> Stop Timer
                    </button>
                  )}
                </div>
              </div>

              {/* Grounding Exercise Info */}
              <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm space-y-3">
                <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide border-b border-slate-100 pb-2">5-4-3-2-1 Grounding Method</h3>
                <p className="text-xs text-slate-650 leading-relaxed">
                  When feeling overwhelmed or anxious, slow down your thoughts by noticing things in your environment:
                </p>
                <ul className="text-xs text-slate-600 space-y-1.5 pl-4 list-decimal font-semibold">
                  <li>Identify <span className="text-wellness-700">5</span> things you can see around you.</li>
                  <li>Identify <span className="text-wellness-700">4</span> things you can physically touch.</li>
                  <li>Identify <span className="text-wellness-700">3</span> things you can hear in the distance.</li>
                  <li>Identify <span className="text-wellness-700">2</span> things you can smell.</li>
                  <li>Identify <span className="text-wellness-700">1</span> thing you can taste.</li>
                </ul>
              </div>
            </div>
          )}

          {activeCategory === 'academic' && (
            <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide border-b border-slate-100 pb-2">Task Deconstruction</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                When academic demands spike, cognitive load can paralyze productivity. Use a micro-progress routine:
              </p>
              <div className="space-y-3 mt-4 text-xs text-slate-650">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <strong className="text-slate-800 block mb-1">Step 1: Set the smallest possible threshold</strong>
                  Define a task so small it feels trivial: e.g., "I will open my code editor and type one line of comments," or "I will read one page of references."
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg">
                  <strong className="text-slate-800 block mb-1">Step 2: Commit to 10 Minutes Only</strong>
                  Allow yourself permission to stop after 10 minutes. More often than not, starting is the highest energy barrier.
                </div>
              </div>
            </div>
          )}

          {activeCategory === 'sleep' && (
            <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide border-b border-slate-100 pb-2">Wind-Down checklist</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                If you have been mentioning sleep difficulties, try building a transition ritual between work and rest:
              </p>
              <ul className="text-xs text-slate-650 space-y-2 pl-4 list-disc">
                <li>**Work Terminus:** Close all academic/work tabs 60 minutes before bed. Store laptops in a bag to create physical boundaries.</li>
                <li>**Decompression:** Spend 15 minutes journaling freely in MindTrace to download rumination cycles.</li>
                <li>**Screen-free Gap:** Avoid news and social feeds in bed; replace with reading or progressive muscle relaxation.</li>
              </ul>
            </div>
          )}

          {activeCategory === 'rumination' && (
            <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wide border-b border-slate-100 pb-2">Cognitive Reframing</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Notice loops where you exaggerate worst-case scenarios:
              </p>
              <div className="space-y-3 mt-4 text-xs">
                <div className="p-3 bg-rose-50 border border-rose-150 rounded-lg">
                  <strong className="text-rose-800 block">Initial Thought (Catastrophizing):</strong>
                  "I'm failing my project review, and I won't get my degree."
                </div>
                <div className="p-3 bg-emerald-50 border border-emerald-150 rounded-lg">
                  <strong className="text-emerald-800 block">Reframed Observation:</strong>
                  "I have some complex feedback to address, but this is a normal revision stage. I can schedule a help session with my project guide."
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Safety Callouts */}
        <div className="lg:col-span-1 bg-white p-6 rounded-xl border border-wellness-100 shadow-sm space-y-6 self-start">
          <div className="flex items-center space-x-2 text-rose-600 border-b border-slate-100 pb-3 mb-2">
            <ShieldAlert size={20} />
            <h3 className="font-bold text-slate-800">Crisis Help</h3>
          </div>
          <p className="text-xs text-slate-500 leading-relaxed">
            If you or someone you care about is going through a critical crisis, professional human help is available immediately.
          </p>

          <div className="space-y-3 pt-2">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="text-xs font-bold text-slate-800">988 Lifeline</h4>
              <p className="text-[10px] text-slate-500 mt-0.5">Free national support (US & Canada)</p>
              <p className="text-xs font-bold text-wellness-700 mt-1">Call / Text: 988</p>
            </div>
            
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <h4 className="text-xs font-bold text-slate-800">Kiran Helpline</h4>
              <p className="text-[10px] text-slate-500 mt-0.5">National mental health helpline (India)</p>
              <p className="text-xs font-bold text-wellness-700 mt-1">Call: 1800-599-0019</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

export default Support
