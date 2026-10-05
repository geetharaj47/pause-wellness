'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Sparkles, Check, CheckSquare, Plus, ArrowRight, Heart, Calendar, BookOpen, Clock, Tag } from 'lucide-react';
import { fetchWithAuth, getStoredToken } from './lib/api';

const MOODS = [
  { label: 'Great', emoji: '☀️', color: 'border-amber-300 hover:bg-amber-50' },
  { label: 'Good', emoji: '🌿', color: 'border-emerald-300 hover:bg-emerald-50' },
  { label: 'Okay', emoji: '☁️', color: 'border-slate-300 hover:bg-slate-50' },
  { label: 'Uneasy', emoji: '🌊', color: 'border-indigo-300 hover:bg-indigo-50' },
  { label: 'Difficult', emoji: '🌧️', color: 'border-stone-400 hover:bg-stone-50' },
];

const CONTEXT_TAGS = ['study', 'sleep', 'relationships', 'health', 'finances', 'other'];

export default function TodayPage() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  const [selectedEnergy, setSelectedEnergy] = useState<number | null>(null);
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [note, setNote] = useState('');
  const [existingCheckinId, setExistingCheckinId] = useState<string | null>(null);
  const [checkinSaved, setCheckinSaved] = useState(false);
  const [isSavingCheckin, setIsSavingCheckin] = useState(false);

  // Today's Plan state
  const [planFocus, setPlanFocus] = useState('');
  const [planSteps, setPlanSteps] = useState<{ id: string; text: string; completed: bool }[]>([]);
  const [isSavingPlan, setIsSavingPlan] = useState(false);
  const [planSaved, setPlanSaved] = useState(false);

  // Suggested Action state
  const [suggestedAction, setSuggestedAction] = useState<any>(null);
  const [feedbackSent, setFeedbackSent] = useState<string | null>(null);

  const todayDateStr = new Date().toISOString().split('T')[0];
  const formattedToday = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric'
  });

  useEffect(() => {
    const token = getStoredToken();
    if (token) {
      setIsLoggedIn(true);
      loadTodayData();
    } else {
      setIsLoggedIn(false);
      loadSampleAction('study');
    }
  }, []);

  async function loadTodayData() {
    try {
      // 1. Fetch check-in for today
      const ciRes = await fetchWithAuth('/api/v1/check-ins?limit=1');
      if (ciRes.ok) {
        const checkins = await ciRes.json();
        if (checkins.length > 0 && checkins[0].local_date === todayDateStr) {
          const ci = checkins[0];
          setExistingCheckinId(ci.id);
          setSelectedMood(ci.self_reported_mood);
          setSelectedEnergy(ci.self_reported_energy);
          setSelectedTags(ci.context_tags || []);
          setNote(ci.note || '');
          setCheckinSaved(true);
        }
      }

      // 2. Fetch daily plan
      const planRes = await fetchWithAuth('/api/v1/daily-plan/today');
      if (planRes.ok) {
        const plan = await planRes.json();
        if (plan) {
          setPlanFocus(plan.focus || '');
          setPlanSteps(plan.steps || []);
        }
      }

      // 3. Fetch suggested action based on first selected tag or study
      const primaryContext = selectedTags.length > 0 ? selectedTags[0] : 'study';
      loadSampleAction(primaryContext);
    } catch {
      // Offline fallback
    }
  }

  async function loadSampleAction(context: string) {
    try {
      const res = await fetchWithAuth(`/api/v1/actions?context=${context}`);
      if (res.ok) {
        const actions = await res.json();
        if (actions.length > 0) {
          setSuggestedAction(actions[0]);
        }
      }
    } catch {
      // Ignore
    }
  }

  function toggleTag(tag: string) {
    const nextTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];
    setSelectedTags(nextTags);
    if (nextTags.length > 0) {
      loadSampleAction(nextTags[0]);
    }
  }

  async function handleSaveCheckin() {
    if (!isLoggedIn) {
      alert("Please log in or click 'Use Demo Account' to save your check-ins.");
      return;
    }
    setIsSavingCheckin(true);
    try {
      const payload = {
        local_date: todayDateStr,
        self_reported_mood: selectedMood,
        self_reported_energy: selectedEnergy,
        context_tags: selectedTags,
        note: note.trim() || null
      };

      let res;
      if (existingCheckinId) {
        res = await fetchWithAuth(`/api/v1/check-ins/${existingCheckinId}`, {
          method: 'PATCH',
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetchWithAuth('/api/v1/check-ins', {
          method: 'POST',
          body: JSON.stringify(payload)
        });
      }

      if (res.ok) {
        const data = await res.json();
        setExistingCheckinId(data.id);
        setCheckinSaved(true);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSavingCheckin(false);
    }
  }

  async function handleSavePlan() {
    if (!planFocus.trim()) return;
    setIsSavingPlan(true);
    try {
      const res = await fetchWithAuth('/api/v1/daily-plan/today', {
        method: 'PUT',
        body: JSON.stringify({
          local_date: todayDateStr,
          focus: planFocus,
          steps: planSteps
        })
      });
      if (res.ok) {
        setPlanSaved(true);
        setTimeout(() => setPlanSaved(false), 2500);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsSavingPlan(false);
    }
  }

  function addPlanStep() {
    if (planSteps.length >= 3) return;
    setPlanSteps([...planSteps, { id: String(Date.now()), text: '', completed: false }]);
  }

  function updatePlanStepText(index: number, text: string) {
    const updated = [...planSteps];
    updated[index].text = text;
    setPlanSteps(updated);
  }

  function togglePlanStepCompleted(index: number) {
    const updated = [...planSteps];
    updated[index].completed = !updated[index].completed;
    setPlanSteps(updated);
  }

  function removePlanStep(index: number) {
    const updated = planSteps.filter((_, i) => i !== index);
    setPlanSteps(updated);
  }

  async function handleActionFeedback(outcome: string) {
    if (!suggestedAction) return;
    try {
      await fetchWithAuth('/api/v1/action-events', {
        method: 'POST',
        body: JSON.stringify({
          action_id: suggestedAction.id,
          local_date: todayDateStr,
          outcome
        })
      });
      setFeedbackSent(outcome);
    } catch {
      // Ignore
    }
  }

  return (
    <div className="space-y-8">
      {/* Date & Header */}
      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between border-b border-paper-300 pb-4">
        <div>
          <span className="text-xs uppercase tracking-wider font-semibold text-sage-600">Daily Reflection</span>
          <h1 className="font-serif text-3xl font-bold tracking-tight text-forest mt-1">Today · {formattedToday}</h1>
          <p className="text-sm text-forest-muted mt-1">
            Check in briefly. Everything is optional, private to your account, and completely user-directed.
          </p>
        </div>

        {!isLoggedIn && (
          <div className="mt-3 sm:mt-0">
            <Link
              href="/login"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-sage-100 hover:bg-sage-200 text-sage-800 transition"
            >
              <span>Explore as Reviewer (Demo)</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}
      </div>

      {/* Grid: Check-in (Left 3 cols) and Next Step / Plan (Right 2 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* CHECK-IN CARD */}
        <div className="lg:col-span-3 space-y-6">
          <div className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-6">
            <div>
              <h2 className="text-lg font-bold text-forest flex items-center space-x-2">
                <span>1. How are you feeling right now?</span>
                <span className="text-xs font-normal text-forest-muted">(optional self-report)</span>
              </h2>
              <p className="text-xs text-forest-muted mt-0.5">
                Your stated mood is stored as your own direct record and kept separate from any AI analysis.
              </p>
            </div>

            {/* Mood selector */}
            <div className="grid grid-cols-5 gap-2">
              {MOODS.map((m) => {
                const isSelected = selectedMood === m.label;
                return (
                  <button
                    key={m.label}
                    type="button"
                    onClick={() => setSelectedMood(isSelected ? null : m.label)}
                    className={`flex flex-col items-center justify-center p-3 rounded-xl border text-center transition ${
                      isSelected
                        ? 'bg-sage-100 border-sage-600 ring-2 ring-sage-600/30 font-semibold text-sage-900'
                        : `border-paper-300 bg-paper-50 ${m.color} text-forest`
                    }`}
                  >
                    <span className="text-2xl mb-1">{m.emoji}</span>
                    <span className="text-xs">{m.label}</span>
                  </button>
                );
              })}
            </div>

            {/* Energy selector */}
            <div className="space-y-2 pt-2 border-t border-paper-200">
              <label className="text-sm font-semibold text-forest flex items-center justify-between">
                <span>Energy level: {selectedEnergy ? `${selectedEnergy} / 5` : 'Not specified'}</span>
                <span className="text-xs text-forest-muted">1 (low) to 5 (high)</span>
              </label>
              <div className="grid grid-cols-5 gap-2">
                {[1, 2, 3, 4, 5].map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setSelectedEnergy(selectedEnergy === lvl ? null : lvl)}
                    className={`py-2 rounded-lg text-xs font-semibold border transition ${
                      selectedEnergy === lvl
                        ? 'bg-forest text-white border-forest'
                        : 'bg-paper-50 border-paper-300 text-forest hover:bg-paper-200'
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>

            {/* Context tags */}
            <div className="space-y-2 pt-2 border-t border-paper-200">
              <label className="text-sm font-semibold text-forest">What is influencing your space today?</label>
              <div className="flex flex-wrap gap-2">
                {CONTEXT_TAGS.map((tag) => {
                  const isSelected = selectedTags.includes(tag);
                  return (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => toggleTag(tag)}
                      className={`inline-flex items-center space-x-1 px-3 py-1.5 rounded-full text-xs font-medium border transition ${
                        isSelected
                          ? 'bg-sage-600 text-white border-sage-600'
                          : 'bg-paper-50 border-paper-300 text-forest-muted hover:border-forest-muted'
                      }`}
                    >
                      <Tag className="w-3 h-3" />
                      <span>{tag.charAt(0).toUpperCase() + tag.slice(1)}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Optional private check-in note */}
            <div className="space-y-2 pt-2 border-t border-paper-200">
              <label className="text-sm font-semibold text-forest">Private reflection note (optional)</label>
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="What feels present today? Stored privately with your check-in."
                rows={3}
                className="w-full p-3 rounded-xl border border-paper-300 bg-paper-50 text-sm text-forest placeholder:text-stone-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-sage-600/30"
              />
            </div>

            {/* Check-in save actions */}
            <div className="flex items-center justify-between pt-2">
              <div className="text-xs text-forest-muted">
                {checkinSaved && <span className="text-emerald-700 font-medium">✓ Check-in saved</span>}
              </div>
              <div className="flex items-center space-x-3">
                {(selectedMood || selectedEnergy || selectedTags.length > 0 || note) && (
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedMood(null);
                      setSelectedEnergy(null);
                      setSelectedTags([]);
                      setNote('');
                    }}
                    className="text-xs text-forest-muted hover:text-forest underline"
                  >
                    Clear
                  </button>
                )}
                <button
                  type="button"
                  onClick={handleSaveCheckin}
                  disabled={isSavingCheckin}
                  className="px-4 py-2 rounded-xl text-sm font-semibold bg-sage-600 hover:bg-sage-700 text-white transition shadow-sm disabled:opacity-50"
                >
                  {isSavingCheckin ? 'Saving...' : existingCheckinId ? 'Update Check-in' : 'Save Check-in'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: SUGGESTED ACTION & ONE-THING PLAN */}
        <div className="lg:col-span-2 space-y-6">
          {/* SUGGESTED ACTION CARD */}
          <div className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider font-semibold text-sage-600">Practical Next Step</span>
              <span className="text-xs text-forest-muted flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>{suggestedAction?.duration_minutes || 4} min</span>
              </span>
            </div>

            <div>
              <h3 className="text-base font-bold text-forest">{suggestedAction?.title || 'Micro-Step Task Slicing'}</h3>
              <p className="text-xs text-sage-700 bg-sage-50 px-2.5 py-1 rounded-md mt-1 inline-block">
                {suggestedAction?.selection_reason || 'Shown because you selected Study'}
              </p>
            </div>

            {/* Steps preview */}
            <div className="space-y-1.5 text-xs text-forest-muted">
              {suggestedAction?.steps?.map((step: string, idx: number) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span className="w-4 h-4 rounded-full bg-paper-200 text-forest text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                    {idx + 1}
                  </span>
                  <span>{step}</span>
                </div>
              ))}
            </div>

            {suggestedAction?.accessibility_note && (
              <p className="text-[11px] text-forest-muted italic border-t border-paper-200 pt-2">
                Note: {suggestedAction.accessibility_note}
              </p>
            )}

            {/* Outcome feedback buttons */}
            <div className="pt-2 border-t border-paper-200 space-y-2">
              <span className="text-xs font-semibold text-forest">Did you try this activity?</span>
              {feedbackSent ? (
                <p className="text-xs text-emerald-700 font-medium">Thank you for your feedback ({feedbackSent}).</p>
              ) : (
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => handleActionFeedback('helped')}
                    className="p-2 rounded-lg border border-paper-300 bg-paper-50 hover:bg-sage-50 hover:border-sage-300 text-forest font-medium transition"
                  >
                    🌱 It helped
                  </button>
                  <button
                    type="button"
                    onClick={() => handleActionFeedback('about_the_same')}
                    className="p-2 rounded-lg border border-paper-300 bg-paper-50 hover:bg-paper-200 text-forest font-medium transition"
                  >
                    About the same
                  </button>
                  <button
                    type="button"
                    onClick={() => handleActionFeedback('did_not_try')}
                    className="p-2 rounded-lg border border-paper-300 bg-paper-50 hover:bg-paper-200 text-forest font-medium transition"
                  >
                    Did not try
                  </button>
                  <button
                    type="button"
                    onClick={() => handleActionFeedback('skipped')}
                    className="p-2 rounded-lg border border-paper-300 bg-paper-50 hover:bg-paper-200 text-forest-muted transition"
                  >
                    Skip
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* ONE-THING PLAN CARD */}
          <div className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs uppercase tracking-wider font-semibold text-sage-600">Daily One-Thing Plan</span>
                <h3 className="text-base font-bold text-forest">Single Focus for Today</h3>
              </div>
              <Link href="/plan" className="text-xs text-sage-700 hover:underline">
                Full Plan
              </Link>
            </div>

            <p className="text-xs text-forest-muted">
              Choose one gentle priority and up to three small steps. No streaks, scores, or productivity shame.
            </p>

            <input
              type="text"
              value={planFocus}
              onChange={(e) => setPlanFocus(e.target.value)}
              placeholder="e.g. Focus calmly on compiler design revision"
              className="w-full p-2.5 rounded-xl border border-paper-300 bg-paper-50 text-sm text-forest placeholder:text-stone-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-sage-600/30"
            />

            {/* Steps list */}
            <div className="space-y-2">
              {planSteps.map((step, idx) => (
                <div key={step.id || idx} className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => togglePlanStepCompleted(idx)}
                    className={`w-5 h-5 rounded border flex items-center justify-center transition ${
                      step.completed ? 'bg-sage-600 border-sage-600 text-white' : 'border-paper-300 bg-paper-50'
                    }`}
                  >
                    {step.completed && <Check className="w-3.5 h-3.5" />}
                  </button>
                  <input
                    type="text"
                    value={step.text}
                    onChange={(e) => updatePlanStepText(idx, e.target.value)}
                    placeholder={`Small step ${idx + 1}`}
                    className={`flex-1 p-1.5 text-xs rounded border border-paper-200 bg-paper-50 focus:bg-white focus:outline-none ${
                      step.completed ? 'line-through text-stone-400' : 'text-forest'
                    }`}
                  />
                  <button
                    type="button"
                    onClick={() => removePlanStep(idx)}
                    className="text-stone-400 hover:text-rose-600 text-xs px-1"
                  >
                    ×
                  </button>
                </div>
              ))}

              {planSteps.length < 3 && (
                <button
                  type="button"
                  onClick={addPlanStep}
                  className="w-full py-1.5 border border-dashed border-paper-300 rounded-lg text-xs text-sage-700 hover:bg-sage-50 transition flex items-center justify-center space-x-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add small step ({planSteps.length}/3)</span>
                </button>
              )}
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-paper-200">
              <span className="text-xs text-forest-muted">
                {planSaved && <span className="text-emerald-700 font-medium">✓ Plan saved</span>}
              </span>
              <button
                type="button"
                onClick={handleSavePlan}
                disabled={isSavingPlan || !planFocus.trim()}
                className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-sage-600 hover:bg-sage-700 text-white transition disabled:opacity-50"
              >
                {isSavingPlan ? 'Saving...' : 'Save Plan'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

