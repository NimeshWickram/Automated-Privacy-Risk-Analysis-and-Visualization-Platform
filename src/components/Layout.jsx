import { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, Search, GitCompareArrows, Menu, X, UploadCloud } from 'lucide-react';
import UploadModal from './UploadModal';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/analyze', label: 'App Analysis', matchPrefix: '/analyze', icon: Search },
  { to: '/compare', label: 'Compare Apps', icon: GitCompareArrows },
];

export default function Layout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col relative z-0">
      {/* Aurora Background */}
      <div className="aurora-bg"></div>

      {/* Floating Navbar */}
      <div className="fixed top-4 sm:top-6 left-1/2 -translate-x-1/2 z-50 w-[95%] max-w-4xl">
        <header className="floating-nav px-3 py-2 sm:px-4 sm:py-3 flex items-center justify-between">
          
          {/* Logo */}
          <NavLink to="/" className="flex items-center gap-3 shrink-0 group">
            <div className="w-10 h-10 rounded-full bg-slate-900 border border-slate-700/50 flex items-center justify-center shadow-lg shadow-indigo-500/10 group-hover:border-indigo-500/50 transition-colors">
              <Shield size={18} className="text-indigo-400 group-hover:text-indigo-300" />
            </div>
            <div className="hidden sm:block">
              <h1 className="text-sm font-bold text-slate-100 leading-tight tracking-wide">PrivacyGuard</h1>
            </div>
          </NavLink>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1 bg-slate-900/50 p-1.5 rounded-full border border-slate-700/30">
            {navItems.map(({ to, label, matchPrefix, icon: Icon }) => {
              const isActive = matchPrefix ? location.pathname.startsWith(matchPrefix) : location.pathname === to;
              return (
                <NavLink
                  key={to}
                  to={to}
                  className={`pill-link flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold whitespace-nowrap ${
                    isActive ? 'active' : 'text-slate-400'
                  }`}
                >
                  <Icon size={16} className="shrink-0" />
                  <span>{label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Action Button & Mobile Toggle */}
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setIsUploadOpen(true)}
              className="hidden sm:flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-bold bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-400 hover:to-purple-500 text-white shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-all hover:-translate-y-0.5 whitespace-nowrap"
            >
              <UploadCloud size={18} className="shrink-0" />
              <span>Analyze APK</span>
            </button>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 hover:text-white transition-colors"
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </header>

        {/* Mobile Dropdown */}
        {mobileMenuOpen && (
          <div className="absolute top-full left-0 right-0 mt-3 p-2 bento-card flex flex-col gap-1 md:hidden">
            {navItems.map(({ to, label, matchPrefix, icon: Icon }) => {
              const isActive = matchPrefix ? location.pathname.startsWith(matchPrefix) : location.pathname === to;
              return (
                <NavLink
                  key={to}
                  to={to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                    isActive ? 'bg-indigo-500/15 text-indigo-300' : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                  }`}
                >
                  <Icon size={18} />
                  {label}
                </NavLink>
              );
            })}
            <button 
              onClick={() => {
                setMobileMenuOpen(false);
                setIsUploadOpen(true);
              }}
              className="w-full mt-2 flex items-center justify-center gap-2 px-4 py-3 rounded-xl text-sm font-bold bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg"
            >
              <UploadCloud size={18} />
              Analyze APK
            </button>
          </div>
        )}
      </div>

      {/* Main content - Add padding top so it doesn't overlap with floating nav */}
      <main className="flex-1 pt-24 sm:pt-28 pb-10">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="mt-auto py-6 text-center border-t border-slate-800/30">
        <p className="text-xs text-slate-500 font-medium tracking-wide">
          Privacy Risk Analysis Platform — v2.1.0
        </p>
      </footer>

      <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} />
    </div>
  );
}
