import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Shield, LayoutDashboard, Search, GitCompareArrows, Menu, X, ChevronRight } from 'lucide-react';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyze', label: 'App Analysis', icon: Search },
  { to: '/compare', label: 'Compare Apps', icon: GitCompareArrows },
];

export default function Layout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-xl">
        <div className="responsive-container h-14 sm:h-16 flex items-center justify-between">
          {/* Logo & brand */}
          <NavLink to="/" className="flex items-center gap-2 sm:gap-3 shrink-0">
            <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Shield size={16} className="text-white sm:w-[18px] sm:h-[18px]" />
            </div>
            <div className="hidden xs:block">
              <h1 className="text-sm sm:text-base font-bold text-slate-100 leading-tight">PrivacyGuard</h1>
              <p className="text-[10px] sm:text-xs text-slate-500 leading-tight hidden sm:block">Educational App Analyzer</p>
            </div>
          </NavLink>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-2 px-3 lg:px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'bg-indigo-500/15 text-indigo-300'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon size={16} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Mobile menu toggle */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-200"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

        {/* Mobile nav drawer */}
        {mobileMenuOpen && (
          <>
            <div
              className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden"
              onClick={() => setMobileMenuOpen(false)}
            />
            <nav className="absolute top-full left-0 right-0 bg-slate-900/95 backdrop-blur-xl border-b border-slate-800/60 z-50 md:hidden">
              <div className="responsive-container py-3 space-y-1">
                {navItems.map(({ to, label, icon: Icon }) => (
                  <NavLink
                    key={to}
                    to={to}
                    end={to === '/'}
                    onClick={() => setMobileMenuOpen(false)}
                    className={({ isActive }) =>
                      `flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                        isActive
                          ? 'bg-indigo-500/15 text-indigo-300'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                      }`
                    }
                  >
                    <span className="flex items-center gap-3">
                      <Icon size={18} />
                      {label}
                    </span>
                    <ChevronRight size={16} className="opacity-40" />
                  </NavLink>
                ))}
              </div>
            </nav>
          </>
        )}
      </header>

      {/* Main content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/40 mt-auto">
        <div className="responsive-container py-4 sm:py-6 flex flex-col sm:flex-row items-center justify-between gap-2 sm:gap-3">
          <p className="text-xs sm:text-sm text-slate-500 text-center sm:text-left">
            Privacy Risk Analysis Platform — Final Year Research Project
          </p>
          <p className="text-[10px] sm:text-xs text-slate-600">Analysis Engine v2.1.0</p>
        </div>
      </footer>
    </div>
  );
}
