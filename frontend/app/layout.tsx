'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { ShieldAlert, BookOpen, CheckSquare, Sparkles, TrendingUp, Compass, Lock, LogOut, User as UserIcon, Search } from 'lucide-react';
import './globals.css';
import { getStoredToken, setStoredToken, fetchWithAuth } from './lib/api';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<any>(null);
  const [isLoadingUser, setIsLoadingUser] = useState(true);

  useEffect(() => {
    checkUserSession();
  }, [pathname]);

  async function checkUserSession() {
    const token = getStoredToken();
    if (!token) {
      setCurrentUser(null);
      setIsLoadingUser(false);
      return;
    }
    try {
      const res = await fetchWithAuth('/api/v1/auth/me');
      if (res.ok) {
        const data = await res.json();
        setCurrentUser(data);
      } else {
        setStoredToken(null);
        setCurrentUser(null);
      }
    } catch {
      // Offline or network error
    } finally {
      setIsLoadingUser(false);
    }
  }

  function handleLogout() {
    fetchWithAuth('/api/v1/auth/logout', { method: 'POST' }).catch(() => {});
    setStoredToken(null);
    setCurrentUser(null);
    router.push('/login');
  }

  const navItems = [
    { label: 'Today', href: '/', icon: Sparkles },
    { label: 'My plan', href: '/plan', icon: CheckSquare },
    { label: 'Journal', href: '/journal', icon: BookOpen },
    { label: 'Ask history', href: '/history', icon: Search },
    { label: 'Reflections', href: '/reflections', icon: TrendingUp },
    { label: 'Activities', href: '/actions', icon: Compass },
    { label: 'Get support', href: '/support', icon: ShieldAlert },
    { label: 'Privacy', href: '/privacy', icon: Lock },
  ];

  return (
    <html lang="en">
      <head>
        <title>Pause · Student Self-Reflection Companion</title>
        <meta name="description" content="A consent-first reflection companion for university students." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="min-h-screen bg-paper-100 text-forest flex flex-col antialiased selection:bg-sage-100 selection:text-forest-dark">
        {/* Top Header */}
        <header className="sticky top-0 z-40 bg-paper-50/95 backdrop-blur-md border-b border-paper-300">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center space-x-3">
              <Link href="/" className="flex items-center space-x-2 group">
                <span className="w-8 h-8 rounded-full bg-sage-600 text-white font-serif font-bold text-lg flex items-center justify-center shadow-sm group-hover:bg-sage-700 transition">
                  P
                </span>
                <span className="font-serif text-2xl font-bold tracking-tight text-forest">
                  Pause
                </span>
              </Link>
              <span className="hidden sm:inline-block text-xs font-medium px-2 py-0.5 rounded bg-paper-200 text-forest-muted">
                Student Wellness
              </span>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center space-x-1 lg:space-x-2" aria-label="Main Navigation">
              {navItems.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                      isActive
                        ? 'bg-sage-100 text-sage-800 font-semibold'
                        : 'text-forest-muted hover:text-forest hover:bg-paper-200'
                    }`}
                  >
                    <Icon className="w-4 h-4 opacity-75" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Action / Support Button */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              <Link
                href="/support"
                className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold text-rose-800 bg-rose-50 border border-rose-200 hover:bg-rose-100 transition shadow-sm"
                title="Immediate access to verified support and emergency helplines without needing AI or login"
              >
                <ShieldAlert className="w-4 h-4 text-rose-600" />
                <span>Get support now</span>
              </Link>

              {currentUser ? (
                <div className="flex items-center space-x-2 pl-2 border-l border-paper-300">
                  <span className="hidden lg:inline text-xs text-forest-muted truncate max-w-[130px]" title={currentUser.email}>
                    {currentUser.email}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="p-1.5 rounded text-forest-muted hover:text-forest hover:bg-paper-200 transition"
                    title="Log out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <Link
                  href="/login"
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold bg-sage-600 hover:bg-sage-700 text-white transition shadow-sm"
                >
                  <UserIcon className="w-4 h-4" />
                  <span>Log in</span>
                </Link>
              )}
            </div>
          </div>

          {/* Mobile Navigation bar */}
          <div className="md:hidden flex overflow-x-auto px-4 py-2 border-t border-paper-300 gap-1 scrollbar-none">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-1 whitespace-nowrap px-2.5 py-1 rounded-md text-xs font-medium ${
                    isActive ? 'bg-sage-100 text-sage-800 font-semibold' : 'text-forest-muted'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        </header>

        {/* Non-monitored disclaimer notice */}
        <div className="bg-paper-200 border-b border-paper-300 text-center py-1 px-3 text-[11px] text-forest-muted">
          Pause is a self-reflection tool, not an emergency service or therapist. Pause is not actively monitored and does not contact authorities automatically.
        </div>

        {/* Main Content Area */}
        <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-6 md:py-8">
          {children}
        </main>

        {/* Calm Footer */}
        <footer className="border-t border-paper-300 bg-paper-50 py-6 text-center text-xs text-forest-muted">
          <div className="max-w-4xl mx-auto px-4 space-y-2">
            <p>Pause AI Student Wellness Companion · University Capstone Research Project</p>
            <p className="text-[11px]">Designed for adults 18+ · Respecting the India Digital Personal Data Protection Act framework</p>
          </div>
        </footer>
      </body>
    </html>
  );
}

