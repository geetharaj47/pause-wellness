'use client';

import React, { useState, useEffect } from 'react';
import { BookOpen, Shield, Trash2, Calendar, Sparkles, AlertCircle, Lock } from 'lucide-react';
import { fetchWithAuth, getStoredToken } from '../lib/api';

export default function JournalPage() {
  const [entries, setEntries] = useState<any[]>([]);
  const [newText, setNewText] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

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

              return (
                <div key={entry.id} className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-3">
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

                  {/* Emotion analysis tag container if present */}
                  {entry.emotion_analysis && (
                    <div className="pt-2 border-t border-paper-200 flex items-center space-x-2 text-xs">
                      <span className="text-forest-muted">Tentative tags:</span>
                      {entry.emotion_analysis.labels.map((lbl: string, i: number) => (
                        <span key={i} className="px-2 py-0.5 rounded bg-sage-100 text-sage-800 text-[11px] font-medium">
                          {lbl}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

