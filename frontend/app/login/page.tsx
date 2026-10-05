'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Lock, ArrowRight, Sparkles, AlertCircle } from 'lucide-react';
import { fetchWithAuth, setStoredToken } from '../lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const res = await fetchWithAuth('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });

      if (res.ok) {
        const data = await res.json();
        setStoredToken(data.access_token);
        router.push('/');
      } else {
        const err = await res.json();
        setErrorMessage(err.detail || 'Invalid email or password.');
      }
    } catch {
      setErrorMessage('Could not connect to the authentication server.');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleOneClickDemo() {
    setIsDemoLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetchWithAuth('/api/v1/demo/seed', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setStoredToken(data.access_token);
        router.push('/');
      } else {
        setErrorMessage('Failed to seed demo account.');
      }
    } catch {
      setErrorMessage('Could not connect to the backend server.');
    } finally {
      setIsDemoLoading(false);
    }
  }

  return (
    <div className="max-w-md mx-auto my-10 space-y-6">
      {/* Title */}
      <div className="text-center space-y-2">
        <span className="w-12 h-12 rounded-full bg-sage-600 text-white font-serif font-bold text-2xl inline-flex items-center justify-center shadow-sm">
          P
        </span>
        <h1 className="font-serif text-3xl font-bold tracking-tight text-forest">Sign in to Pause</h1>
        <p className="text-xs text-forest-muted">
          Your private self-reflection companion for university life.
        </p>
      </div>

      {/* Reviewer One-Click Demo Box */}
      <div className="bg-sage-50 border border-sage-200 rounded-2xl p-4 text-center space-y-2">
        <span className="text-[11px] uppercase font-bold text-sage-800 tracking-wider flex items-center justify-center space-x-1">
          <Sparkles className="w-3.5 h-3.5 text-sage-600" />
          <span>Capstone Evaluators & Reviewers</span>
        </span>
        <p className="text-xs text-forest-muted">
          Click below to instantly sign in with synthetic, clearly labeled student reflection data.
        </p>
        <button
          type="button"
          onClick={handleOneClickDemo}
          disabled={isDemoLoading}
          className="w-full py-2.5 px-4 rounded-xl text-xs font-bold bg-sage-600 hover:bg-sage-700 text-white transition shadow-sm disabled:opacity-50"
        >
          {isDemoLoading ? 'Seeding Fictional Demo...' : 'One-Click Reviewer Demo Sign In'}
        </button>
      </div>

      {/* Standard Login Form */}
      <form onSubmit={handleLogin} className="bg-white rounded-2xl border border-paper-300 p-6 shadow-sm space-y-4">
        {errorMessage && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
            <span>{errorMessage}</span>
          </div>
        )}

        <div className="space-y-1">
          <label className="text-xs font-semibold text-forest">University Email</label>
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
          <label className="text-xs font-semibold text-forest">Password</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full p-2.5 rounded-xl border border-paper-300 bg-paper-50 text-sm text-forest focus:bg-white focus:outline-none focus:ring-2 focus:ring-sage-600/30"
          />
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-2.5 rounded-xl text-sm font-semibold bg-forest hover:bg-forest-dark text-white transition shadow-sm disabled:opacity-50 mt-2"
        >
          {isLoading ? 'Signing in...' : 'Sign In'}
        </button>

        <div className="text-center pt-2">
          <p className="text-xs text-forest-muted">
            New here?{' '}
            <Link href="/register" className="font-semibold text-sage-700 hover:underline">
              Create an account
            </Link>
          </p>
        </div>
      </form>
    </div>
  );
}

