'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ShieldCheck, AlertCircle } from 'lucide-react';
import { fetchWithAuth, setStoredToken } from '../lib/api';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmed18Plus, setConfirmed18Plus] = useState(false);
  const [selectedCountry, setSelectedCountry] = useState('IN');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    if (!confirmed18Plus) {
      setErrorMessage('You must confirm you are 18 or older to use this capstone release.');
      return;
    }
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await fetchWithAuth('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          email,
          password,
          confirmed_18_plus: confirmed18Plus,
          selected_country: selectedCountry,
          locale: 'en-IN'
        })
      });

      if (res.ok) {
        const data = await res.json();
        setStoredToken(data.access_token);
        router.push('/');
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || 'Registration failed.');
      }
    } catch {
      setErrorMessage('Could not connect to the registration server.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto my-10 space-y-6">
      {/* Title */}
      <div className="text-center space-y-2">
        <span className="w-12 h-12 rounded-full bg-sage-600 text-white font-serif font-bold text-2xl inline-flex items-center justify-center shadow-sm">
          P
        </span>
        <h1 className="font-serif text-3xl font-bold tracking-tight text-forest">Create your Pause account</h1>
        <p className="text-xs text-forest-muted">
          Private, consent-first reflection companion for university students.
        </p>
      </div>

      {/* Purpose & Limitations Notice */}
      <div className="bg-paper-200 border border-paper-300 rounded-2xl p-4 text-xs text-forest-muted space-y-1.5 leading-relaxed">
        <div className="font-bold text-forest flex items-center space-x-1.5">
          <ShieldCheck className="w-4 h-4 text-sage-600" />
          <span>Before You Begin</span>
        </div>
        <p>
          Pause is a self-reflection tool. It is <strong>not</strong> a diagnostic instrument, therapist, or emergency crisis service. Your writing remains private to you and is never visible to professors or administrators.
        </p>
      </div>

      {/* Registration Form */}
      <form onSubmit={handleRegister} className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-4">
        {errorMessage && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        <div className="space-y-1">
          <label className="text-xs font-semibold text-forest">Email Address</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="student@university.edu"
            className="w-full p-2.5 rounded-xl border border-paper-300 bg-paper-50 text-sm text-forest focus:bg-white focus:outline-none focus:ring-2 focus:ring-sage-600/30"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold text-forest">Password (minimum 8 characters)</label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full p-2.5 rounded-xl border border-paper-300 bg-paper-50 text-sm text-forest focus:bg-white focus:outline-none focus:ring-2 focus:ring-sage-600/30"
          />
        </div>

        <div className="space-y-1">
          <label className="text-xs font-semibold text-forest">Country / Region (for relevant support helplines)</label>
          <select
            value={selectedCountry}
            onChange={(e) => setSelectedCountry(e.target.value)}
            className="w-full p-2.5 rounded-xl border border-paper-300 bg-paper-50 text-sm text-forest focus:bg-white focus:outline-none focus:ring-2 focus:ring-sage-600/30"
          >
            <option value="IN">India (Tele-MANAS, 112, Kiran)</option>
          </select>
          <p className="text-[11px] text-forest-muted">We do not request precise GPS location.</p>
        </div>

        {/* 18+ Confirmation Checkbox */}
        <div className="pt-2 border-t border-paper-200">
          <label className="flex items-start space-x-2.5 cursor-pointer">
            <input
              type="checkbox"
              required
              checked={confirmed18Plus}
              onChange={(e) => setConfirmed18Plus(e.target.checked)}
              className="mt-0.5 rounded text-sage-600 focus:ring-sage-500 w-4 h-4"
            />
            <span className="text-xs text-forest leading-relaxed font-medium">
              I confirm that I am 18 years of age or older (university student capstone release).
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={isLoading || !confirmed18Plus}
          className="w-full py-2.5 rounded-xl text-sm font-semibold bg-sage-600 hover:bg-sage-700 text-white transition shadow-sm disabled:opacity-50 mt-2"
        >
          {isLoading ? 'Creating account...' : 'Create Account'}
        </button>

        <div className="text-center pt-2">
          <p className="text-xs text-forest-muted">
            Already have an account?{' '}
            <Link href="/login" className="font-semibold text-sage-700 hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </form>
    </div>
  );
}

