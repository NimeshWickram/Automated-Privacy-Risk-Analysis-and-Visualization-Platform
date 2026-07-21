import { AlertTriangle, CheckCircle, ExternalLink, Calendar, Users, Database } from 'lucide-react';

const severityConfig = {
  Critical: { color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/20', dotBg: 'bg-rose-400', lineColor: 'bg-rose-500/40' },
  High: { color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20', dotBg: 'bg-orange-400', lineColor: 'bg-orange-500/40' },
  Medium: { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', dotBg: 'bg-amber-400', lineColor: 'bg-amber-500/40' },
  Low: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', dotBg: 'bg-emerald-400', lineColor: 'bg-emerald-500/40' },
};

export default function IncidentTimeline({ data }) {
  if (!data || !data.list || data.list.length === 0) {
    return (
      <div className="bento-card p-8 text-center">
        <CheckCircle className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-white mb-2">No Security Incidents</h3>
        <p className="text-sm text-slate-400">
          No known security incidents have been recorded for this app. This is a positive indicator,
          though it doesn't guarantee the app is immune to future incidents.
        </p>
      </div>
    );
  }

  // Count by severity
  const severityCounts = {};
  data.list.forEach(inc => {
    severityCounts[inc.severity] = (severityCounts[inc.severity] || 0) + 1;
  });

  return (
    <div className="space-y-6">
      {/* Incident Summary */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <SummaryCard label="Total Incidents" value={data.total} color="text-slate-200" />
        <SummaryCard label="Critical/High" value={(severityCounts.Critical || 0) + (severityCounts.High || 0)} color="text-rose-400" />
        <SummaryCard label="Medium" value={severityCounts.Medium || 0} color="text-amber-400" />
        <SummaryCard label="Resolved" value={data.list.filter(i => i.isResolved).length} color="text-emerald-400" />
      </div>

      {/* Timeline */}
      <div className="bento-card p-5">
        <h3 className="text-base font-bold text-white mb-6 flex items-center gap-2">
          <Calendar size={18} className="text-indigo-400" />
          Incident Timeline
        </h3>

        <div className="relative">
          {/* Vertical line */}
          <div className="absolute left-[15px] top-2 bottom-2 w-0.5 bg-slate-700/50" />

          <div className="space-y-6">
            {data.list.map((incident, i) => {
              const severity = severityConfig[incident.severity] || severityConfig.Medium;
              const date = new Date(incident.incidentDate).toLocaleDateString('en-US', {
                year: 'numeric', month: 'short', day: 'numeric'
              });

              return (
                <div key={i} className="relative pl-10">
                  {/* Timeline dot */}
                  <div className={`absolute left-[8px] top-1 w-4 h-4 rounded-full ${severity.dotBg} shadow-lg ring-4 ring-slate-900`} />

                  <div className={`bento-card p-4 ${severity.border} hover:bg-slate-800/30 transition-colors`}>
                    {/* Header */}
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-3">
                      <div className="flex-1">
                        <h4 className="text-sm font-bold text-white">{incident.title}</h4>
                        <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
                          <span>{date}</span>
                          <span className={`px-2 py-0.5 rounded-full font-bold ${severity.bg} ${severity.color}`}>
                            {incident.severity}
                          </span>
                          {incident.isResolved && (
                            <span className="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-300 font-medium flex items-center gap-1">
                              <CheckCircle size={10} /> Resolved
                            </span>
                          )}
                        </div>
                      </div>
                      {incident.cveId && (
                        <span className="text-[10px] px-2 py-1 rounded-lg bg-slate-800/80 text-slate-300 font-mono whitespace-nowrap">
                          {incident.cveId}
                        </span>
                      )}
                    </div>

                    {/* Description */}
                    <p className="text-xs text-slate-400 leading-relaxed mb-3">{incident.description}</p>

                    {/* Details */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      <div className="flex items-center gap-2 text-slate-500">
                        <Users size={12} className="shrink-0" />
                        <span>Affected: <span className="text-slate-300 font-medium">{incident.affectedUsers}</span></span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-500">
                        <Database size={12} className="shrink-0" />
                        <span className="line-clamp-1">Data: <span className="text-slate-300 font-medium">{incident.dataCompromised}</span></span>
                      </div>
                    </div>

                    {/* Resolution */}
                    {incident.resolution && (
                      <div className="mt-3 pt-3 border-t border-slate-700/30">
                        <p className="text-xs text-slate-500">
                          <span className="text-emerald-400/80 font-semibold">Resolution:</span>{' '}
                          <span className="text-slate-400">{incident.resolution}</span>
                        </p>
                      </div>
                    )}

                    {/* Source link */}
                    {incident.sourceUrl && (
                      <a
                        href={incident.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 mt-2 transition-colors"
                      >
                        <ExternalLink size={10} /> View Source
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, color }) {
  return (
    <div className="bento-card p-4 text-center">
      <div className={`text-2xl font-black ${color}`}>{value}</div>
      <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-1">{label}</div>
    </div>
  );
}
