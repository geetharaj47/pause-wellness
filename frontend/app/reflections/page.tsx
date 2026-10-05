'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, Calendar, Info, BarChart2, Tag, Compass, Sparkles } from 'lucide-react';
import { fetchWithAuth } from '../lib/api';

export default function ReflectionsPage() {
  const [range, setRange] = useState<'7d' | '30d'>('7d');
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadReflections();
  }, [range]);

  async function loadReflections() {
    setIsLoading(true);
    try {
      const res = await fetchWithAuth(`/api/v1/reflections?range=${range}`);
      if (res.ok) {
        const result = await res.json();
        setData(result);
      }
    } catch {
      // Offline fallback
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-paper-300 pb-4 gap-4">
        <div>
          <span className="text-xs uppercase tracking-wider font-semibold text-sage-600">Looking Back</span>
          <h1 className="font-serif text-3xl font-bold tracking-tight text-forest mt-1">Reflections & Trends</h1>
          <p className="text-sm text-forest-muted mt-1">
            Patterns from your own self-reports. We describe associations without asserting cause or diagnosis.
          </p>
        </div>

        {/* Range Selector */}
        <div className="flex items-center space-x-1 p-1 bg-paper-200 rounded-xl border border-paper-300 shrink-0">
          <button
            onClick={() => setRange('7d')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              range === '7d' ? 'bg-white text-forest shadow-sm' : 'text-forest-muted hover:text-forest'
            }`}
          >
            Past 7 Days
          </button>
          <button
            onClick={() => setRange('30d')}
            className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
              range === '30d' ? 'bg-white text-forest shadow-sm' : 'text-forest-muted hover:text-forest'
            }`}
          >
            Past 30 Days
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-sm text-forest-muted">Summarizing your recorded reflections...</div>
      ) : !data || !data.has_sufficient_data ? (
        <div className="bg-white rounded-2xl border border-paper-300 p-8 text-center space-y-3">
          <TrendingUp className="w-10 h-10 text-sage-600 mx-auto opacity-50" />
          <h3 className="text-base font-bold text-forest">More entries needed for reflections</h3>
          <p className="text-xs text-forest-muted max-w-md mx-auto leading-relaxed">
            Pause requires at least 2 check-ins within the selected window to display honest observations. We never extrapolate or invent a pattern from a single day.
          </p>
          <div className="pt-2">
            <span className="inline-block text-xs bg-paper-100 text-forest-muted px-3 py-1 rounded-full border border-paper-200">
              Recorded entries: {data?.total_checkins || 0}
            </span>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Transparency metadata pill */}
          <div className="flex items-center justify-between text-xs text-forest-muted bg-paper-100 border border-paper-300 px-4 py-2.5 rounded-xl">
            <span>
              Summary based on <strong className="text-forest">{data.total_checkins} check-ins</strong> between {data.date_range_start} and {data.date_range_end}.
            </span>
            {data.average_energy && (
              <span>Average energy: <strong className="text-forest">{data.average_energy} / 5</strong></span>
            )}
          </div>

          {/* Non-causal observations callout */}
          <div className="bg-sage-50/70 border border-sage-200 rounded-2xl p-6 space-y-2">
            <h3 className="text-xs uppercase tracking-wider font-semibold text-sage-800 flex items-center space-x-1.5">
              <Info className="w-3.5 h-3.5 text-sage-600" />
              <span>Descriptive Observations (Non-Causal)</span>
            </h3>
            <div className="space-y-1.5 text-sm text-forest font-serif leading-relaxed">
              {data.non_causal_observations.map((obs: string, idx: number) => (
                <p key={idx}>{obs}</p>
              ))}
            </div>
            <p className="text-[11px] text-forest-muted pt-2 border-t border-sage-200">
              Note: Correlation does not indicate causation. These summaries strictly reflect what you chose to log.
            </p>
          </div>

          {/* Grid: Mood distribution and Context tags */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Mood breakdown */}
            <div className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-forest flex items-center space-x-2">
                <BarChart2 className="w-4 h-4 text-sage-600" />
                <span>Self-Reported Moods</span>
              </h3>
              <div className="space-y-2">
                {data.mood_distribution.map((item: any) => {
                  const pct = Math.round((item.count / data.total_checkins) * 100);
                  return (
                    <div key={item.mood} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="font-medium text-forest">{item.mood}</span>
                        <span className="text-forest-muted">{item.count} ({pct}%)</span>
                      </div>
                      <div className="w-full h-2 bg-paper-200 rounded-full overflow-hidden">
                        <div className="h-full bg-sage-600 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Context tag frequencies */}
            <div className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-forest flex items-center space-x-2">
                <Tag className="w-4 h-4 text-sage-600" />
                <span>Active Life Contexts</span>
              </h3>
              {data.context_summaries.length === 0 ? (
                <p className="text-xs text-forest-muted">No context tags recorded in this window.</p>
              ) : (
                <div className="space-y-2">
                  {data.context_summaries.map((ctx: any) => (
                    <div key={ctx.tag} className="p-2.5 rounded-xl border border-paper-200 bg-paper-50 flex items-center justify-between text-xs">
                      <div>
                        <span className="font-semibold text-forest capitalize">{ctx.tag}</span>
                        <span className="text-forest-muted ml-2">({ctx.count} times logged)</span>
                      </div>
                      <div className="text-[11px] text-forest-muted">
                        {Object.entries(ctx.associated_moods).map(([m, c]) => `${m}: ${c}`).join(' · ')}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Action feedback stats */}
          {data.action_feedback && data.action_feedback.length > 0 && (
            <div className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-4">
              <h3 className="text-sm font-bold text-forest flex items-center space-x-2">
                <Compass className="w-4 h-4 text-sage-600" />
                <span>Reviewed Activity Outcomes</span>
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                {data.action_feedback.map((af: any) => (
                  <div key={af.action_id} className="p-3 rounded-xl border border-paper-200 bg-paper-50 space-y-1">
                    <span className="font-semibold text-forest block">{af.action_title}</span>
                    <div className="flex space-x-3 text-forest-muted text-[11px]">
                      <span>Helped: {af.helped_count}</span>
                      <span>About same: {af.about_same_count}</span>
                      <span>Did not try: {af.did_not_try_count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

