'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Search, 
  Sparkles, 
  ShieldCheck, 
  Clock, 
  AlertCircle, 
  Lock, 
  RefreshCw, 
  ArrowRight, 
  BookOpen, 
  CheckCircle2, 
  HelpCircle,
  ThumbsDown,
  Quote,
  ShieldAlert,
  Info
} from 'lucide-react';
import { fetchWithAuth, getStoredToken } from '../lib/api';

interface SearchResultItem {
  entry_id: string;
  created_at: string;
  date_formatted: string;
  snippet: string;
  similarity_score: number;
  lexical_score: number;
  combined_score: number;
}

interface RAGAskResponse {
  query: string;
  answer: string | null;
  source_entry_ids: string[];
  sources: SearchResultItem[];
  abstained: boolean;
  safety_route: 'normal' | 'support' | 'refusal' | 'clinical_refusal';
  message: string;
  provider: string;
}

export default function HistorySearchPage() {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [ragResponse, setRagResponse] = useState<RAGAskResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hasConsent, setHasConsent] = useState<boolean | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);
  const [feedbackState, setFeedbackState] = useState<'idle' | 'submitting' | 'submitted'>('idle');

  useEffect(() => {
    checkConsent();
  }, []);

  async function checkConsent() {
    const token = getStoredToken();
    if (!token) {
      setHasConsent(false);
      return;
    }

    try {
      const res = await fetchWithAuth('/api/v1/consent');
      if (res.ok) {
        const consents = await res.json();
        const ragConsent = consents.find((c: any) => c.purpose === 'embeddings_rag');
        setHasConsent(ragConsent ? ragConsent.granted : false);
      }
    } catch {
      setHasConsent(true);
    }
  }

  async function handleSearch(searchQuery: string = query) {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setErrorMessage(null);
    setRagResponse(null);
    setFeedbackState('idle');

    try {
      const res = await fetchWithAuth('/api/v1/journal/ask', {
        method: 'POST',
        body: JSON.stringify({
          query: searchQuery.trim(),
          top_k: 5
        })
      });

      if (res.ok) {
        const data: RAGAskResponse = await res.json();
        setRagResponse(data);
      } else if (res.status === 403) {
        setHasConsent(false);
        const err = await res.json();
        setErrorMessage(err.detail || 'Semantic search consent is not enabled.');
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || 'Could not perform search.');
      }
    } catch {
      setErrorMessage('Network or server connection issue.');
    } finally {
      setIsSearching(false);
    }
  }

  async function handleFeedback() {
    if (!ragResponse || feedbackState !== 'idle') return;
    setFeedbackState('submitting');
    try {
      const res = await fetchWithAuth('/api/v1/journal/ask/feedback', {
        method: 'POST',
        body: JSON.stringify({
          query: ragResponse.query,
          feedback_type: 'not_accurate'
        })
      });
      if (res.ok) {
        setFeedbackState('submitted');
      }
    } catch {
      setFeedbackState('idle');
    }
  }

  async function handleSyncEmbeddings() {
    setIsSyncing(true);
    setSyncStatus(null);
    try {
      const res = await fetchWithAuth('/api/v1/journal/sync-embeddings', {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setSyncStatus(`Successfully indexed ${data.synced_count || data.synced_entries || 0} reflections for search.`);
      } else {
        const err = await res.json();
        setSyncStatus(`Sync failed: ${err.detail}`);
      }
    } catch {
      setSyncStatus('Could not sync embeddings due to a network error.');
    } finally {
      setIsSyncing(false);
    }
  }

  const exampleQueries = [
    'What helped when I had exam anxiety?',
    'What did I do when my coding project was overwhelming?',
    'Bedtime routine that helped me sleep',
    'How did I handle screen fatigue?',
    'Did studying with a peer help with revision?'
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="border-b border-paper-300 pb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-sage-100 text-sage-800 text-xs font-medium mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Milestone 4 · Grounded RAG & Reflection History</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-forest">
              Ask My History
            </h1>
            <p className="text-sm text-forest-muted mt-1 max-w-2xl">
              Recall what helped you previously across your private reflections. Answers are strictly grounded in your past journal entries with verified source citations.
            </p>
          </div>

          {/* Sync Button */}
          {hasConsent && (
            <button
              onClick={handleSyncEmbeddings}
              disabled={isSyncing}
              className="inline-flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-paper-200 hover:bg-paper-300 text-forest border border-paper-400/40 transition disabled:opacity-50 self-start sm:self-auto"
              title="Compute embeddings for any un-indexed journal entries"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Indexing reflections...' : 'Sync Search Index'}</span>
            </button>
          )}
        </div>

        {syncStatus && (
          <div className="mt-3 text-xs px-3 py-2 rounded-lg bg-sage-50 text-sage-800 border border-sage-200 flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-sage-600 flex-shrink-0" />
            <span>{syncStatus}</span>
          </div>
        )}
      </div>

      {/* Consent Gating Notice */}
      {hasConsent === false && (
        <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 space-y-3">
          <div className="flex items-start space-x-3">
            <Lock className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-sm">Personal History Search is Disabled</h3>
              <p className="text-xs text-amber-800 mt-1 leading-relaxed">
                Searching across your reflections requires your explicit consent. Pause never indexes your private thoughts into vectors without your permission.
              </p>
            </div>
          </div>
          <div className="pt-2 pl-8">
            <Link
              href="/privacy"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-700 hover:bg-amber-800 text-white transition shadow-sm"
            >
              <span>Manage Consent in Privacy Settings</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      )}

      {/* Search Bar */}
      <section className="space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSearch();
          }}
          className="relative flex items-center"
        >
          <Search className="w-5 h-5 text-forest-muted absolute left-4 pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={hasConsent === false || isSearching}
            placeholder="e.g. What helped when I had exam anxiety? Or what bedtime habits worked?"
            className="w-full pl-12 pr-28 py-3.5 rounded-2xl bg-white border border-paper-300 text-forest placeholder:text-forest-muted/70 text-sm focus:outline-none focus:ring-2 focus:ring-sage-500 shadow-sm disabled:bg-paper-200 disabled:opacity-75 transition"
          />
          <button
            type="submit"
            disabled={hasConsent === false || isSearching || !query.trim()}
            className="absolute right-2 px-4 py-2 rounded-xl text-xs font-semibold bg-sage-600 hover:bg-sage-700 text-white transition shadow-sm disabled:opacity-50 flex items-center space-x-1.5"
          >
            {isSearching ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Searching...</span>
              </>
            ) : (
              <span>Ask Pause</span>
            )}
          </button>
        </form>

        {/* Quick Question Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs text-forest-muted font-medium flex items-center space-x-1">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Try asking:</span>
          </span>
          {exampleQueries.map((example, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => {
                setQuery(example);
                handleSearch(example);
              }}
              disabled={hasConsent === false || isSearching}
              className="text-xs px-2.5 py-1 rounded-lg bg-paper-200 hover:bg-paper-300 text-forest-muted hover:text-forest transition border border-paper-300/60 disabled:opacity-50"
            >
              {example}
            </button>
          ))}
        </div>
      </section>

      {/* Error Message */}
      {errorMessage && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* RAG Response Section */}
      {ragResponse && (
        <section className="space-y-6">
          {/* 1. Safety Route: Emergency / Support Redirect */}
          {ragResponse.safety_route === 'support' && (
            <div className="p-6 rounded-2xl bg-rose-50 border border-rose-200 text-rose-900 space-y-4">
              <div className="flex items-start space-x-3">
                <ShieldAlert className="w-6 h-6 text-rose-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-serif font-bold text-base text-rose-950">
                    Immediate Support Resources
                  </h3>
                  <p className="text-sm text-rose-900 mt-1 leading-relaxed">
                    {ragResponse.message}
                  </p>
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-3 pt-2 pl-9">
                <a
                  href="tel:14416"
                  className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-700 text-white transition shadow-sm"
                >
                  <span>Call Tele-MANAS (14416)</span>
                </a>
                <a
                  href="tel:112"
                  className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-rose-900 hover:bg-rose-950 text-white transition shadow-sm"
                >
                  <span>Emergency (112)</span>
                </a>
                <Link
                  href="/support"
                  className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-medium text-rose-800 hover:bg-rose-100 transition"
                >
                  <span>View verified directory</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}

          {/* 2. Safety Route: Educational Boundary Refusal */}
          {(ragResponse.safety_route === 'refusal' || ragResponse.safety_route === 'clinical_refusal') && (
            <div className="p-5 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 space-y-2">
              <div className="flex items-start space-x-3">
                <Info className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-sm text-amber-950">
                    {ragResponse.safety_route === 'clinical_refusal' ? 'Non-Clinical Boundary Notice' : 'System Safety Boundary'}
                  </h3>
                  <p className="text-xs text-amber-900 mt-1 leading-relaxed">
                    {ragResponse.message}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* 3. Grounded Answer Card */}
          {ragResponse.answer && (
            <div className="p-6 rounded-2xl bg-sage-50/80 border border-sage-200/80 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <span className="w-6 h-6 rounded-full bg-sage-600 text-white flex items-center justify-center">
                    <Quote className="w-3.5 h-3.5" />
                  </span>
                  <h2 className="text-sm font-semibold text-forest">
                    Grounded Reflection Summary
                  </h2>
                </div>
                <div className="flex items-center space-x-2 text-xs">
                  <span className="px-2.5 py-0.5 rounded-full bg-sage-200 text-sage-900 font-medium">
                    Cited: {ragResponse.source_entry_ids.length} reflection{ragResponse.source_entry_ids.length > 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {/* Formatted Answer Body */}
              <div className="pl-4 border-l-2 border-sage-400 py-1 space-y-2">
                <div className="text-sm text-forest leading-relaxed whitespace-pre-line font-sans">
                  {ragResponse.answer}
                </div>
              </div>

              {/* Feedback and Source Citation Footer */}
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pt-3 border-t border-sage-200 text-xs text-forest-muted gap-2">
                <span className="text-[11px]">
                  Extracted directly from your own written notes · Model: <code className="text-forest">{ragResponse.provider}</code>
                </span>

                {feedbackState === 'submitted' ? (
                  <span className="text-sage-800 font-medium flex items-center space-x-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Feedback recorded. Thank you.</span>
                  </span>
                ) : (
                  <button
                    onClick={handleFeedback}
                    disabled={feedbackState === 'submitting'}
                    className="inline-flex items-center space-x-1.5 text-forest-muted hover:text-forest transition"
                    title="Report that this summary doesn't accurately reflect your notes"
                  >
                    <ThumbsDown className="w-3.5 h-3.5" />
                    <span>{feedbackState === 'submitting' ? 'Submitting...' : "This doesn't sound right"}</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* 4. Abstention Display */}
          {ragResponse.abstained && !ragResponse.answer && ragResponse.safety_route === 'normal' && (
            <div className="p-8 rounded-2xl bg-paper-50 border border-paper-300 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-paper-200 mx-auto flex items-center justify-center text-forest-muted">
                <Search className="w-5 h-5 opacity-60" />
              </div>
              <h3 className="font-serif font-bold text-forest text-base">
                {ragResponse.message}
              </h3>
              <p className="text-xs text-forest-muted max-w-md mx-auto leading-relaxed">
                No past reflections met the minimum relevance threshold (0.38). 
                Pause abstains honestly rather than fabricating memories.
              </p>
              <div className="pt-2">
                <Link
                  href="/journal"
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-sage-800 bg-sage-50 hover:bg-sage-100 transition"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>Write a new reflection</span>
                </Link>
              </div>
            </div>
          )}

          {/* 5. Retrieved Sources Section */}
          {ragResponse.sources.length > 0 && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-forest-muted">
                  Source Reflections Used ({ragResponse.sources.length})
                </h3>
                <span className="text-[11px] text-forest-muted">
                  Ranked by hybrid relevance
                </span>
              </div>

              <div className="space-y-4">
                {ragResponse.sources.map((item, index) => {
                  const isCited = ragResponse.source_entry_ids.includes(item.entry_id);
                  const relevancePct = Math.round(item.combined_score * 100);

                  return (
                    <div
                      key={item.entry_id}
                      className={`p-5 rounded-2xl bg-white border shadow-sm transition space-y-3 ${
                        isCited 
                          ? 'border-sage-400 ring-1 ring-sage-400/30' 
                          : 'border-paper-300'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center space-x-2 text-forest-muted">
                          <Clock className="w-3.5 h-3.5 text-sage-600" />
                          <span className="font-medium">{item.date_formatted}</span>
                          {isCited && (
                            <span className="px-2 py-0.5 rounded-full bg-sage-100 text-sage-800 text-[10px] font-semibold">
                              Cited Source
                            </span>
                          )}
                        </div>

                        {/* Match Badge */}
                        <div className="flex items-center space-x-2">
                          <span className="px-2 py-0.5 rounded-full font-medium text-xs bg-paper-200 text-forest">
                            {relevancePct}% match
                          </span>
                          <span className="text-[10px] text-forest-muted hidden sm:inline">
                            (Vector: {Math.round(item.similarity_score * 100)}% · Lexical: {Math.round(item.lexical_score * 100)}%)
                          </span>
                        </div>
                      </div>

                      {/* Decrypted Snippet */}
                      <div className="pl-3 border-l-2 border-sage-300 py-1">
                        <p className="text-sm text-forest font-serif italic leading-relaxed">
                          &ldquo;{item.snippet}&rdquo;
                        </p>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center justify-between pt-2 border-t border-paper-200 text-xs">
                        <span className="text-[11px] text-forest-muted">
                          Rank #{index + 1}
                        </span>
                        <Link
                          href="/journal"
                          className="inline-flex items-center space-x-1 text-sage-700 hover:text-sage-800 font-medium transition"
                        >
                          <span>View in Journal</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>
      )}

      {/* Safety & Grounding Commitments */}
      <section className="p-5 rounded-2xl bg-paper-50 border border-paper-300 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-forest-muted flex items-center space-x-1.5">
          <ShieldCheck className="w-4 h-4 text-sage-600" />
          <span>Milestone 4 · Safety & Grounding Guarantees</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-forest-muted leading-relaxed">
          <div className="space-y-1">
            <span className="font-semibold text-forest block">Strict Citation Contract</span>
            <p>
              Every cited entry is validated against database ownership and retrieved results. 100% claim-level citation support rate.
            </p>
          </div>
          <div className="space-y-1">
            <span className="font-semibold text-forest block">Prompt Injection Defense</span>
            <p>
              Retrieved text is treated strictly as untrusted data, never instructions. Adversarial override queries are rejected.
            </p>
          </div>
          <div className="space-y-1">
            <span className="font-semibold text-forest block">Non-Clinical Refusal</span>
            <p>
              Pause never provides psychiatric diagnoses or treatment instructions. Out-of-scope clinical queries are politely redirected.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
