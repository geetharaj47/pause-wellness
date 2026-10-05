'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { BookOpen, Shield, Trash2, Calendar, Sparkles, AlertCircle, Lock, Edit3, EyeOff, Check, X } from 'lucide-react';
import { fetchWithAuth, getStoredToken } from '../lib/api';

export default function JournalPage() {
  const [entries, setEntries] = useState<any[]>([]);
  const [newText, setNewText] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Analysis state per entry
  const [analyzingIds, setAnalyzingIds] = useState<string[]>([]);
  const [consentErrorId, setConsentErrorId] = useState<string | null>(null);
  const [editingAnalysisId, setEditingAnalysisId] = useState<string | null>(null);
  const [correctionInput, setCorrectionInput] = useState('');

  useEffect(() => {
    loadJournalEntries();
  }, []);

  async function loadJournalEntries() {
    setIsLoading(true);
    try {
      const res = await fetchWithAuth('/api/v1/journal');
      if (res.ok) {
        const data = await res.json();
        setEntries(data);
      }
    } catch {
      // Offline fallback
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCreateEntry(e: React.FormEvent) {
    e.preventDefault();
    if (!newText.trim()) return;
    setIsSaving(true);
    setErrorMessage(null);

    try {
      const res = await fetchWithAuth('/api/v1/journal', {
        method: 'POST',
        body: JSON.stringify({
          text: newText,
          language: 'en'
        })
      });

      if (res.ok) {
        setNewText('');
        await loadJournalEntries();
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || 'Could not save journal entry.');
      }
    } catch {
      setErrorMessage('Network or server connection issue.');
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDeleteEntry(id: string) {
    if (!confirm('Permanently delete this journal entry? Any associated analysis and embeddings will be immediately erased.')) {
      return;
    }
    try {
      const res = await fetchWithAuth(`/api/v1/journal/${id}`, {
        method: 'DELETE'
      });
      if (res.ok || res.status === 204) {
        setEntries(entries.filter(e => e.id !== id));
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function handleAnalyzeEntry(entryId: string) {
    setAnalyzingIds(prev => [...prev, entryId]);
    setConsentErrorId(null);

    try {
      const res = await fetchWithAuth(`/api/v1/journal/${entryId}/analyze`, {
        method: 'POST'
      });

      if (res.ok) {
        const analysisData = await res.json();
        setEntries(prev => prev.map(entry => {
          if (entry.id === entryId) {
            return {
              ...entry,
              emotion_analysis: analysisData
            };
          }
          return entry;
        }));
      } else if (res.status === 403) {
        setConsentErrorId(entryId);
      } else {
        const err = await res.json();
        alert(err.detail || 'Could not analyze entry at this time.');
      }
    } catch {
      alert('Analysis service is currently offline or unreachable.');
    } finally {
      setAnalyzingIds(prev => prev.filter(id => id !== entryId));
    }
  }

  async function handleSaveCorrection(entryId: string) {
    if (!correctionInput.trim()) return;
    try {
      const res = await fetchWithAuth(`/api/v1/journal/${entryId}/analysis`, {
        method: 'PATCH',
        body: JSON.stringify({
          user_correction: correctionInput.trim()
        })
      });

      if (res.ok) {
        const updated = await res.json();
        setEntries(prev => prev.map(entry => {
          if (entry.id === entryId) {
            return {
              ...entry,
              emotion_analysis: updated
            };
          }
          return entry;
        }));
        setEditingAnalysisId(null);
        setCorrectionInput('');
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function handleHideAnalysis(entryId: string) {
    try {
      const res = await fetchWithAuth(`/api/v1/journal/${entryId}/analysis`, {
        method: 'PATCH',
        body: JSON.stringify({ hidden: true })
      });
      if (res.ok) {
        setEntries(prev => prev.map(entry => {
          if (entry.id === entryId) {
            return { ...entry, emotion_analysis: null };
          }
          return entry;
        }));
      }
    } catch (e) {
      console.error(e);
    }
  }

  async function handleDeleteAnalysis(entryId: string) {
    try {
      const res = await fetchWithAuth(`/api/v1/journal/${entryId}/analysis`, {
        method: 'DELETE'
      });
      if (res.ok || res.status === 204) {
        setEntries(prev => prev.map(entry => {
          if (entry.id === entryId) {
            return { ...entry, emotion_analysis: null };
          }
          return entry;
        }));
      }
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      {/* Header */}
      <div className="border-b border-paper-300 pb-4">
        <span className="text-xs uppercase tracking-wider font-semibold text-sage-600">Private Reflection</span>
        <h1 className="font-serif text-3xl font-bold tracking-tight text-forest mt-1">Journal</h1>
        <p className="text-sm text-forest-muted mt-1">
          A quiet space to write for yourself. No teachers, peers, or administrators can ever view your entries.
        </p>

        {/* Security badge */}
        <div className="mt-3 flex items-center space-x-2 text-xs text-forest-muted bg-paper-200/80 px-3 py-1.5 rounded-lg border border-paper-300 inline-flex">
          <Lock className="w-3.5 h-3.5 text-sage-600" />
          <span>Encrypted at rest with application-level Fernet cipher. Decrypted only for you.</span>
        </div>
      </div>

      {/* Editor Form */}
      <form onSubmit={handleCreateEntry} className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-4">
        <label className="block text-sm font-bold text-forest">
          Write an entry
        </label>
        <textarea
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          placeholder="What went well today? What felt challenging or heavy? Write freely without pressure..."
          rows={5}
          className="w-full p-4 rounded-xl border border-paper-300 bg-paper-50 text-sm text-forest placeholder:text-stone-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-sage-600/30 font-serif leading-relaxed"
        />

        {errorMessage && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        <div className="flex items-center justify-between pt-2">
          <span className="text-xs text-forest-muted">
            English language analysis evaluated in this version.
          </span>
          <button
            type="submit"
            disabled={isSaving || !newText.trim()}
            className="px-5 py-2 rounded-xl text-sm font-semibold bg-sage-600 hover:bg-sage-700 text-white transition shadow-sm disabled:opacity-50"
          >
            {isSaving ? 'Encrypting & Saving...' : 'Save Private Entry'}
          </button>
        </div>
      </form>

      {/* Entry History */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-forest">Your previous entries</h2>
          <span className="text-xs text-forest-muted">{entries.length} recorded</span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-sm text-forest-muted">Loading your reflections...</div>
        ) : entries.length === 0 ? (
          <div className="bg-white rounded-2xl border border-paper-300 p-8 text-center space-y-2">
            <BookOpen className="w-8 h-8 text-forest-muted mx-auto opacity-40" />
            <p className="text-sm font-semibold text-forest">No journal entries recorded yet</p>
            <p className="text-xs text-forest-muted">Write your first reflection above. Entries are completely private.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => {
              const dateFormatted = new Date(entry.created_at).toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                year: 'numeric'
              });
              const isAnalyzing = analyzingIds.includes(entry.id);
              const hasConsentError = consentErrorId === entry.id;
              const isEditing = editingAnalysisId === entry.id;

              return (
                <div key={entry.id} className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-4">
                  <div className="flex items-center justify-between border-b border-paper-200 pb-2">
                    <span className="text-xs font-semibold text-forest-muted flex items-center space-x-1.5">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{dateFormatted}</span>
                    </span>
                    <button
                      onClick={() => handleDeleteEntry(entry.id)}
                      className="text-stone-400 hover:text-rose-600 transition p-1"
                      title="Permanently delete entry"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <p className="text-sm text-forest font-serif leading-relaxed whitespace-pre-wrap">
                    {entry.text}
                  </p>

                  {/* EMOTION ANALYSIS COMPONENT */}
                  <div className="pt-2 border-t border-paper-200">
                    {entry.emotion_analysis ? (
                      <div className="bg-paper-100 rounded-xl p-4 border border-paper-300 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-forest flex items-center space-x-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-sage-600" />
                            <span>Language Reflection Suggestion</span>
                          </span>
                          <div className="flex items-center space-x-2 text-xs">
                            <button
                              type="button"
                              onClick={() => {
                                setEditingAnalysisId(isEditing ? null : entry.id);
                                setCorrectionInput(entry.emotion_analysis.user_correction || '');
                              }}
                              className="text-forest-muted hover:text-forest flex items-center space-x-1"
                              title="Correct or annotate tags"
                            >
                              <Edit3 className="w-3.5 h-3.5" />
                              <span>{isEditing ? 'Cancel' : 'Edit'}</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleHideAnalysis(entry.id)}
                              className="text-forest-muted hover:text-forest flex items-center space-x-1"
                              title="Hide from view"
                            >
                              <EyeOff className="w-3.5 h-3.5" />
                              <span>Hide</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteAnalysis(entry.id)}
                              className="text-stone-400 hover:text-rose-600 text-xs"
                              title="Remove analysis independently"
                            >
                              Remove
                            </button>
                          </div>
                        </div>

                        {/* Labels and Abstention */}
                        {entry.emotion_analysis.labels && entry.emotion_analysis.labels.length > 0 ? (
                          <div className="space-y-2">
                            <div className="flex flex-wrap items-center gap-1.5">
                              {entry.emotion_analysis.labels.map((lbl: string, idx: number) => {
                                const band = entry.emotion_analysis.confidence_bands?.[idx] || 'tentative';
                                return (
                                  <span
                                    key={idx}
                                    className="px-2.5 py-1 rounded-lg bg-sage-100 text-sage-900 border border-sage-300 text-xs font-medium inline-flex items-center space-x-1"
                                  >
                                    <span>{lbl}</span>
                                    <span className="text-[10px] text-sage-700 bg-white/70 px-1 rounded font-normal">
                                      {band}
                                    </span>
                                  </span>
                                );
                              })}
                            </div>

                            {/* Phrase Anchors */}
                            {entry.emotion_analysis.explanation_spans && entry.emotion_analysis.explanation_spans.length > 0 && (
                              <p className="text-[11px] text-forest-muted">
                                Context: {entry.emotion_analysis.explanation_spans.join(', ')}
                              </p>
                            )}

                            <p className="text-xs text-forest-muted italic">
                              "The model tentatively tagged this entry based on phrase patterns. Does that feel right?"
                            </p>
                          </div>
                        ) : (
                          <div className="p-2.5 bg-paper-200/80 rounded-lg text-xs text-forest-muted">
                            <p className="font-semibold text-forest">I’m not sure</p>
                            <p className="mt-0.5">The language in this entry was too subtle or neutral to force an emotion label.</p>
                          </div>
                        )}

                        {/* User Correction Display or Input */}
                        {isEditing ? (
                          <div className="pt-2 border-t border-paper-300 space-y-2">
                            <label className="text-xs font-semibold text-forest">Your correction or note:</label>
                            <div className="flex items-center space-x-2">
                              <input
                                type="text"
                                value={correctionInput}
                                onChange={(e) => setCorrectionInput(e.target.value)}
                                placeholder="e.g. Actually I felt relieved rather than overwhelmed"
                                className="flex-1 p-2 text-xs rounded-lg border border-paper-300 bg-white focus:outline-none focus:ring-1 focus:ring-sage-600"
                              />
                              <button
                                type="button"
                                onClick={() => handleSaveCorrection(entry.id)}
                                className="px-3 py-2 rounded-lg bg-sage-600 text-white text-xs font-semibold hover:bg-sage-700"
                              >
                                Save
                              </button>
                            </div>
                          </div>
                        ) : entry.emotion_analysis.user_correction && (
                          <div className="text-xs text-forest bg-white/70 p-2 rounded-lg border border-paper-300">
                            <strong>Your note:</strong> {entry.emotion_analysis.user_correction}
                          </div>
                        )}

                        <div className="text-[10px] text-forest-muted pt-1 flex items-center justify-between">
                          <span>Model: {entry.emotion_analysis.model_id}</span>
                          <span>Evaluated for English text only</span>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <button
                          type="button"
                          onClick={() => handleAnalyzeEntry(entry.id)}
                          disabled={isAnalyzing}
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border border-paper-300 bg-paper-50 hover:bg-sage-50 hover:border-sage-300 text-forest transition"
                        >
                          <Sparkles className="w-3.5 h-3.5 text-sage-600" />
                          <span>{isAnalyzing ? 'Analyzing note...' : 'Analyze this note'}</span>
                        </button>
                        <span className="text-[11px] text-forest-muted">
                          Runs only on your request.
                        </span>
                      </div>
                    )}

                    {hasConsentError && (
                      <div className="mt-2 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start justify-between">
                        <span>Emotion analysis is currently disabled in your consent settings.</span>
                        <Link href="/privacy" className="font-bold underline hover:text-amber-950 shrink-0 ml-2">
                          Privacy Settings →
                        </Link>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
