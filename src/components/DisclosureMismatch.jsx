import { useState } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, ChevronDown, ChevronUp } from 'lucide-react';

const severityConfig = {
  critical: { icon: XCircle, bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', badge: 'bg-red-500/20 text-red-400', label: 'Critical' },
  high: { icon: XCircle, bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400', badge: 'bg-orange-500/20 text-orange-400', label: 'High' },
  medium: { icon: AlertTriangle, bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', badge: 'bg-amber-500/20 text-amber-400', label: 'Medium' },
  low: { icon: Info, bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', badge: 'bg-emerald-500/20 text-emerald-400', label: 'Low' },
  info: { icon: Info, bg: 'bg-slate-500/10', border: 'border-slate-500/30', text: 'text-slate-400', badge: 'bg-slate-500/20 text-slate-400', label: 'Info' },
};

function MismatchRow({ item, index }) {
  const [expanded, setExpanded] = useState(false);
  const config = severityConfig[item.severity] || severityConfig.info;
  const Icon = item.isMismatch ? config.icon : CheckCircle;

  return (
    <div
      className={`${config.bg} border ${config.border} rounded-xl p-3 sm:p-4 transition-premium hover:translate-x-0.5 hover:shadow-md cursor-pointer`}
      onClick={() => setExpanded(!expanded)}
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="flex items-start justify-between gap-2 sm:gap-3">
        <div className="flex items-start gap-2 sm:gap-3 flex-1 min-w-0">
          <div className={`mt-0.5 shrink-0 ${item.isMismatch ? config.text : 'text-emerald-400'}`}>
            <Icon size={16} className="sm:w-5 sm:h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
              <h4 className="font-semibold text-slate-200 text-sm">{item.dataType}</h4>
              {item.isMismatch && <span className={`px-1.5 sm:px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-bold uppercase tracking-wider ${config.badge}`}>Mismatch</span>}
              <span className={`px-1.5 sm:px-2 py-0.5 rounded-full text-[9px] sm:text-[10px] font-bold uppercase tracking-wider ${config.badge}`}>{config.label}</span>
            </div>
            <div className="mt-1.5 sm:mt-2 grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3 text-xs sm:text-sm">
              <div>
                <span className="text-slate-500 text-[10px] sm:text-xs uppercase tracking-wider font-semibold">Description:</span>
                <p className="text-slate-300 mt-0.5 leading-relaxed">{item.description}</p>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] sm:text-xs uppercase tracking-wider font-semibold">Mismatch Type:</span>
                <p className={`mt-0.5 ${item.isMismatch ? config.text : 'text-emerald-400'} font-semibold capitalize`}>
                  {item.mismatchType?.replace('_', ' ')}
                </p>
              </div>
            </div>
          </div>
        </div>
        <button className="text-slate-400 hover:text-slate-200 transition-colors p-0.5 sm:p-1 shrink-0">
          {expanded ? <ChevronUp size={16} className="sm:w-[18px] sm:h-[18px]" /> : <ChevronDown size={16} className="sm:w-[18px] sm:h-[18px]" />}
        </button>
      </div>
      {expanded && (
        <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-slate-700/35">
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">{item.explanation}</p>
        </div>
      )}
    </div>
  );
}

export default function DisclosureMismatch({ data }) {
  const items = data?.list || [];
  const mismatches = items.length;
  
  if (items.length === 0) {
    return (
      <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-5 sm:p-6 backdrop-blur-xl">
        <h2 className="text-base sm:text-lg font-bold text-slate-100 flex items-center gap-2 mb-4">
          <CheckCircle size={20} className="text-emerald-400" />
          No Disclosure Mismatches Detected
        </h2>
        <p className="text-sm text-slate-400">
          The application's technical behavior is consistent with its privacy policy and Google Play Data Safety declaration.
        </p>
      </div>
    );
  }

  // Ensure isMismatch is set for styling
  const formattedItems = items.map(item => ({
    ...item,
    isMismatch: true
  }));
  
  // SVG Circle parameters
  const radius = 45;
  const strokeWidth = 8;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (data.overallMatch / 100) * circumference;

  return (
    <div className="glass-card p-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8">
        
        {/* Left Column - Overall Stats Sidebar on Desktop */}
        <div className="lg:col-span-1 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-slate-800/80 pb-6 lg:pb-0 lg:pr-8">
          <div>
            <h3 className="text-base sm:text-lg font-semibold text-slate-200 flex items-center gap-2">
              Data Safety Disclosure Check
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 mt-1.5 leading-relaxed">
              Comparing developer claims against analysis findings. Mismatching claims violate store policies.
            </p>
          </div>
          
          {/* Visual Gauge */}
          <div className="flex flex-row lg:flex-col items-center justify-around lg:justify-center gap-6 my-6">
            <div className="relative w-28 h-28 shrink-0 flex items-center justify-center">
              <svg className="w-28 h-28 transform -rotate-90">
                <circle
                  cx="56"
                  cy="56"
                  r={radius}
                  className="stroke-slate-800/50 fill-transparent"
                  strokeWidth={strokeWidth}
                />
                <circle
                  cx="56"
                  cy="56"
                  r={radius}
                  className={`fill-transparent transition-all duration-1000 ${
                    data.overallMatch < 50 ? 'stroke-red-500' : data.overallMatch < 75 ? 'stroke-amber-500' : 'stroke-emerald-500'
                  }`}
                  strokeWidth={strokeWidth}
                  strokeDasharray={circumference}
                  strokeDashoffset={strokeDashoffset}
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-xl font-black ${
                  data.overallMatch < 50 ? 'text-red-400' : data.overallMatch < 75 ? 'text-amber-400' : 'text-emerald-400'
                }`}>{data.overallMatch}%</span>
                <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">Accuracy</span>
              </div>
            </div>
            
            <div className="space-y-2 lg:w-full">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-800/20 border border-slate-800/40 text-xs font-semibold">
                <span className="text-slate-400">Match Rate</span>
                <span className={data.overallMatch < 50 ? 'text-red-400' : data.overallMatch < 75 ? 'text-amber-400' : 'text-emerald-400'}>
                  {data.overallMatch}%
                </span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-800/20 border border-slate-800/40 text-xs font-semibold">
                <span className="text-slate-400">Mismatches</span>
                <span className="text-red-400">{mismatches} Items</span>
              </div>
            </div>
          </div>

          <div className="hidden lg:block pt-4 border-t border-slate-800/60">
            <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/5 border border-amber-500/10 text-xs text-amber-300 leading-normal">
              <Info size={16} className="shrink-0" />
              <span>Mismatching claims violate Google Play child protection requirements.</span>
            </div>
          </div>
        </div>

        {/* Right Columns - Disclosure List */}
        <div className="lg:col-span-2 space-y-3 sm:space-y-4 relative">
          {formattedItems.map((item, index) => (
            <MismatchRow key={item.id || index} item={item} index={index} />
          ))}
        </div>
        
      </div>
    </div>
  );
}

