import { Shield, Lock, Unlock, Globe } from 'lucide-react';

function TrackerCard({ tracker }) {
  const riskColors = {
    high: { bg: 'bg-red-500/10', border: 'border-red-500/30', dot: 'bg-red-400' },
    medium: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', dot: 'bg-amber-400' },
    low: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', dot: 'bg-emerald-400' },
  };
  const c = riskColors[tracker.risk] || riskColors.medium;
  return (
    <div className={`${c.bg} border ${c.border} rounded-lg p-2.5 sm:p-3 transition-all hover:scale-[1.01] sm:hover:scale-[1.02]`}>
      <div className="flex items-center gap-1.5 sm:gap-2 mb-0.5 sm:mb-1">
        <span className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full ${c.dot}`} />
        <h4 className="text-xs sm:text-sm font-semibold text-slate-200 truncate">{tracker.name}</h4>
      </div>
      <p className="text-[10px] sm:text-xs text-slate-400 line-clamp-2">{tracker.description}</p>
      <span className="inline-block mt-1.5 sm:mt-2 text-[9px] sm:text-[10px] uppercase tracking-wider text-slate-500 bg-slate-700/40 px-1.5 sm:px-2 py-0.5 rounded-full">{tracker.category}</span>
    </div>
  );
}

export default function TrackersAndNetwork({ trackers, network }) {
  const encryptPercent = Math.round((network.encrypted / network.total) * 100);
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Trackers */}
      <div className="glass-card p-4 sm:p-6 flex flex-col justify-between">
        <div>
          <h3 className="text-base sm:text-lg font-semibold text-slate-200 flex items-center gap-2 mb-0.5 sm:mb-1">
            <Shield size={18} className="text-indigo-400 sm:w-5 sm:h-5" /> Third-Party Trackers
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 mb-4">{trackers.total} tracking SDKs detected in this app</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-2.5 max-h-[320px] overflow-y-auto pr-1 flex-1">
          {trackers.list.map((t, i) => <TrackerCard key={i} tracker={t} />)}
        </div>
      </div>

      {/* Network */}
      <div className="glass-card p-4 sm:p-6 flex flex-col justify-between">
        <div>
          <h3 className="text-base sm:text-lg font-semibold text-slate-200 flex items-center gap-2 mb-0.5 sm:mb-1">
            <Globe size={18} className="text-indigo-400 sm:w-5 sm:h-5" /> Network Connections
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 mb-4">{network.total} endpoints contacted during analysis</p>
        </div>

        {/* Encryption stats */}
        <div className="flex items-center gap-3 sm:gap-4 mb-4 p-2.5 sm:p-3 bg-slate-800/50 rounded-xl">
          <div className="flex-1 min-w-0">
            <div className="flex justify-between text-xs sm:text-sm mb-1">
              <span className="text-slate-400 font-medium">Encryption Coverage</span>
              <span className={encryptPercent === 100 ? 'text-emerald-400' : 'text-amber-400'}>{encryptPercent}%</span>
            </div>
            <div className="h-1.5 sm:h-2 bg-slate-700 rounded-full overflow-hidden">
              <div className={`h-full rounded-full animate-progress ${encryptPercent === 100 ? 'bg-emerald-500' : 'bg-amber-500'}`} style={{ width: `${encryptPercent}%` }} />
            </div>
          </div>
          <div className="text-center border-l border-slate-600/50 pl-3 sm:pl-4 shrink-0">
            <div className="text-red-400 font-bold text-lg sm:text-xl">{network.unencrypted}</div>
            <div className="text-[10px] sm:text-xs text-slate-500">Insecure</div>
          </div>
        </div>

        {/* Endpoints list */}
        <div className="space-y-1.5 max-h-[320px] overflow-y-auto pr-1 flex-1">
          {network.endpoints.map((ep, i) => (
            <div key={i} className="flex items-center gap-1.5 sm:gap-2 p-1.5 sm:p-2 rounded-lg bg-slate-800/30 hover:bg-slate-800/60 transition-colors text-xs sm:text-sm">
              {ep.encrypted
                ? <Lock size={12} className="text-emerald-400 shrink-0 sm:w-3.5 sm:h-3.5" />
                : <Unlock size={12} className="text-red-400 shrink-0 sm:w-3.5 sm:h-3.5" />
              }
              <span className="text-slate-300 truncate flex-1 font-mono text-[10px] sm:text-xs">{ep.url}</span>
              <span className="text-[10px] sm:text-xs text-slate-500 shrink-0 hidden xs:inline">{ep.purpose}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

