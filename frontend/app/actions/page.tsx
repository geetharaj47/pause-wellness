'use client';

import React, { useState, useEffect } from 'react';
import { Compass, Clock, Bookmark, BookmarkCheck, Tag, Info, Check, Shield } from 'lucide-react';
import { fetchWithAuth } from '../lib/api';

const CONTEXT_FILTERS = ['All', 'study', 'sleep', 'stress', 'relationships', 'health'];

export default function ActionsPage() {
  const [actions, setActions] = useState<any[]>([]);
  const [selectedContext, setSelectedContext] = useState('All');
  const [isLoading, setIsLoading] = useState(true);
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadActions();
  }, [selectedContext]);

  async function loadActions() {
    setIsLoading(true);
    try {
      const url = selectedContext === 'All'
        ? '/api/v1/actions'
        : `/api/v1/actions?context=${selectedContext.toLowerCase()}`;
      const res = await fetchWithAuth(url);
      if (res.ok) {
        const data = await res.json();
        setActions(data);
      }
    } catch {
      // Offline fallback
    } finally {
      setIsLoading(false);
    }
  }

  async function toggleSave(actionId: string, currentlySaved: boolean) {
    try {
      if (currentlySaved) {
        await fetchWithAuth(`/api/v1/saved-actions/${actionId}`, { method: 'DELETE' });
      } else {
        await fetchWithAuth('/api/v1/saved-actions', {
          method: 'POST',
          body: JSON.stringify({ action_id: actionId })
        });
      }
      setActions(actions.map(a => a.id === actionId ? { ...a, is_saved: !currentlySaved } : a));
    } catch (e) {
      console.error(e);
    }
  }

  async function recordOutcome(actionId: string, outcome: string) {
    try {
      const todayStr = new Date().toISOString().split('T')[0];
      await fetchWithAuth('/api/v1/action-events', {
        method: 'POST',
        body: JSON.stringify({
          action_id: actionId,
          local_date: todayStr,
          outcome
        })
      });
      setFeedbackSuccess(actionId);
      setTimeout(() => setFeedbackSuccess(null), 3000);
    } catch {
      // Ignore
    }
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="border-b border-paper-300 pb-4">
        <span className="text-xs uppercase tracking-wider font-semibold text-sage-600">Action Library</span>
        <h1 className="font-serif text-3xl font-bold tracking-tight text-forest mt-1">Reviewed Wellness Activities</h1>
        <p className="text-sm text-forest-muted mt-1">
          Evidence-informed, low-friction micro-practices reviewed by the team and academic advisors. Never clinical treatment.
        </p>

        {/* Filter pills */}
        <div className="flex flex-wrap gap-2 mt-4">
          {CONTEXT_FILTERS.map((ctx) => (
            <button
              key={ctx}
              onClick={() => setSelectedContext(ctx)}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition ${
                selectedContext === ctx
                  ? 'bg-sage-600 text-white border-sage-600'
                  : 'bg-white border-paper-300 text-forest hover:bg-paper-200'
              }`}
            >
              {ctx.charAt(0).toUpperCase() + ctx.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Action cards grid */}
      {isLoading ? (
        <div className="text-center py-12 text-sm text-forest-muted">Loading activities catalog...</div>
      ) : actions.length === 0 ? (
        <div className="p-8 text-center text-sm text-forest-muted bg-white rounded-2xl border border-paper-300">
          No activities found for this filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {actions.map((action) => (
            <div
              key={action.id}
              className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <span className="inline-flex items-center space-x-1 text-xs text-forest-muted bg-paper-100 px-2 py-0.5 rounded">
                      <Clock className="w-3 h-3 text-sage-600" />
                      <span>{action.duration_minutes} minutes</span>
                    </span>
                    <h3 className="text-base font-bold text-forest">{action.title}</h3>
                  </div>
                  <button
                    onClick={() => toggleSave(action.id, action.is_saved)}
                    className="p-1.5 rounded-lg text-forest-muted hover:text-sage-700 transition"
                    title={action.is_saved ? 'Remove from saved' : 'Save to favorite list'}
                  >
                    {action.is_saved ? (
                      <BookmarkCheck className="w-5 h-5 text-sage-600" />
                    ) : (
                      <Bookmark className="w-5 h-5" />
                    )}
                  </button>
                </div>

                {/* Steps */}
                <ol className="space-y-2 text-xs text-forest-muted pl-4 list-decimal leading-relaxed">
                  {action.steps.map((st: string, idx: number) => (
                    <li key={idx}>{st}</li>
                  ))}
                </ol>

                {action.accessibility_note && (
                  <p className="text-[11px] text-forest-muted italic border-t border-paper-200 pt-2">
                    Accessibility note: {action.accessibility_note}
                  </p>
                )}
              </div>

              {/* Feedback and review version */}
              <div className="pt-3 border-t border-paper-200 space-y-2">
                <div className="flex items-center justify-between text-[11px] text-forest-muted">
                  <span>Reviewed: {action.review_version}</span>
                  <span className="truncate max-w-[180px]">{action.source}</span>
                </div>

                {feedbackSuccess === action.id ? (
                  <p className="text-xs text-emerald-700 font-medium">Feedback recorded gently.</p>
                ) : (
                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-[11px] text-forest-muted">Tried it?</span>
                    <button
                      onClick={() => recordOutcome(action.id, 'helped')}
                      className="px-2 py-0.5 rounded bg-sage-50 hover:bg-sage-100 text-sage-800 border border-sage-200 text-[11px] font-medium transition"
                    >
                      Helped
                    </button>
                    <button
                      onClick={() => recordOutcome(action.id, 'about_the_same')}
                      className="px-2 py-0.5 rounded bg-paper-100 hover:bg-paper-200 text-forest border border-paper-300 text-[11px] transition"
                    >
                      About the same
                    </button>
                    <button
                      onClick={() => recordOutcome(action.id, 'did_not_try')}
                      className="px-2 py-0.5 rounded bg-paper-100 hover:bg-paper-200 text-forest-muted border border-paper-300 text-[11px] transition"
                    >
                      Did not try
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

