'use client';

import React, { useState, useEffect } from 'react';
import { ShieldAlert, Phone, ExternalLink, Heart, CheckCircle2, AlertTriangle, Users } from 'lucide-react';
import { fetchWithAuth } from '../lib/api';

export default function SupportPage() {
  const [resources, setResources] = useState<any[]>([]);
  const [disclaimer, setDisclaimer] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSupportResources();
  }, []);

  async function loadSupportResources() {
    try {
      const res = await fetchWithAuth('/api/v1/support-resources?country=IN');
      if (res.ok) {
        const data = await res.json();
        setResources(data.resources || []);
        setDisclaimer(data.disclaimer || '');
      }
    } catch {
      // Offline fallback
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      {/* Calm Crisis Support Header */}
      <div className="bg-rose-50 border border-rose-200 rounded-3xl p-6 md:p-8 space-y-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-full bg-rose-100 flex items-center justify-center shrink-0">
            <ShieldAlert className="w-6 h-6 text-rose-700" />
          </div>
          <div>
            <span className="text-xs uppercase tracking-wider font-bold text-rose-700">Immediate Support</span>
            <h1 className="font-serif text-2xl md:text-3xl font-bold tracking-tight text-rose-950">
              You are not alone. Human help is available right now.
            </h1>
          </div>
        </div>

        <p className="text-sm text-rose-900 leading-relaxed font-medium">
          If you are feeling overwhelmed, having thoughts of self-harm, or simply need to speak to someone who will listen without judgment, please connect with these verified human support lines.
        </p>

        {/* Clear non-monitored disclaimer */}
        <div className="p-3.5 bg-white/80 rounded-xl border border-rose-200 text-xs text-rose-950 leading-relaxed space-y-1">
          <div className="font-bold flex items-center space-x-1.5 text-rose-800">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>Important Safety Notice</span>
          </div>
          <p>
            {disclaimer || "Pause is a self-reflection companion, NOT an emergency service or clinical crisis intervention. Pause is not actively monitored, does not contact emergency services automatically, and cannot guarantee detection."}
          </p>
        </div>
      </div>

      {/* Verified Support Helplines List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-paper-300 pb-2">
          <h2 className="text-lg font-bold text-forest">Verified Support Lines (India)</h2>
          <span className="text-xs text-forest-muted">Updated & Verified 2026</span>
        </div>

        {isLoading ? (
          <div className="text-center py-8 text-sm text-forest-muted">Loading verified contact numbers...</div>
        ) : (
          <div className="space-y-3">
            {resources.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-2xl border border-paper-300 p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs px-2 py-0.5 rounded font-semibold uppercase tracking-wider bg-sage-100 text-sage-800">
                      {item.type}
                    </span>
                    <span className="text-xs text-forest-muted">Verified: {item.verified_at}</span>
                  </div>
                  <h3 className="text-base font-bold text-forest">{item.display_name}</h3>
                  <p className="text-xs text-forest-muted">{item.language_notes}</p>
                </div>

                <div className="flex items-center space-x-3 shrink-0">
                  <a
                    href={`tel:${item.contact.split('/')[0].trim()}`}
                    className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-bold bg-rose-600 hover:bg-rose-700 text-white shadow-sm transition"
                  >
                    <Phone className="w-4 h-4" />
                    <span>{item.contact}</span>
                  </a>
                  <a
                    href={item.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 rounded-lg text-forest-muted hover:text-forest hover:bg-paper-100 transition"
                    title="Official Govt/Agency Source Link"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Reaching a Trusted Person */}
      <div className="bg-white rounded-2xl border border-paper-300 p-6 space-y-3 shadow-sm">
        <div className="flex items-center space-x-2 text-forest font-bold">
          <Users className="w-5 h-5 text-sage-600" />
          <span>Consider Reaching Out to Someone You Know</span>
        </div>
        <p className="text-xs text-forest-muted leading-relaxed">
          Sometimes talking to a roommate, a trusted friend, a family member, or a campus advisor can bring grounded relief. You do not need to explain everything; simply saying:
        </p>
        <div className="p-3 rounded-xl bg-paper-100 text-xs italic font-serif text-forest border border-paper-200">
          "Hey, I am having a really hard time right now. Are you around to talk or sit with me for a bit?"
        </div>
      </div>
    </div>
  );
}

