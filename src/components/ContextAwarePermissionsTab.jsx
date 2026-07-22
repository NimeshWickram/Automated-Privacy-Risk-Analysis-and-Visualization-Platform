import { ShieldCheck, ShieldAlert, CheckCircle, AlertTriangle, XCircle, Info, Lock, Activity, ArrowRight } from 'lucide-react';

const justificationStyles = {
  'justified': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', icon: CheckCircle },
  'conditional': { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', icon: AlertTriangle },
  'excessive': { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20', icon: XCircle },
};

const riskLevelColors = {
  'low': 'text-emerald-400',
  'medium': 'text-amber-400',
  'high': 'text-orange-400',
  'critical': 'text-rose-400',
};

export default function ContextAwarePermissionsTab({ data }) {
  if (!data || !data.list || data.list.length === 0) {
    return (
      <div className="bento-card p-8 text-center">
        <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-white mb-2">No Permissions Declared</h3>
        <p className="text-sm text-slate-400">This app does not request any Android permissions.</p>
      </div>
    );
  }

  // Calculate some summaries
  const dangerousCount = data.list.filter(p => p.status === 'dangerous').length;
  const excessiveCount = data.list.filter(p => p.educationalJustification === 'excessive').length;
  const sdkAttributedCount = data.list.filter(p => p.sdkAttribution && p.sdkAttribution.length > 0 && p.sdkAttribution !== "[]" && p.sdkAttribution !== "app").length;
  
  const avgNecessity = Math.round(
    data.list.reduce((acc, p) => acc + (p.necessityScore || 0), 0) / data.list.length
  );

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <SummaryCard label="Avg Necessity" value={`${avgNecessity}%`} icon={Activity} color={avgNecessity > 70 ? 'text-emerald-400' : 'text-amber-400'} />
        <SummaryCard label="Dangerous" value={dangerousCount} icon={ShieldAlert} color="text-orange-400" />
        <SummaryCard label="Excessive" value={excessiveCount} icon={XCircle} color="text-rose-400" />
        <SummaryCard label="SDK Driven" value={sdkAttributedCount} icon={AlertTriangle} color="text-purple-400" />
      </div>

      {/* Permissions List */}
      <div className="space-y-4">
        {data.list.map((perm, idx) => {
          const isDangerous = perm.status === 'dangerous';
          const justStyle = justificationStyles[perm.educationalJustification] || justificationStyles['conditional'];
          const JustIcon = justStyle.icon;
          const riskColor = riskLevelColors[perm.privacyRiskLevel] || riskLevelColors['medium'];
          
          let alternativeData = null;
          try {
            if (perm.alternativePermission) {
              alternativeData = JSON.parse(perm.alternativePermission);
            }
          } catch(e) {}

          let sdkArray = [];
          try {
              if (perm.sdkAttribution) {
                  sdkArray = typeof perm.sdkAttribution === 'string' ? JSON.parse(perm.sdkAttribution.replace(/'/g, '"')) : perm.sdkAttribution;
              }
          } catch(e) {
              sdkArray = [perm.sdkAttribution];
          }

          return (
            <div key={idx} className={`bento-card overflow-hidden border-l-4 ${isDangerous ? 'border-l-rose-500' : 'border-l-slate-700'}`}>
              <div className="p-4 sm:p-5">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-4">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <h3 className="text-base sm:text-lg font-bold text-white font-mono break-all sm:break-normal">
                        {perm.name}
                      </h3>
                      {isDangerous && (
                        <span className="text-[10px] px-2 py-0.5 bg-rose-500/20 text-rose-300 rounded-full font-bold uppercase">
                          Dangerous
                        </span>
                      )}
                      <span className="text-[10px] px-2 py-0.5 bg-slate-700 text-slate-300 rounded-full font-medium">
                        {perm.riskCategory}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400">{perm.description}</p>
                  </div>
                  
                  {/* Necessity Score Gauge */}
                  <div className="flex items-center gap-3 bg-slate-900/50 p-2 sm:p-3 rounded-xl border border-slate-700/30 shrink-0">
                    <div className="text-right">
                      <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-0.5">Necessity</div>
                      <div className={`text-xl font-black ${perm.necessityScore > 75 ? 'text-emerald-400' : perm.necessityScore > 40 ? 'text-amber-400' : 'text-rose-400'}`}>
                        {perm.necessityScore}%
                      </div>
                    </div>
                    {/* Tiny visual bar */}
                    <div className="w-1.5 h-10 bg-slate-800 rounded-full overflow-hidden flex flex-col justify-end">
                      <div 
                        className={`w-full rounded-full ${perm.necessityScore > 75 ? 'bg-emerald-500' : perm.necessityScore > 40 ? 'bg-amber-500' : 'bg-rose-500'}`}
                        style={{ height: `${perm.necessityScore}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* Justification & Explanation */}
                <div className={`p-3 rounded-xl border ${justStyle.bg} ${justStyle.border} flex items-start gap-3 mb-4`}>
                  <JustIcon size={18} className={`${justStyle.text} shrink-0 mt-0.5`} />
                  <div>
                    <div className={`text-xs font-bold uppercase tracking-wider mb-1 ${justStyle.text}`}>
                      {(perm.educationalJustification || '').replace('-', ' ')}
                    </div>
                    <p className="text-sm text-slate-300 leading-relaxed">
                      {perm.explanation}
                    </p>
                  </div>
                </div>

                {/* Bottom Metadata Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Left Column */}
                  <div className="space-y-3">
                    {/* SDK Attribution */}
                    {sdkArray && sdkArray.length > 0 && sdkArray[0] && (
                      <div className="flex items-start gap-2">
                        <AlertTriangle size={14} className="text-purple-400 shrink-0 mt-0.5" />
                        <div>
                          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">SDK Attribution</div>
                          <div className="text-sm text-purple-300 font-medium">
                            {Array.isArray(sdkArray) ? sdkArray.join(', ') : sdkArray}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Risk Details */}
                    <div className="flex items-start gap-2">
                      <Lock size={14} className={`${riskColor} shrink-0 mt-0.5`} />
                      <div>
                        <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Privacy Risk</div>
                        <div className={`text-sm font-bold ${riskColor}`}>
                          {perm.privacyRiskLevel} Risk
                        </div>
                        {perm.childRiskMultiplier > 1 && (
                          <div className="text-[11px] text-orange-400 font-medium mt-0.5">
                            {perm.childRiskMultiplier}x Child Safety Multiplier Applied
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Alternative API */}
                  {alternativeData && (
                    <div className="bg-indigo-500/5 border border-indigo-500/20 rounded-xl p-3">
                      <div className="flex items-center gap-1.5 mb-2">
                        <Info size={14} className="text-indigo-400" />
                        <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Privacy-Preserving Alternative</span>
                      </div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-slate-400 line-through decoration-rose-500/50">{perm.name}</span>
                        <ArrowRight size={12} className="text-slate-500" />
                        <span className="text-xs font-mono text-indigo-300 bg-indigo-500/10 px-1.5 py-0.5 rounded">{alternativeData.api}</span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-snug">
                        {alternativeData.explanation}
                      </p>
                    </div>
                  )}
                </div>
                
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function SummaryCard({ label, value, icon: Icon, color }) {
  return (
    <div className="bento-card p-4 text-center">
      <Icon size={18} className={`${color} mx-auto mb-2`} />
      <div className={`text-xl sm:text-2xl font-black ${color}`}>{value}</div>
      <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-1">{label}</div>
    </div>
  );
}
