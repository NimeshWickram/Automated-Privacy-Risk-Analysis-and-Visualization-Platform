import React, { useState } from 'react';
import { Search, Database, Code, Smartphone, Globe, FileText, ShieldAlert } from 'lucide-react';

const sourceIconMap = {
  manifest: <Database size={16} />,
  decompiled_code: <Code size={16} />,
  app_ui: <Smartphone size={16} />,
  network_traffic: <Globe size={16} />,
  privacy_policy: <FileText size={16} />,
  data_safety: <ShieldAlert size={16} />,
};

const sourceLabelMap = {
  manifest: 'Android Manifest',
  decompiled_code: 'Decompiled Code',
  app_ui: 'App UI',
  network_traffic: 'Network Traffic',
  privacy_policy: 'Privacy Policy',
  data_safety: 'Data Safety Declaration',
};

const severityStyles = {
  critical: 'bg-red-500/10 text-red-400 border-red-500/30',
  high: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
  medium: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  info: 'bg-slate-500/10 text-slate-400 border-slate-500/30',
};

export default function EvidenceSourcesTab({ data }) {
  const sources = data?.list || [];
  const [filter, setFilter] = useState('All');

  const uniqueSources = ['All', ...new Set(sources.map(s => s.sourceType))];
  const filteredSources = filter === 'All' ? sources : sources.filter(s => s.sourceType === filter);

  if (!sources.length) {
    return (
      <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-8 text-center backdrop-blur-xl">
        <Search className="w-12 h-12 text-slate-500 mx-auto mb-4 opacity-50" />
        <h3 className="text-lg font-semibold text-slate-300">No Evidence Recorded</h3>
        <p className="text-slate-500 mt-2 max-w-md mx-auto">Multimodal evidence collection was not performed for this application or no relevant privacy evidence was found.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="bg-slate-800/40 border border-slate-700/50 rounded-2xl p-5 sm:p-6 backdrop-blur-xl relative overflow-hidden">
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2 mb-4">
          <Search size={20} className="text-indigo-400" />
          Multimodal Evidence Findings
        </h2>
        
        <div className="flex flex-wrap gap-2 mb-6">
          {uniqueSources.map(source => (
            <button
              key={source}
              onClick={() => setFilter(source)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                filter === source 
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30' 
                  : 'bg-slate-800 border border-slate-700 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
              }`}
            >
              {source === 'All' ? 'All Sources' : sourceLabelMap[source] || source}
              <span className="ml-2 px-1.5 py-0.5 bg-slate-900/50 rounded-md text-[10px]">
                {source === 'All' ? sources.length : sources.filter(s => s.sourceType === source).length}
              </span>
            </button>
          ))}
        </div>

        <div className="space-y-3">
          {filteredSources.map((ev, index) => (
            <div key={ev.id || index} className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-4 transition-all hover:bg-slate-800/80">
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-[10px] font-semibold uppercase tracking-wider">
                      <span className="text-indigo-400">{sourceIconMap[ev.sourceType]}</span>
                      {sourceLabelMap[ev.sourceType] || ev.sourceType}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full border text-[10px] font-semibold uppercase tracking-wider ${severityStyles[ev.severity] || severityStyles.info}`}>
                      {ev.severity}
                    </span>
                  </div>
                  <h3 className="text-sm font-medium text-slate-200">{ev.dataType}</h3>
                  <p className="text-sm text-slate-400 mt-1">{ev.description}</p>
                </div>
                <div className="flex flex-col items-start sm:items-end gap-2 shrink-0">
                   <div className="flex items-center gap-2">
                     <span className="text-[10px] text-slate-500 font-semibold">Evidence Strength Score: {ev.evidenceStrengthScore == null ? 'Not assigned' : ev.evidenceStrengthScore}</span>
                   </div>
                   {ev.fileReference && (
                     <span className="text-xs text-slate-500 font-mono bg-slate-950 px-2 py-1 rounded">
                       {ev.fileReference}{ev.lineNumber ? `:${ev.lineNumber}` : ''}
                     </span>
                   )}
                </div>
              </div>
              
              {ev.rawEvidence && (
                <div className="mt-3 p-2 bg-slate-950 rounded-lg border border-slate-800/50 overflow-x-auto">
                  <code className="text-[11px] text-slate-300 font-mono whitespace-pre-wrap break-all">
                    {ev.rawEvidence}
                  </code>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
