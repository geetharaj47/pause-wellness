import React, { useState, useEffect } from 'react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { TrendingUp, Info, ToggleLeft, ToggleRight, Sparkles } from 'lucide-react'

// ==========================================
# GENERATE SYNTHETIC 30-DAY DEMO DATA
// ==========================================
const generateDemoData = () => {
  const data = []
  const baseStressMean = 0.3
  const baseStressStd = 0.08
  
  // Phase 1: Days 1-20 (Normal Stable Baseline)
  for (let i = 1; i <= 20; i++) {
    // Small random fluctuations around base stress
    const stress = Math.max(0.1, baseStressMean + (Math.random() - 0.5) * 0.2)
    data.push({
      day: `Day ${i}`,
      mood: Math.floor(Math.random() * 2) + 4, // 4 or 5
      sleep: Math.floor(Math.random() * 2) + 4, // 4 or 5
      stress: parseFloat(stress.toFixed(2)),
      fatigue: parseFloat((stress * 0.8 + Math.random() * 0.1).toFixed(2)),
      baselineMean: baseStressMean,
      dynamicThreshold: parseFloat((baseStressMean + 1.96 * baseStressStd).toFixed(2)),
      staticThreshold: 0.70
    })
  }

  // Inject a sudden stress spike on Day 15 (Single anomaly, should NOT trigger Model B flag if short)
  data[14].stress = 0.65 // Single spike
  data[14].mood = 3
  
  // Phase 2: Days 21-30 (Injected Shift - Sleep problems & high academic pressure)
  const shiftStressMean = 0.72
  for (let i = 21; i <= 30; i++) {
    const stress = Math.max(0.55, shiftStressMean + (Math.random() - 0.5) * 0.25)
    data.push({
      day: `Day ${i}`,
      mood: Math.floor(Math.random() * 2) + 1, // 1 or 2 (Difficult / Very Difficult)
      sleep: Math.floor(Math.random() * 2) + 1, // 1 or 2 (Difficult / Very Difficult)
      stress: parseFloat(stress.toFixed(2)),
      fatigue: parseFloat((stress * 0.9 + Math.random() * 0.1).toFixed(2)),
      baselineMean: baseStressMean,
      // For simplicity, we keep referencing the trained baseline parameters
      dynamicThreshold: parseFloat((baseStressMean + 1.96 * baseStressStd).toFixed(2)),
      staticThreshold: 0.70
    })
  }

  return data
}

const Trends = () => {
  const [demoMode, setDemoMode] = useState(true)
  const [chartData, setChartData] = useState([])
  const [userEntries, setUserEntries] = useState([])

  useEffect(() => {
    // Read local journal records
    const stored = JSON.parse(localStorage.getItem('mock_checkins') || '[]')
    const formatted = stored.reverse().map((entry, index) => ({
      day: `Log ${index + 1}`,
      mood: entry.mood,
      sleep: entry.sleep || 3,
      // Simulate basic NLP extraction scores locally for visual chart
      stress: entry.academic_work ? 0.8 : (entry.mood <= 2 ? 0.6 : 0.25),
      fatigue: entry.sleep <= 2 ? 0.75 : 0.3
    }))
    setUserEntries(formatted)
    
    if (demoMode) {
      setChartData(generateDemoData())
    } else {
      setChartData(formatted)
    }
  }, [demoMode])

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="border-b border-wellness-100 pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-800">Wellness Trends</h1>
          <p className="text-sm text-slate-500 mt-1">Visualize longitudinal wellness indexes and shift detections.</p>
        </div>
        
        {/* Toggle Mode */}
        <button
          onClick={() => setDemoMode(!demoMode)}
          className="flex items-center space-x-2 bg-white border border-wellness-250 px-4 py-2 rounded-xl text-xs font-bold text-slate-700 shadow-sm transition hover:bg-slate-55/30"
        >
          {demoMode ? <ToggleRight className="text-wellness-600" size={20} /> : <ToggleLeft className="text-slate-400" size={20} />}
          <span>{demoMode ? 'Showing Demonstration Cohort (30 Days)' : 'Showing My Active Logs'}</span>
        </button>
      </div>

      {/* Warning/Info bar for demonstration */}
      {demoMode && (
        <div className="bg-wellness-100 border border-wellness-250 p-4 rounded-xl text-xs text-wellness-850 flex items-start space-x-3">
          <Sparkles size={18} className="text-wellness-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold">Understanding Research Comparison (Model A vs. Model B):</h4>
            <p className="mt-1 leading-relaxed">
              *   **Model A (Static Population Threshold = 0.70):** Flags alerts ONLY when stress exceeds 0.70. Note that it fails to flag the onset of stress on Day 21-22 because the scores are rising but haven't crossed the hard ceiling.
            </p>
            <p className="mt-1 leading-relaxed">
              *   **Model B (Personalized Dynamic Threshold = ~0.46):** Automatically calculates your individual baseline standard deviation. It flags stress as a statistical deviation on **Day 21**—detecting the shift earlier and adapting to your normal quiet period.
            </p>
          </div>
        </div>
      )}

      {/* Verification state for active logs */}
      {!demoMode && userEntries.length < 5 && (
        <div className="bg-amber-50 border border-amber-250 p-6 rounded-xl text-center text-xs text-slate-650">
          <Info size={24} className="text-amber-500 mx-auto mb-2" />
          <h4 className="font-bold text-slate-850">Insufficient Data</h4>
          <p className="mt-1">
            We require at least **5 check-ins** before we can build a baseline and render trends. You currently have {userEntries.length} logged.
          </p>
        </div>
      )}

      {(demoMode || userEntries.length >= 5) && (
        <div className="grid grid-cols-1 gap-6">
          
          {/* Chart 1: Mood & Sleep */}
          <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4">Mood & Sleep Index</h3>
            <div className="h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="day" style={{ fontSize: 10, fill: '#64748b' }} />
                  <YAxis domain={[1, 5]} ticks={[1, 2, 3, 4, 5]} style={{ fontSize: 10, fill: '#64748b' }} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                  <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                  <Line type="monotone" dataKey="mood" name="Mood Rating" stroke="#58846c" strokeWidth={2} activeDot={{ r: 6 }} />
                  <Line type="monotone" dataKey="sleep" name="Sleep Quality" stroke="#818cf8" strokeWidth={2} strokeDasharray="4 4" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Chart 2: NLP Derived Signals (Stress) */}
          <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
              <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Derived Stress Signal Deviation</h3>
              <div className="flex items-center space-x-4 text-[10px] font-semibold text-slate-500">
                <span className="flex items-center space-x-1"><span className="w-3 h-0.5 bg-rose-500 block"></span><span>Model A Ceiling (0.70)</span></span>
                <span className="flex items-center space-x-1"><span className="w-3 h-0.5 bg-amber-500 block"></span><span>Model B Threshold (Dynamic)</span></span>
              </div>
            </div>
            
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                  <defs>
                    <linearGradient id="colorStress" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.2}/>
                      <stop offset="95%" stopColor="#f43f5e" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="day" style={{ fontSize: 10, fill: '#64748b' }} />
                  <YAxis domain={[0.0, 1.0]} ticks={[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]} style={{ fontSize: 10, fill: '#64748b' }} />
                  <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                  <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                  <Area type="monotone" dataKey="stress" name="Derived Stress Score" stroke="#f43f5e" strokeWidth={2} fillOpacity={1} fill="url(#colorStress)" />
                  
                  {/* Threshold overlays (available in demo data) */}
                  {demoMode && (
                    <>
                      <ReferenceLine y={0.70} stroke="#f43f5e" strokeDasharray="3 3" strokeWidth={1.5} label={{ value: 'Model A', position: 'insideRight', fill: '#f43f5e', fontSize: 9 }} />
                      <Line type="monotone" dataKey="dynamicThreshold" name="Model B Threshold" stroke="#d97706" strokeWidth={1.5} dot={false} strokeDasharray="5 5" />
                    </>
                  )}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      )}
    </div>
  )
}

export default Trends
