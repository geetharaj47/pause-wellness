import React, { useState, useEffect, useContext } from 'react'
import { Link } from 'react-router-dom'
import { Calendar, Activity, BookOpen, AlertCircle, Sparkles, TrendingUp } from 'lucide-react'
import { AuthContext } from '../App'

const Dashboard = () => {
  const { user } = useContext(AuthContext)
  const [isCheckedIn, setIsCheckedIn] = useState(false)
  const [entryCount, setEntryCount] = useState(0)

  useEffect(() => {
    // Quick local storage checks for mock walkthrough in Phase 1
    const storedCheckins = JSON.parse(localStorage.getItem('mock_checkins') || '[]')
    const today = new Date().toDateString()
    
    const todayChecked = storedCheckins.some(c => new Date(c.created_at).toDateString() === today)
    setIsCheckedIn(todayChecked)
    setEntryCount(storedCheckins.length)
  }, [])

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-wellness-100 pb-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-slate-800">Hello, Friend</h1>
          <p className="text-sm text-slate-500 mt-1">Welcome back to your private reflection space.</p>
        </div>
        <div className="flex items-center space-x-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-600 mt-3 md:mt-0 shadow-sm">
          <Calendar size={14} className="text-wellness-500" />
          <span>{new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</span>
        </div>
      </div>

      {/* Primary Action Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Daily Checkin Tracker */}
        <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-wellness-600">
              <Activity size={20} />
              <h3 className="font-bold text-slate-800">Daily Check-in</h3>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              {isCheckedIn 
                ? "You've successfully completed your check-in for today. Great job!" 
                : "Spend 30 seconds rating your mood and selecting factors influencing your day."}
            </p>
          </div>
          <div className="mt-6">
            {isCheckedIn ? (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-wellness-100 text-wellness-800 border border-wellness-200">
                Completed
              </span>
            ) : (
              <Link to="/journal" className="block text-center bg-wellness-600 hover:bg-wellness-700 text-white text-xs font-bold py-2 rounded-lg transition shadow-sm">
                Start Check-in
              </Link>
            )}
          </div>
        </div>

        {/* Journal Entries Counter */}
        <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-wellness-600">
              <BookOpen size={20} />
              <h3 className="font-bold text-slate-800">Your Journal</h3>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              You have logged <strong className="text-wellness-600">{entryCount}</strong> entries. Longitudinal personalization starts to activate at 5 entries.
            </p>
          </div>
          <div className="mt-6">
            <Link to="/journal" className="block text-center bg-white border border-wellness-300 hover:bg-wellness-50 text-wellness-700 text-xs font-bold py-2 rounded-lg transition">
              Write New Entry
            </Link>
          </div>
        </div>

        {/* Personal Baseline Status */}
        <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-wellness-600">
              <TrendingUp size={20} />
              <h3 className="font-bold text-slate-800">Model Adaptation</h3>
            </div>
            <p className="text-xs text-slate-500 mt-2">
              {entryCount >= 5 
                ? "Your personalized baseline model (Model B) is currently active and learning your patterns." 
                : "MindTrace is running in standard calibration. Keep journaling to trigger individual baselines."}
            </p>
          </div>
          <div className="mt-6">
            <Link to="/trends" className="block text-center bg-white border border-slate-350 hover:bg-slate-50 text-slate-600 text-xs font-bold py-2 rounded-lg transition">
              View Trends
            </Link>
          </div>
        </div>
      </div>

      {/* Middle dashboard block */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Anomaly / What's changing card */}
        <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm">
          <div className="flex items-center space-x-2 text-amber-600 border-b border-slate-100 pb-3 mb-4">
            <AlertCircle size={20} />
            <h3 className="font-bold text-slate-800">What's Changing?</h3>
          </div>
          {entryCount < 5 ? (
            <div className="py-8 text-center text-slate-400 text-xs">
              <p>Insufficent history to compute dynamic statistical shifts.</p>
              <p className="mt-1">Add {5 - entryCount} more journal entries to activate comparison graphs.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                <span className="text-xs font-bold text-amber-800 block uppercase tracking-wide">Dynamic Alert (Model B)</span>
                <p className="text-xs text-slate-700 mt-1">
                  We've noticed a shift: your stress-related signals have increased relative to your usual baseline, appearing alongside academic workload tags.
                </p>
                <Link to="/trends" className="text-xs text-wellness-600 font-semibold hover:underline mt-2 inline-block">Investigate this change &rarr;</Link>
              </div>
            </div>
          )}
        </div>

        {/* Weekly Reflection Summary */}
        <div className="bg-white p-6 rounded-xl border border-wellness-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-wellness-600 border-b border-slate-100 pb-3 mb-4">
              <Sparkles size={20} />
              <h3 className="font-bold text-slate-800">Weekly Reflection</h3>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed">
              Every Sunday, MindTrace compiles a longitudinal summary comparing your weekly scores with your long-term average. Write entries during the week to unlock your upcoming reflection block.
            </p>
          </div>
          <div className="mt-8 bg-wellness-50 border border-wellness-150 p-3 rounded-lg text-xs text-wellness-800">
            <strong>Tip:</strong> Free-form writing helps extract emotional nuance better than numerical checks. Try typing freely about your sleep quality.
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard
