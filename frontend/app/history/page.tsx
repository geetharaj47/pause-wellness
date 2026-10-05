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
  HelpCircle 
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

interface SearchResponse {
  query: string;
  total_retrieved: number;
  relevance_threshold: number;
  abstained: boolean;
  message: string;
  results: SearchResultItem[];
}

export default function HistorySearchPage() {
  const [query, setQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hasConsent, setHasConsent] = useState<boolean | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null);

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
      // offline / demo fallback
      setHasConsent(true);
    }
  }

  async function handleSearch(searchQuery: string = query) {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setErrorMessage(null);
    setSearchResponse(null);

    try {
      const res = await fetchWithAuth('/api/v1/journal/search', {
        method: 'POST',
        body: JSON.stringify({
          query: searchQuery.trim(),
          top_k: 5
        })
      });

      if (res.ok) {
        const data: SearchResponse = await res.json();
        setSearchResponse(data);
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

  async function handleSyncEmbeddings() {
    setIsSyncing(true);
    setSyncStatus(null);
    try {
      const res = await fetchWithAuth('/api/v1/journal/sync-embeddings', {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setSyncStatus(`Successfully indexed ${data.synced_entries} reflections for search.`);
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
    'What helped when I felt exam anxiety?',
    'What did I do when my coding project was overwhelming?',
    'Bedtime routine that helped me sleep',
    'How did I handle screen fatigue?',
    'Studying with a peer'
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="border-b border-paper-300 pb-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-sage-100 text-sage-800 text-xs font-medium mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Milestone 3 · Hybrid Semantic Search</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-forest">
              Ask My History
            </h1>
            <p className="text-sm text-forest-muted mt-1 max-w-2xl">
              Recall what helped you previously across your private reflections using local semantic retrieval. 
              Only your private entries are searched.
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
              <span>Search</span>
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

      {/* Results Section */}
      {searchResponse && (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-forest flex items-center space-x-2">
              <span>Search Results</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-paper-200 text-forest-muted font-normal">
                {searchResponse.total_retrieved} found
              </span>
            </h2>
            <span className="text-xs text-forest-muted">
              Threshold gate: {searchResponse.relevance_threshold}
            </span>
          </div>

          {/* Abstention display */}
          {searchResponse.abstained || searchResponse.results.length === 0 ? (
            <div className="p-8 rounded-2xl bg-paper-50 border border-paper-300 text-center space-y-3">
              <div className="w-12 h-12 rounded-full bg-paper-200 mx-auto flex items-center justify-center text-forest-muted">
                <Search className="w-5 h-5 opacity-60" />
              </div>
              <h3 className="font-serif font-bold text-forest text-base">
                {searchResponse.message}
              </h3>
              <p className="text-xs text-forest-muted max-w-md mx-auto leading-relaxed">
                No past reflections met the minimum relevance threshold ({searchResponse.relevance_threshold}). 
                This protects against presenting false matches or ungrounded associations.
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
          ) : (
            <div className="space-y-4">
              {searchResponse.results.map((item, index) => {
                const relevancePct = Math.round(item.combined_score * 100);
                const isHighMatch = item.combined_score >= 0.55;

                return (
                  <div
                    key={item.entry_id}
                    className="p-5 rounded-2xl bg-white border border-paper-300 shadow-sm hover:shadow transition space-y-3"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <div className="flex items-center space-x-2 text-forest-muted">
                        <Clock className="w-3.5 h-3.5 text-sage-600" />
                        <span className="font-medium">{item.date_formatted}</span>
                      </div>

                      {/* Match Badge */}
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-2 py-0.5 rounded-full font-medium text-xs ${
                            isHighMatch
                              ? 'bg-sage-100 text-sage-800'
                              : 'bg-paper-200 text-forest'
                          }`}
                        >
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
          )}
        </section>
      )}

      {/* Safety & Grounding Commitments */}
      <section className="p-5 rounded-2xl bg-paper-50 border border-paper-300 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-forest-muted flex items-center space-x-1.5">
          <ShieldCheck className="w-4 h-4 text-sage-600" />
          <span>Privacy & Grounding Commitments</span>
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-forest-muted leading-relaxed">
          <div className="space-y-1">
            <span className="font-semibold text-forest block">Strict Tenant Isolation</span>
            <p>
              Your database queries filter by your user ID before semantic vector ranking. No cross-student data can ever leak.
            </p>
          </div>
          <div className="space-y-1">
            <span className="font-semibold text-forest block">Zero External APIs</span>
            <p>
              Vector embeddings are computed locally using <code className="text-forest">all-MiniLM-L6-v2</code>. Your journal never leaves this machine.
            </p>
          </div>
          <div className="space-y-1">
            <span className="font-semibold text-forest block">Honest Abstention</span>
            <p>
              If no entries score above the relevance gate (0.38), Pause displays an honest "not found" instead of hallucinating.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
