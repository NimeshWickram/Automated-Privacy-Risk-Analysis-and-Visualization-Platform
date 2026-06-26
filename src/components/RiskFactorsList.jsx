import React from 'react';
import { MapPin, Megaphone, ShieldOff, Power, FileWarning, Key, Baby, Mic, AlertTriangle } from 'lucide-react';

const iconMap = {
  'map-pin': MapPin, 'megaphone': Megaphone, 'shield-off': ShieldOff, 'power': Power,
  'file-warning': FileWarning, 'key': Key, 'baby': Baby, 'mic': Mic,
};

const severityStyles = {
  critical: { bg: 'bg-red-500/10', border: 'border-red-500/30', icon: 'text-red-400', badge: 'bg-red-500/20 text-red-300' },
  high: { bg: 'bg-orange-500/10', border: 'border-orange-500/30', icon: 'text-orange-400', badge: 'bg-orange-500/20 text-orange-300' },
  medium: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', icon: 'text-amber-400', badge: 'bg-amber-500/20 text-amber-300' },
  low: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', icon: 'text-emerald-400', badge: 'bg-emerald-500/20 text-emerald-300' },
};

export default function RiskFactorsList({ factors }) {
  const criticalCount = factors.filter(f => f.severity === 'critical').length;
  const highCount = factors.filter(f => f.severity === 'high').length;

  return (
    <div className="glass-card p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-3 sm:mb-4 gap-2">
        <div>
          <h3 className="text-base sm:text-lg font-semibold text-slate-200 flex items-center gap-2">
            <AlertTriangle size={18} className="text-amber-400 sm:w-5 sm:h-5" /> Risk Factors Explained
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 mt-0.5 sm:mt-1">Plain-language warnings about privacy concerns</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {criticalCount > 0 && <span className="px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-full text-[10px] sm:text-xs font-medium bg-red-500/20 text-red-300">{criticalCount} Critical</span>}
          {highCount > 0 && <span className="px-2 sm:px-2.5 py-0.5 sm:py-1 rounded-full text-[10px] sm:text-xs font-medium bg-orange-500/20 text-orange-300">{highCount} High</span>}
        </div>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 sm:gap-3">
        {factors.map((factor, i) => {
          const style = severityStyles[factor.severity] || severityStyles.medium;
          const Icon = iconMap[factor.icon] || AlertTriangle;
          return (
            <div
              key={factor.id}
              className={`${style.bg} border ${style.border} rounded-xl p-3 sm:p-4 transition-all duration-300 hover:scale-[1.01] sm:hover:scale-[1.02] hover:shadow-lg`}
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <div className="flex items-start gap-2 sm:gap-3">
                <div className={`p-1.5 sm:p-2 rounded-lg ${style.bg} ${style.icon} shrink-0`}>
                  <Icon size={16} className="sm:w-5 sm:h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap mb-0.5 sm:mb-1">
                    <h4 className="font-semibold text-slate-200 text-xs sm:text-sm">{factor.title}</h4>
                    <span className={`px-1.5 sm:px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-bold uppercase tracking-wider ${style.badge}`}>{factor.severity}</span>
                  </div>
                  <p className="text-xs sm:text-sm text-slate-400 leading-relaxed line-clamp-3 sm:line-clamp-none">{factor.description}</p>
                  <span className="inline-block mt-1.5 sm:mt-2 text-[10px] sm:text-xs text-slate-500 bg-slate-700/50 px-1.5 sm:px-2 py-0.5 rounded-full">{factor.category}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
