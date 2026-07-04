import React from 'react';
import { ShieldCheck, Server, Key, AlertTriangle } from 'lucide-react';
import RiskRadarChart from './RiskRadarChart';

export default function PrintableReport({ app, riskDimensionsData, analysisMetadata, disclosureMismatchData, trackersData, networkData }) {
  const analysisDate = new Date(app.analyzedAt || Date.now()).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  });

  return (
    <div className="bg-white text-black p-8 max-w-[800px] w-[800px] mx-auto font-sans" style={{ minHeight: '1120px' }}>
      {/* Header */}
      <div className="border-b-2 border-slate-200 pb-6 mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-bold text-slate-900 mb-2">{app.name}</h1>
          <p className="text-lg text-slate-600">{app.developer}</p>
          <div className="text-sm text-slate-500 mt-2 flex gap-4">
            <span>Category: {app.category}</span>
            <span>Version: {app.version || "1.0.4"}</span>
            <span>Date: {analysisDate}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-sm text-slate-500 mb-1">Overall Risk Grade</div>
          <div className={`text-4xl font-black ${
            app.riskGrade === 'A' || app.riskGrade === 'B' ? 'text-emerald-600' :
            app.riskGrade === 'C' ? 'text-amber-600' : 'text-red-600'
          }`}>
            {app.riskGrade}
          </div>
          <div className="text-sm font-semibold text-slate-600">Score: {app.riskScore}/100</div>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-slate-800 border-b border-slate-200 pb-2 mb-4">Executive Summary</h2>
        <div className="grid grid-cols-2 gap-6 text-sm">
          <div>
            <p><span className="font-semibold text-slate-700">APK Size:</span> {analysisMetadata.apkSize}</p>
            <p><span className="font-semibold text-slate-700">Target SDK:</span> API {analysisMetadata.targetSdkVersion}</p>
            <p><span className="font-semibold text-slate-700">Risk Level:</span> {app.riskLevel}</p>
          </div>
          <div>
            <p><span className="font-semibold text-slate-700">Trackers Detected:</span> {trackersData.total}</p>
            <p><span className="font-semibold text-slate-700">Insecure Endpoints:</span> {networkData.unencrypted}</p>
            <p><span className="font-semibold text-slate-700">Dangerous Permissions:</span> {app.permissions?.dangerous || 0}</p>
          </div>
        </div>
        <div className="mt-4 text-xs font-mono text-slate-500 bg-slate-50 p-2 rounded border border-slate-100 break-all">
          APK Hash: {analysisMetadata.apkHash}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-8 mb-8">
        {/* Risk Radar */}
        <div>
           <h2 className="text-xl font-bold text-slate-800 border-b border-slate-200 pb-2 mb-4">Risk Radar</h2>
           {/* Wrap in a dark theme container strictly for the radar to keep it looking nice, or adapt it. The radar uses slate colors heavily. */}
           <div className="bg-slate-900 rounded-xl p-2" style={{ height: '300px' }}>
              <RiskRadarChart dimensions={riskDimensionsData} height={260} />
           </div>
        </div>
        
        {/* Disclosure Mismatches */}
        <div>
           <h2 className="text-xl font-bold text-slate-800 border-b border-slate-200 pb-2 mb-4">Disclosure Assessment</h2>
           {disclosureMismatchData.items.length === 0 ? (
             <p className="text-emerald-700 bg-emerald-50 p-3 rounded border border-emerald-200 text-sm">
               ✅ No disclosure mismatches detected between actual app behavior and developer claims.
             </p>
           ) : (
             <div className="space-y-3">
               {disclosureMismatchData.items.map((item, i) => (
                 <div key={i} className="bg-red-50 border border-red-200 p-3 rounded">
                   <div className="flex items-center gap-2 font-semibold text-red-800 text-sm mb-1">
                     <AlertTriangle size={14} /> Mismatch: {item.dataType}
                   </div>
                   <p className="text-xs text-red-700">Claim: {item.playStoreClaim}</p>
                   <p className="text-xs text-slate-700 mt-1">Finding: {item.analysisResult}</p>
                 </div>
               ))}
             </div>
           )}
        </div>
      </div>

      {/* Permissions Analysis */}
      <div>
        <h2 className="text-2xl font-bold text-slate-800 border-b border-slate-200 pb-2 mb-4">Permissions Analysis</h2>
        <div className="grid grid-cols-2 gap-4">
          {app.permissions?.list?.map((perm, i) => (
            <div key={i} className={`p-3 rounded border ${perm.status === 'dangerous' ? 'bg-red-50 border-red-200' : 'bg-slate-50 border-slate-200'}`}>
               <div className="flex justify-between items-start mb-1">
                 <span className={`font-mono text-xs font-semibold ${perm.status === 'dangerous' ? 'text-red-700' : 'text-slate-700'}`}>
                   {perm.name.split('.').pop()}
                 </span>
                 {perm.status === 'dangerous' && (
                   <span className="text-[10px] bg-red-600 text-white px-1.5 py-0.5 rounded font-bold uppercase">Dangerous</span>
                 )}
               </div>
               <p className="text-xs text-slate-600">{perm.description || perm.justification}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
