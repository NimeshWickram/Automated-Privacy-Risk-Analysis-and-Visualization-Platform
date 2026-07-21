import { TrendingUp, AlertTriangle, Shield, Lightbulb, Clock, Target } from 'lucide-react';

const severityConfig = {
  Critical: { color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20' },
  High: { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20' },
  Medium: { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
  Low: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20' },
};

const categoryColors = {
  'Personal Data': 'from-rose-500/20 to-rose-500/5',
  'Payment': 'from-purple-500/20 to-purple-500/5',
  'Network': 'from-amber-500/20 to-amber-500/5',
  'Compliance': 'from-indigo-500/20 to-indigo-500/5',
};

export default function RiskPredictions({ data }) {
  if (!data || !data.list || data.list.length === 0) {
    return (
      <div className="bento-card p-8 text-center">
        <Shield className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-white mb-2">No Risk Predictions</h3>
        <p className="text-sm text-slate-400">Risk prediction analysis is not yet available for this app.</p>
      </div>
    );
  }

  // Sort by probability descending
  const sorted = [...data.list].sort((a, b) => b.probability - a.probability);
  const avgProbability = Math.round((sorted.reduce((sum, p) => sum + p.probability, 0) / sorted.length) * 100);
  const avgConfidence = Math.round((sorted.reduce((sum, p) => sum + p.confidence, 0) / sorted.length) * 100);
  const highRisk = sorted.filter(p => p.probability >= 0.3).length;

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <SummaryCard label="Predictions" value={data.total} icon={TrendingUp} color="text-indigo-400" />
        <SummaryCard label="Avg Probability" value={`${avgProbability}%`} icon={Target} color="text-amber-400" />
        <SummaryCard label="Avg Confidence" value={`${avgConfidence}%`} icon={Shield} color="text-purple-400" />
        <SummaryCard label="High Risk" value={highRisk} icon={AlertTriangle} color="text-rose-400" />
      </div>

      {/* Prediction Cards */}
      {sorted.map((pred, i) => {
        const severity = severityConfig[pred.severityIfRealized] || severityConfig.Medium;
        const prob = Math.round(pred.probability * 100);
        const conf = Math.round(pred.confidence * 100);
        const gradient = categoryColors[pred.riskCategory] || 'from-slate-500/20 to-slate-500/5';
        let factors = [];
        try {
          factors = JSON.parse(pred.contributingFactors);
        } catch {
          factors = [];
        }

        return (
          <div key={i} className={`bento-card overflow-hidden bg-gradient-to-br ${gradient}`}>
            {/* Header */}
            <div className="p-5 border-b border-slate-700/30">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <AlertTriangle size={16} className={severity.color} />
                    <h4 className="text-sm font-bold text-white">{pred.predictionType}</h4>
                  </div>
                  <div className="flex flex-wrap items-center gap-2 mt-1">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800/60 text-slate-300 font-medium">
                      {pred.riskCategory}
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${severity.bg} ${severity.color}`}>
                      {pred.severityIfRealized} if realized
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800/60 text-slate-400 flex items-center gap-1">
                      <Clock size={9} /> {pred.timeframe}
                    </span>
                  </div>
                </div>
                {/* Probability gauge */}
                <div className="flex items-center gap-4 shrink-0">
                  <ProbabilityGauge label="Risk" value={prob} color={prob >= 30 ? '#f97316' : '#10b981'} />
                  <ProbabilityGauge label="Confidence" value={conf} color="#818cf8" />
                </div>
              </div>
            </div>

            {/* Body */}
            <div className="p-5 space-y-4">
              <p className="text-sm text-slate-300 leading-relaxed">{pred.description}</p>

              {/* Contributing Factors */}
              {factors.length > 0 && (
                <div>
                  <h5 className="text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-2">Contributing Factors</h5>
                  <div className="flex flex-wrap gap-1.5">
                    {factors.map((factor, j) => (
                      <span key={j} className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/60 text-slate-300 border border-slate-700/30">
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Mitigation */}
              {pred.recommendedMitigation && (
                <div className="bg-emerald-500/5 border border-emerald-500/15 rounded-xl p-3.5">
                  <div className="flex items-start gap-2">
                    <Lightbulb size={14} className="text-emerald-400 mt-0.5 shrink-0" />
                    <div>
                      <h5 className="text-[10px] text-emerald-400 uppercase font-bold tracking-wider mb-1">Recommended Mitigation</h5>
                      <p className="text-xs text-slate-300">{pred.recommendedMitigation}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Historical Basis */}
              {pred.historicalBasis && (
                <p className="text-[11px] text-slate-500 italic">
                  📊 {pred.historicalBasis}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SummaryCard({ label, value, icon: Icon, color }) {
  return (
    <div className="bento-card p-4 text-center">
      <Icon size={18} className={`${color} mx-auto mb-2`} />
      <div className={`text-2xl font-black ${color}`}>{value}</div>
      <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-1">{label}</div>
    </div>
  );
}

function ProbabilityGauge({ label, value, color }) {
  return (
    <div className="text-center">
      <div className="relative w-14 h-14">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 56 56">
          <circle cx="28" cy="28" r="22" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
          <circle
            cx="28" cy="28" r="22" fill="none"
            stroke={color}
            strokeWidth="4" strokeLinecap="round"
            strokeDasharray={`${value * 1.38} 138`}
            className="transition-all duration-700"
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-xs font-black text-white">{value}%</span>
      </div>
      <span className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">{label}</span>
    </div>
  );
}
