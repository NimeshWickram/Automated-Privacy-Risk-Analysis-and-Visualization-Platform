import { Shield, ShieldCheck, ShieldX, Lock, Wifi, UserCheck, FileCheck } from 'lucide-react';

const categoryIcons = {
  'Network': Wifi,
  'Authentication': UserCheck,
  'Data Protection': Lock,
  'Compliance': FileCheck,
};

const qualityColors = {
  Good: 'text-emerald-400',
  Partial: 'text-amber-400',
  Poor: 'text-rose-400',
  'N/A': 'text-slate-500',
};

export default function SecurityMechanismsTab({ data }) {
  if (!data || !data.list || data.list.length === 0) {
    return (
      <div className="bento-card p-8 text-center">
        <ShieldX className="w-12 h-12 text-rose-400 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-white mb-2">No Security Data</h3>
        <p className="text-sm text-slate-400">Security mechanism analysis is not available for this app.</p>
      </div>
    );
  }

  const implemented = data.implemented;
  const total = data.total;
  const percentage = Math.round((implemented / total) * 100);

  // Group by category
  const categories = {};
  data.list.forEach(item => {
    if (!categories[item.category]) categories[item.category] = [];
    categories[item.category].push(item);
  });

  return (
    <div className="space-y-6">
      {/* Score Overview */}
      <div className="bento-card p-6 flex flex-col sm:flex-row items-center gap-6">
        <div className="relative w-28 h-28 shrink-0">
          <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
            <circle cx="50" cy="50" r="42" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" />
            <circle
              cx="50" cy="50" r="42" fill="none"
              stroke={percentage >= 80 ? '#10b981' : percentage >= 50 ? '#f59e0b' : '#ef4444'}
              strokeWidth="8" strokeLinecap="round"
              strokeDasharray={`${percentage * 2.64} 264`}
              className="transition-all duration-1000"
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-2xl font-black text-white">{percentage}%</span>
            <span className="text-[9px] text-slate-400 uppercase font-bold tracking-widest">Secure</span>
          </div>
        </div>
        <div>
          <h3 className="text-lg font-bold text-white mb-1">Security Implementation Score</h3>
          <p className="text-sm text-slate-400">
            <span className="text-emerald-400 font-bold">{implemented}</span> of <span className="font-bold text-white">{total}</span> security mechanisms are implemented.
          </p>
          <div className="flex flex-wrap gap-2 mt-3">
            <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 font-medium flex items-center gap-1">
              <ShieldCheck size={12} /> {implemented} Implemented
            </span>
            <span className="text-xs px-2.5 py-1 rounded-full bg-rose-500/15 text-rose-300 font-medium flex items-center gap-1">
              <ShieldX size={12} /> {total - implemented} Missing
            </span>
          </div>
        </div>
      </div>

      {/* Category Breakdown */}
      {Object.entries(categories).map(([category, items]) => {
        const Icon = categoryIcons[category] || Shield;
        const catImplemented = items.filter(m => m.isImplemented).length;
        return (
          <div key={category} className="bento-card overflow-hidden">
            <div className="p-5 border-b border-slate-700/30 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-slate-800/80">
                  <Icon size={18} className="text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{category}</h3>
                  <p className="text-xs text-slate-500">{catImplemented}/{items.length} implemented</p>
                </div>
              </div>
              {/* Mini progress bar */}
              <div className="w-20 h-2 rounded-full bg-slate-800/60 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
                  style={{ width: `${(catImplemented / items.length) * 100}%` }}
                />
              </div>
            </div>

            <div className="divide-y divide-slate-800/30">
              {items.map((mech, i) => (
                <div key={i} className="p-4 hover:bg-slate-800/20 transition-colors">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2.5">
                      {mech.isImplemented ? (
                        <ShieldCheck size={16} className="text-emerald-400 shrink-0" />
                      ) : (
                        <ShieldX size={16} className="text-rose-400 shrink-0" />
                      )}
                      <span className="font-semibold text-sm text-slate-200">{mech.mechanismName}</span>
                    </div>
                    {mech.implementationQuality && mech.implementationQuality !== 'N/A' && (
                      <span className={`text-[10px] font-bold uppercase tracking-wider ${qualityColors[mech.implementationQuality] || 'text-slate-500'}`}>
                        {mech.implementationQuality}
                      </span>
                    )}
                  </div>
                  {mech.details && (
                    <p className="text-xs text-slate-400 ml-[26px]">{mech.details}</p>
                  )}
                  {mech.recommendation && (
                    <p className="text-xs text-amber-400/80 ml-[26px] mt-1 flex items-start gap-1">
                      <span className="shrink-0">💡</span>
                      <span>{mech.recommendation}</span>
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
