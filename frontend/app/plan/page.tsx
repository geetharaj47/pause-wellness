'use client';

import React, { useState, useEffect } from 'react';
import { CheckSquare, Check, Plus, Trash2, Calendar, Sparkles } from 'lucide-react';
import { fetchWithAuth } from '../lib/api';

export default function PlanPage() {
  const [focus, setFocus] = useState('');
  const [steps, setSteps] = useState<{ id: string; text: string; completed: bool }[]>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  const todayStr = new Date().toISOString().split('T')[0];
  const formattedToday = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric'
  });

  useEffect(() => {
    loadPlan();
  }, []);

  async function loadPlan() {
    try {
      const res = await fetchWithAuth('/api/v1/daily-plan/today');
      if (res.ok) {
        const data = await res.json();
        if (data) {
          setFocus(data.focus || '');
          setSteps(data.steps || []);
        }
      }
    } catch {
      // Offline fallback
    }
  }

  async function handleSave() {
    if (!focus.trim()) return;
    setIsSaving(true);
    setSaveStatus(null);
    try {
      const res = await fetchWithAuth('/api/v1/daily-plan/today', {
        method: 'PUT',
        body: JSON.stringify({
          local_date: todayStr,
          focus,
          steps
        })
      });
      if (res.ok) {
        setSaveStatus('Plan updated gently.');
        setTimeout(() => setSaveStatus(null), 3000);
      }
    } catch {
      setSaveStatus('Could not save plan.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeletePlan() {
    if (!confirm('Clear today\'s plan?')) return;
    try {
      await fetchWithAuth('/api/v1/daily-plan/today', { method: 'DELETE' });
      setFocus('');
      setSteps([]);
    } catch {
      // Ignore
    }
  }

  function addStep() {
    if (steps.length >= 3) return;
    setSteps([...steps, { id: String(Date.now()), text: '', completed: false }]);
  }

  function updateStepText(idx: number, text: string) {
    const next = [...steps];
    next[idx].text = text;
    setSteps(next);
  }

  function toggleStep(idx: number) {
    const next = [...steps];
    next[idx].completed = !next[idx].completed;
    setSteps(next);
  }

  function removeStep(idx: number) {
    setSteps(steps.filter((_, i) => i !== idx));
  }

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      {/* Header */}
      <div className="border-b border-paper-300 pb-4">
        <span className="text-xs uppercase tracking-wider font-semibold text-sage-600">Gentle Focus</span>
        <h1 className="font-serif text-3xl font-bold tracking-tight text-forest mt-1">My Plan · {formattedToday}</h1>
        <p className="text-sm text-forest-muted mt-1">
          Pick one priority that matters today and break it into up to three small steps. No scores, no streaks, no productivity guilt.
        </p>
      </div>

      {/* Plan Card */}
      <div className="bg-white rounded-2xl border border-paper-300 p-6 md:p-8 shadow-sm space-y-6">
        <div className="space-y-2">
          <label className="block text-sm font-bold text-forest">
            What is your single focus for today?
          </label>
          <input
            type="text"
            value={focus}
            onChange={(e) => setFocus(e.target.value)}
            placeholder="e.g. Work through 2 practice problems for algorithms class"
            className="w-full p-3.5 rounded-xl border border-paper-300 bg-paper-50 text-sm text-forest placeholder:text-stone-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-sage-600/30 font-medium"
          />
        </div>

        {/* Steps */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs uppercase tracking-wider font-semibold text-forest-muted">
              Small Steps ({steps.length}/3)
            </label>
            <span className="text-xs text-forest-muted">Check off or edit freely</span>
          </div>

          <div className="space-y-2.5">
            {steps.map((step, idx) => (
              <div key={step.id || idx} className="flex items-center space-x-3 p-2.5 rounded-xl border border-paper-200 bg-paper-50/60">
                <button
                  type="button"
                  onClick={() => toggleStep(idx)}
                  className={`w-6 h-6 rounded-lg border flex items-center justify-center transition shrink-0 ${
                    step.completed ? 'bg-sage-600 border-sage-600 text-white' : 'border-paper-300 bg-white hover:border-sage-500'
                  }`}
                  title={step.completed ? 'Mark incomplete' : 'Mark complete'}
                >
                  {step.completed && <Check className="w-4 h-4" />}
                </button>
                <input
                  type="text"
                  value={step.text}
                  onChange={(e) => updateStepText(idx, e.target.value)}
                  placeholder={`Step ${idx + 1}`}
                  className={`flex-1 bg-transparent text-sm focus:outline-none ${
                    step.completed ? 'line-through text-stone-400' : 'text-forest'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => removeStep(idx)}
                  className="text-stone-400 hover:text-rose-600 text-sm px-2"
                >
                  ×
                </button>
              </div>
            ))}

            {steps.length < 3 && (
              <button
                type="button"
                onClick={addStep}
                className="w-full py-2.5 border border-dashed border-paper-300 rounded-xl text-xs font-medium text-sage-700 hover:bg-sage-50 transition flex items-center justify-center space-x-1.5"
              >
                <Plus className="w-4 h-4" />
                <span>Add small step</span>
              </button>
            )}
          </div>
        </div>

        {/* Actions bar */}
        <div className="flex items-center justify-between pt-4 border-t border-paper-200">
          <div>
            {saveStatus && <span className="text-xs text-emerald-700 font-medium">{saveStatus}</span>}
          </div>
          <div className="flex items-center space-x-3">
            {(focus || steps.length > 0) && (
              <button
                type="button"
                onClick={handleDeletePlan}
                className="text-xs text-forest-muted hover:text-rose-700 transition"
              >
                Clear plan
              </button>
            )}
            <button
              type="button"
              onClick={handleSave}
              disabled={isSaving || !focus.trim()}
              className="px-5 py-2 rounded-xl text-sm font-semibold bg-sage-600 hover:bg-sage-700 text-white transition shadow-sm disabled:opacity-50"
            >
              {isSaving ? 'Saving...' : 'Save Plan'}
            </button>
          </div>
        </div>
      </div>

      {/* Gentle reassurance notice */}
      <div className="p-4 rounded-xl bg-paper-200 text-xs text-forest-muted leading-relaxed">
        <p className="font-semibold text-forest">A reminder about university days:</p>
        <p className="mt-0.5">
          Completing or not completing these steps is never an evaluation of your discipline or wellbeing. If your energy shifted today, you are completely free to edit, pause, or discard this plan.
        </p>
      </div>
    </div>
  );
}

