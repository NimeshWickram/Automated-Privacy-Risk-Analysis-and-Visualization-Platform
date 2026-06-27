import { useState } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { GitCompareArrows } from 'lucide-react';
import { comparisonApps } from '../data/mockData';

const gradeStyles = {
  A: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  B: 'bg-green-500/15 text-green-400 border-green-500/30',
  C: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  D: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  F: 'bg-red-500/15 text-red-400 border-red-500/30',
};

const radarColors = ['#818cf8', '#f472b6', '#34d399'];

export default function CompareApps() {
  const [selectedApps, setSelectedApps] = useState([0, 1]);

  const apps = selectedApps.map(i => comparisonApps[i]);

  // Build radar data
  const dimensions = ['Permissions', 'Trackers', 'Network', 'Storage', 'Child Safety'];
  const radarData = dimensions.map(dim => {
    const entry = { dimension: dim };
    apps.forEach((app) => {
      entry[app.name] = app.dimensions[dim];
    });
    return entry;
  });

  const toggleApp = (slotIndex, appIndex) => {
    const newSelection = [...selectedApps];
    newSelection[slotIndex] = appIndex;
    setSelectedApps(newSelection);
  };

  const comparisonMetrics = [
    { label: 'Risk Score', key: 'riskScore', format: (v) => `${v}/100`, colorFn: (v) => v > 60 ? 'text-red-400' : v > 40 ? 'text-amber-400' : 'text-emerald-400' },
    { label: 'Grade', key: 'riskGrade', format: (v) => v, isBadge: true },
    { label: 'Total Permissions', key: 'permissions', format: (v) => v.total, colorFn: () => 'text-slate-200' },
    { label: 'Dangerous Permissions', key: 'permissions', format: (v) => v.dangerous, colorFn: (v) => v > 5 ? 'text-red-400' : v > 2 ? 'text-amber-400' : 'text-emerald-400', rawValue: (v) => v.dangerous },
    { label: 'Trackers', key: 'trackers', format: (v) => v, colorFn: (v) => v > 5 ? 'text-red-400' : v > 2 ? 'text-amber-400' : 'text-emerald-400' },
    { label: 'Encrypted Endpoints', key: 'encryptedEndpoints', format: (v) => v, colorFn: (v) => v === '100%' ? 'text-emerald-400' : 'text-amber-400' },
    { label: 'Disclosure Match', key: 'disclosureMatch', format: (v) => v, colorFn: (v) => parseInt(v) > 80 ? 'text-emerald-400' : parseInt(v) > 50 ? 'text-amber-400' : 'text-red-400' },
    { label: 'Child Safety', key: 'childSafety', format: (v) => v, colorFn: (v) => v === 'Compliant' ? 'text-emerald-400' : v === 'Partial' ? 'text-amber-400' : 'text-red-400' },
  ];

  return (
    <div className="responsive-container py-4 sm:py-6 lg:py-8 space-y-4 sm:space-y-6 lg:space-y-8">
      {/* Title */}
      <div className="animate-fade-in-up">
        <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-white flex items-center gap-2 sm:gap-3">
          <GitCompareArrows size={22} className="text-indigo-400 sm:w-7 sm:h-7" />
          <span>Compare <span className="gradient-text">Apps</span></span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1">Side-by-side privacy risk comparison</p>
      </div>

      {/* App selector */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 animate-fade-in-up stagger-1">
        {selectedApps.map((appIdx, slotIdx) => (
          <div key={slotIdx} className="glass-card p-3 sm:p-4">
            <label className="text-[10px] sm:text-xs text-slate-500 font-medium uppercase tracking-wider">App {slotIdx + 1}</label>
            <select
              value={appIdx}
              onChange={(e) => toggleApp(slotIdx, parseInt(e.target.value))}
              className="w-full mt-1.5 px-3 py-2 bg-slate-800/60 border border-slate-700/40 rounded-xl text-xs sm:text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50 transition-colors appearance-none cursor-pointer"
              style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%2394a3b8' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10l-5 5z'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 12px center' }}
            >
              {comparisonApps.map((app, i) => (
                <option key={i} value={i}>{app.name} — {app.developer}</option>
              ))}
            </select>
            <div className="flex items-center gap-2 mt-2">
              <span className={`inline-flex items-center justify-center w-6 h-6 sm:w-7 sm:h-7 rounded-lg border font-bold text-[10px] sm:text-xs ${gradeStyles[comparisonApps[appIdx].riskGrade]}`}>
                {comparisonApps[appIdx].riskGrade}
              </span>
              <span className="text-xs sm:text-sm text-slate-400">{comparisonApps[appIdx].name}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Side-by-side Chart and Table layout on desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 animate-fade-in-up stagger-2">
        {/* Left Column: Radar Chart */}
        <div className="glass-card p-6 lg:col-span-5 flex flex-col justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-slate-200 mb-1">Risk Dimension Comparison</h2>
            <p className="text-xs sm:text-sm text-slate-400 mb-6">Higher values indicate greater privacy risk</p>
          </div>
          <div className="flex-1 flex items-center justify-center">
            <ResponsiveContainer width="100%" height={380}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                <PolarGrid stroke="#334155" strokeDasharray="3 3" />
                <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} />
                <Tooltip content={<CompareTooltip />} />
                {apps.map((app, i) => (
                  <Radar
                    key={app.name}
                    name={app.name}
                    dataKey={app.name}
                    stroke={radarColors[i]}
                    fill={radarColors[i]}
                    fillOpacity={0.15}
                    strokeWidth={2}
                    dot={{ r: 3, fill: radarColors[i] }}
                  />
                ))}
                <Legend wrapperStyle={{ fontSize: '12px', color: '#94a3b8', paddingTop: '10px' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right Column: Detailed comparison table */}
        <div className="glass-card p-6 lg:col-span-7 flex flex-col justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-slate-200 mb-1">Detailed Comparison</h2>
            <p className="text-xs sm:text-sm text-slate-400 mb-6">Side-by-side comparison of specific metrics</p>
          </div>
          
          {/* Desktop table */}
          <div className="hidden sm:block overflow-hidden rounded-xl border border-slate-800/60 bg-slate-900/40 flex-1">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-slate-800/40 border-b border-slate-800/80 text-slate-300">
                  <th className="text-left text-xs font-semibold uppercase tracking-wider py-3.5 px-4 text-slate-400">Metric</th>
                  {apps.map((app, i) => (
                    <th key={i} className="text-center text-xs font-semibold uppercase tracking-wider py-3.5 px-4 text-slate-400">
                      <div className="flex items-center justify-center gap-1.5">
                        <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: radarColors[i] }} />
                        {app.name}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparisonMetrics.map((metric) => (
                  <tr key={metric.label} className="border-b border-slate-800/30 hover:bg-slate-800/20 transition-premium duration-150">
                    <td className="py-3 px-4 text-slate-300 font-semibold text-xs sm:text-sm">{metric.label}</td>
                    {apps.map((app, i) => {
                      const val = app[metric.key];
                      const display = metric.format(val);
                      const rawVal = metric.rawValue ? metric.rawValue(val) : (typeof val === 'object' ? null : val);
                      const colorClass = metric.colorFn ? metric.colorFn(rawVal ?? val) : 'text-slate-200';
                      return (
                        <td key={i} className="py-3 px-4 text-center">
                          {metric.isBadge ? (
                            <span className={`inline-flex items-center justify-center w-8 h-8 rounded-lg border font-bold text-sm shadow-sm ${gradeStyles[display]}`}>
                              {display}
                            </span>
                          ) : (
                            <span className={`font-semibold ${colorClass}`}>{display}</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile stacked comparison */}
          <div className="sm:hidden space-y-2.5">
            {comparisonMetrics.map((metric) => (
              <div key={metric.label} className="p-3 rounded-xl bg-slate-800/20 border border-slate-700/15">
                <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider mb-2">{metric.label}</p>
                <div className="grid grid-cols-2 gap-3">
                  {apps.map((app, i) => {
                    const val = app[metric.key];
                    const display = metric.format(val);
                    const rawVal = metric.rawValue ? metric.rawValue(val) : (typeof val === 'object' ? null : val);
                    const colorClass = metric.colorFn ? metric.colorFn(rawVal ?? val) : 'text-slate-200';
                    return (
                      <div key={i} className="text-center">
                        <p className="text-[10px] text-slate-500 mb-0.5 truncate">{app.name}</p>
                        {metric.isBadge ? (
                          <span className={`inline-flex items-center justify-center w-7 h-7 rounded-lg border font-bold text-xs ${gradeStyles[display]}`}>
                            {display}
                          </span>
                        ) : (
                          <span className={`text-sm font-semibold ${colorClass}`}>{display}</span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </div>
  );
}

function CompareTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-3 py-2 text-sm">
        <p className="text-slate-200 font-semibold mb-1">{label}</p>
        {payload.map((entry, i) => (
          <p key={i} style={{ color: entry.color }} className="text-xs">
            {entry.name}: <span className="font-bold">{entry.value}</span>/100
          </p>
        ))}
      </div>
    );
  }
  return null;
}
