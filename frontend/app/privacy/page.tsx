'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Lock, Download, Trash2, Shield, AlertTriangle, Check, RefreshCw } from 'lucide-react';
import { fetchWithAuth, setStoredToken } from '../lib/api';

export default function PrivacyPage() {
  const router = useRouter();
  const [consents, setConsents] = useState<any>({
    save_journal: true,
    emotion_analysis: false,
    embeddings_rag: false,
    external_inference: false
  });
  const [isUpdating, setIsUpdating] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);

  useEffect(() => {
    loadConsents();
  }, []);

  async function loadConsents() {
    try {
      const res = await fetchWithAuth('/api/v1/consents');
      if (res.ok) {
        const data = await res.json();
        setConsents({
          save_journal: data.save_journal,
          emotion_analysis: data.emotion_analysis,
          embeddings_rag: data.embeddings_rag,
          external_inference: data.external_inference
        });
      }
    } catch {
      // Offline fallback
    }
  }

  async function handleToggleConsent(purpose: string, currentValue: boolean) {
    const nextVal = !currentValue;
    setIsUpdating(true);
    setStatusMessage(null);

    try {
      const res = await fetchWithAuth('/api/v1/consents', {
        method: 'PUT',
        body: JSON.stringify({
          [purpose]: nextVal,
          delete_existing_embeddings_on_revoke: true
        })
      });

      if (res.ok) {
        const updated = await res.json();
        setConsents({
          save_journal: updated.save_journal,
          emotion_analysis: updated.emotion_analysis,
          embeddings_rag: updated.embeddings_rag,
          external_inference: updated.external_inference
        });
        setStatusMessage('Privacy preferences updated successfully.');
        setTimeout(() => setStatusMessage(null), 3000);
      }
    } catch {
      setStatusMessage('Failed to update consent settings.');
    } finally {
      setIsUpdating(false);
    }
  }

  async function handleExportData() {
    setIsExporting(true);
    try {
      const res = await fetchWithAuth('/api/v1/privacy/export');
      if (res.ok) {
        const data = await res.json();
        const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(data, null, 2))}`;
        const downloadAnchor = document.createElement('a');
        downloadAnchor.setAttribute('href', jsonString);
        downloadAnchor.setAttribute('download', `pause_data_export_${new Date().toISOString().split('T')[0]}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
      }
    } catch {
      alert('Could not export data. Please check your connection.');
    } finally {
      setIsExporting(false);
    }
  }

  async function handleDeleteAccount() {
    const confirmation = prompt(
      'Are you sure you want to permanently delete your account and all data? Type "DELETE" to confirm:'
    );
    if (confirmation !== 'DELETE') return;

    setIsDeletingAccount(true);
    try {
      const res = await fetchWithAuth('/api/v1/account', { method: 'DELETE' });
      if (res.ok) {
        setStoredToken(null);
        alert('Your account and all associated reflections have been permanently erased.');
        router.push('/');
      }
    } catch {
      alert('Could not complete deletion. Please try again.');
    } finally {
      setIsDeletingAccount(false);
    }
  }

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      {/* Header */}
      <div className="border-b border-paper-300 pb-4">
        <span className="text-xs uppercase tracking-wider font-semibold text-sage-600">User Control</span>
        <h1 className="font-serif text-3xl font-bold tracking-tight text-forest mt-1">Privacy & Consent Controls</h1>
        <p className="text-sm text-forest-muted mt-1">
          You have granular control over how your writing is handled. We never silently scan text in the background.
        </p>
      </div>

      {statusMessage && (
        <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 font-medium flex items-center space-x-2">
          <Check className="w-4 h-4 text-emerald-600" />
          <span>{statusMessage}</span>
        </div>
      )}

      {/* Consent Toggles */}
      <div className="bg-white rounded-2xl border border-paper-300 divide-y divide-paper-200 shadow-sm">
        {/* Save Journal */}
        <div className="p-6 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-forest">1. Save Journal Entries</h3>
            <p className="text-xs text-forest-muted leading-relaxed">
              When enabled, your reflection text is encrypted at rest using AES-256 Fernet cipher and stored securely on your behalf.
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleToggleConsent('save_journal', consents.save_journal)}
            className={`w-12 h-6 rounded-full transition-colors relative shrink-0 ${
              consents.save_journal ? 'bg-sage-600' : 'bg-stone-300'
            }`}
          >
            <span
              className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                consents.save_journal ? 'right-1' : 'left-1'
              }`}
            />
          </button>
        </div>

        {/* Emotion Analysis */}
        <div className="p-6 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-forest">2. Emotion Analysis Suggestions</h3>
            <p className="text-xs text-forest-muted leading-relaxed">
              When enabled, you may click "Analyze this note" to request tentative language labels. Analysis runs only on demand, never silently in the background.
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleToggleConsent('emotion_analysis', consents.emotion_analysis)}
            className={`w-12 h-6 rounded-full transition-colors relative shrink-0 ${
              consents.emotion_analysis ? 'bg-sage-600' : 'bg-stone-300'
            }`}
          >
            <span
              className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                consents.emotion_analysis ? 'right-1' : 'left-1'
              }`}
            />
          </button>
        </div>

        {/* Embeddings / RAG */}
        <div className="p-6 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-forest">3. Personal History Semantic Search (Embeddings)</h3>
            <p className="text-xs text-forest-muted leading-relaxed">
              Creates mathematical vector embeddings of your entries to answer questions like "What helped when I had exams?". Revoking this consent immediately purges all existing vector embeddings.
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleToggleConsent('embeddings_rag', consents.embeddings_rag)}
            className={`w-12 h-6 rounded-full transition-colors relative shrink-0 ${
              consents.embeddings_rag ? 'bg-sage-600' : 'bg-stone-300'
            }`}
          >
            <span
              className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                consents.embeddings_rag ? 'right-1' : 'left-1'
              }`}
            />
          </button>
        </div>

        {/* External Inference */}
        <div className="p-6 flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold text-forest">4. External Model Provider Sharing</h3>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-800">
                Default Off
              </span>
            </div>
            <p className="text-xs text-forest-muted leading-relaxed">
              Allows sending text to a third-party hosted model provider. When disabled, all analysis and embeddings run strictly on our secure local servers.
            </p>
          </div>
          <button
            type="button"
            onClick={() => handleToggleConsent('external_inference', consents.external_inference)}
            className={`w-12 h-6 rounded-full transition-colors relative shrink-0 ${
              consents.external_inference ? 'bg-sage-600' : 'bg-stone-300'
            }`}
          >
            <span
              className={`w-4 h-4 bg-white rounded-full absolute top-1 transition-transform ${
                consents.external_inference ? 'right-1' : 'left-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Export & Deletion Section */}
      <div className="bg-white rounded-2xl border border-paper-300 p-6 space-y-4 shadow-sm">
        <h3 className="text-sm font-bold text-forest">Data Portability & Permanent Deletion</h3>
        <p className="text-xs text-forest-muted leading-relaxed">
          Under DPDP principles, your data belongs strictly to you. You can export a machine-readable JSON copy or permanently erase your account at any time.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <button
            type="button"
            onClick={handleExportData}
            disabled={isExporting}
            className="inline-flex items-center justify-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-paper-100 hover:bg-paper-200 border border-paper-300 text-forest transition"
          >
            <Download className="w-4 h-4" />
            <span>{isExporting ? 'Generating JSON...' : 'Export My Data (JSON)'}</span>
          </button>

          <button
            type="button"
            onClick={handleDeleteAccount}
            disabled={isDeletingAccount}
            className="inline-flex items-center justify-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 transition"
          >
            <Trash2 className="w-4 h-4" />
            <span>{isDeletingAccount ? 'Erasing...' : 'Delete Entire Account & All Data'}</span>
          </button>
        </div>
      </div>

      {/* Threat Model & Safeguards */}
      <div className="bg-paper-200 rounded-2xl p-6 space-y-3 border border-paper-300 text-xs text-forest-muted leading-relaxed">
        <h3 className="font-bold text-forest flex items-center space-x-1.5">
          <Shield className="w-4 h-4 text-sage-600" />
          <span>Our Technical Privacy Guarantees</span>
        </h3>
        <ul className="list-disc pl-5 space-y-1">
          <li><strong>No Admin/Faculty Dashboard:</strong> There is no view for professors or staff to read student reflections.</li>
          <li><strong>Zero Identifiable Prompts in Logs:</strong> Raw journal text, prompts, and embeddings are strictly barred from server logs and analytics.</li>
          <li><strong>Tenant Isolation:</strong> Database queries are filtered by authenticated server context before ranking or retrieval.</li>
          <li><strong>No Location Tracking:</strong> We never request precise GPS location.</li>
        </ul>
      </div>
    </div>
  );
}

