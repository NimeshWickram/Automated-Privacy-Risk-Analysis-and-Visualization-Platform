import { useState, useEffect, useMemo } from 'react';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { GitCompareArrows, Shield, AlertTriangle, Database, CreditCard, ShieldCheck, ShieldX, Loader2, CheckCircle, XCircle } from 'lucide-react';

const APP_COLORS = ['#818cf8', '#c084fc', '#2dd4bf', '#f59e0b'];

const gradeStyles = {
  A: 'bg-teal-500/15 text-teal-300 border border-teal-500/30',
  B: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
  C: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
  D: 'bg-orange-500/15 text-orange-300 border border-orange-500/30',
  F: 'bg-rose-500/15 text-rose-300 border border-rose-500/30',
};

export default function CompareApps() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);

  useEffect(() => {
    fetch('/api/compare')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch comparison data');
        return res.json();
      })
      .then(data => {
        setApps(data);
        setSelectedIds(data.map(a => a.id));
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const selectedApps = useMemo(() => apps.filter(a => selectedIds.includes(a.id)), [apps, selectedIds]);

  const radarData = useMemo(() => {
    if (selectedApps.length === 0) return [];
    const dimensions = ['Permissions', 'Trackers', 'Data Sharing', 'Payment Risk', 'Incidents'];
    return dimensions.map(dim => {
      const item = { dimension: dim };
      selectedApps.forEach(app => {
        item[app.name] = app.dimensions?.[dim] || 0;
      });
      return item;
    });
  }, [selectedApps]);

  const toggleApp = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="bento-card border-rose-500/20 p-8 flex flex-col items-center max-w-md text-center">
          <AlertTriangle className="text-rose-400 w-12 h-12 mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Failed to load data</h2>
          <p className="text-slate-400 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  // Find the safest app
  const safestApp = selectedApps.length > 0 ? selectedApps.reduce((a, b) => a.riskScore > b.riskScore ? a : b) : null;

  return (
    <div className="responsive-container py-4 sm:py-6 space-y-6">
      {/* Header */}
      <div className="animate-fade-in-up stagger-1">
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white tracking-tight mb-2">
          Compare <span className="gradient-text">Applications</span>
        </h1>
        <p className="text-sm sm:text-base text-slate-400 font-medium">
          Side-by-side privacy and security comparison of educational apps
        </p>
      </div>

      {/* App Selector */}
      <div className="flex flex-wrap gap-2 animate-fade-in-up stagger-2">
        {apps.map((app, i) => (
          <button
            key={app.id}
            onClick={() => toggleApp(app.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all border ${
              selectedIds.includes(app.id)
                ? 'border-indigo-500/40 bg-indigo-500/10 text-white'
                : 'border-slate-700/30 bg-slate-800/30 text-slate-500 hover:text-slate-300'
            }`}
          >
            <span className="w-3 h-3 rounded-full" style={{ backgroundColor: APP_COLORS[i] }} />
            {app.name}
          </button>
        ))}
      </div>

      {selectedApps.length === 0 ? (
        <div className="bento-card p-12 text-center">
          <GitCompareArrows className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <p className="text-slate-400 text-sm">Select at least one app to compare</p>
        </div>
      ) : (
        <>
          {/* Radar Chart */}
          <div className="bento-card p-6 animate-fade-in-up stagger-3">
            <div className="mb-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Shield size={18} className="text-indigo-400" />
                Risk Dimensions Comparison
              </h2>
              <p className="text-xs sm:text-sm text-slate-400 mb-6">Higher values indicate greater privacy risk</p>
            </div>
            <div className="flex-1 flex items-center justify-center">
              <ResponsiveContainer width="100%" height={380} minWidth={0}>
                <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="70%">
                  <PolarGrid stroke="#334155" strokeDasharray="3 3" />
                  <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#475569', fontSize: 10 }} />
                  {selectedApps.map((app, i) => (
                    <Radar
                      key={app.id}
                      name={app.name}
                      dataKey={app.name}
                      stroke={APP_COLORS[apps.findIndex(a => a.id === app.id)]}
                      fill={APP_COLORS[apps.findIndex(a => a.id === app.id)]}
                      fillOpacity={0.15}
                      strokeWidth={2}
                    />
                  ))}
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', borderRadius: '12px' }}
                    itemStyle={{ color: '#e2e8f0', fontSize: '12px' }}
                  />
                  <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '20px' }} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="bento-card overflow-hidden animate-fade-in-up stagger-4">
            <div className="p-5 border-b border-slate-700/30">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <GitCompareArrows size={18} className="text-teal-400" />
                Detailed Comparison
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-slate-900/40 text-xs uppercase text-slate-500 tracking-wider">
                  <tr>
                    <th className="py-3 px-4 text-left font-semibold sticky left-0 bg-slate-900/60 backdrop-blur z-10">Metric</th>
                    {selectedApps.map((app, i) => (
                      <th key={app.id} className="py-3 px-4 text-center font-semibold whitespace-nowrap">
                        <div className="flex items-center justify-center gap-2">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: APP_COLORS[apps.findIndex(a => a.id === app.id)] }} />
                          {app.name}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/30">
                  <CompareRow label="Risk Score" values={selectedApps.map(a => `${a.riskScore}/100`)} />
                  <CompareRow label="Risk Grade" values={selectedApps.map(a => a.riskGrade)} isGrade />
                  <CompareRow label="Target Age" values={selectedApps.map(a => a.targetAge || 'N/A')} />
                  <CompareRow label="Installs" values={selectedApps.map(a => a.installs || 'N/A')} />
                  <CompareRow label="Total Permissions" values={selectedApps.map(a => a.permissions?.total || 0)} />
                  <CompareRow label="Dangerous Permissions" values={selectedApps.map(a => a.permissions?.dangerous || 0)} highlight="high" />
                  <CompareRow label="Trackers" values={selectedApps.map(a => a.trackers || 0)} highlight="high" />
                  <CompareRow label="Personal Data Items" values={selectedApps.map(a => a.personalDataItems || 0)} highlight="high" />
                  <CompareRow label="Shared with 3rd Parties" values={selectedApps.map(a => a.sharedDataItems || 0)} highlight="high" />
                  <CompareRow label="Payment Methods" values={selectedApps.map(a => a.paymentMethods || 0)} />
                  <CompareRow label="Security Incidents" values={selectedApps.map(a => a.incidents || 0)} highlight="high" />
                  <CompareRow label="Security Mechanisms" values={selectedApps.map(a => `${a.securityMechanisms?.implemented || 0}/${a.securityMechanisms?.total || 0}`)} />
                  <CompareRow label="2FA Available" values={selectedApps.map(a => a.has2fa)} isBoolean />
                  <CompareRow label="Compliance" values={selectedApps.map(a => a.complianceStandards || 'None')} />
                  <CompareRow label="Avg Prediction Risk" values={selectedApps.map(a => `${a.avgPredictionRisk || 0}%`)} highlight="high" />
                </tbody>
              </table>
            </div>
          </div>

          {/* Safest App Highlight */}
          {safestApp && (
            <div className="bento-card p-6 border-emerald-500/20 bg-emerald-500/5 animate-fade-in-up stagger-5">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-emerald-500/15">
                  <CheckCircle className="w-6 h-6 text-emerald-400" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-emerald-300">Safest App: {safestApp.name}</h3>
                  <p className="text-sm text-slate-400">
                    With a risk score of {safestApp.riskScore}/100 (Grade {safestApp.riskGrade}), {safestApp.name} demonstrates the best privacy and security practices among the analyzed applications.
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function CompareRow({ label, values, highlight, isGrade, isBoolean }) {
  return (
    <tr className="hover:bg-slate-800/20 transition-colors">
      <td className="py-3 px-4 text-slate-400 font-medium whitespace-nowrap sticky left-0 bg-slate-900/30 backdrop-blur">{label}</td>
      {values.map((val, i) => (
        <td key={i} className="py-3 px-4 text-center">
          {isGrade ? (
            <span className={`inline-flex items-center justify-center w-8 h-8 rounded-lg font-black text-sm ${gradeStyles[val] || ''}`}>{val}</span>
          ) : isBoolean ? (
            val ? <CheckCircle size={16} className="text-emerald-400 mx-auto" /> : <XCircle size={16} className="text-rose-400 mx-auto" />
          ) : (
            <span className={`font-semibold ${
              highlight === 'high' && typeof val === 'number' && val > 0 ? 'text-amber-400' : 'text-slate-200'
            }`}>
              {val}
            </span>
          )}
        </td>
      ))}
    </tr>
  );
}
