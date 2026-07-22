import { useState } from 'react';
import {
  Shield, ShieldAlert, ShieldCheck, ShieldX, AlertTriangle, CheckCircle, XCircle,
  Info, ChevronDown, ChevronUp, Globe, Lock, Fingerprint, Eye, Baby, FileWarning,
  Activity, Server, ExternalLink
} from 'lucide-react';

const impactColors = {
  'low': { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', label: 'Low Risk' },
  'medium': { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', label: 'Medium Risk' },
  'high': { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', label: 'High Risk' },
  'critical': { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20', label: 'Critical Risk' },
};

const categoryIcons = {
  'advertising': ShieldAlert,
  'analytics': Activity,
  'crash-reporting': Shield,
  'push-notifications': Globe,
  'authentication': Lock,
  'social-media': Eye,
  'location': Globe,
  'cloud-storage': Server,
  'ai-chatbot': Info,
  'unknown': AlertTriangle,
};

const categoryLabels = {
  'advertising': 'Advertising',
  'analytics': 'Analytics',
  'crash-reporting': 'Crash Reporting',
  'push-notifications': 'Push Notifications',
  'authentication': 'Authentication',
  'social-media': 'Social Media',
  'location': 'Location Services',
  'cloud-storage': 'Cloud Storage',
  'ai-chatbot': 'AI / Chatbot',
  'unknown': 'Unknown',
};

function SummaryCard({ label, value, icon: Icon, color, subtext }) {
  return (
    <div className="bento-card p-3 sm:p-4 flex flex-col items-center text-center">
      <Icon className={`w-5 h-5 ${color} mb-1.5`} />
      <span className={`text-xl sm:text-2xl font-black ${color}`}>{value}</span>
      <span className="text-[10px] sm:text-xs text-slate-500 font-semibold uppercase tracking-wider mt-0.5">{label}</span>
      {subtext && <span className="text-[9px] text-slate-600 mt-0.5">{subtext}</span>}
    </div>
  );
}

function SDKCard({ sdk }) {
  const [expanded, setExpanded] = useState(false);
  const impact = impactColors[sdk.privacyImpact] || impactColors['medium'];
  const CatIcon = categoryIcons[sdk.category] || AlertTriangle;
  const catLabel = categoryLabels[sdk.category] || sdk.category;

  let dataAccessed = [];
  try { dataAccessed = typeof sdk.dataAccessed === 'string' ? JSON.parse(sdk.dataAccessed) : (sdk.dataAccessed || []); } catch(e) {}
  
  let permissionsConnected = [];
  try { permissionsConnected = typeof sdk.permissionsConnected === 'string' ? JSON.parse(sdk.permissionsConnected) : (sdk.permissionsConnected || []); } catch(e) {}

  let networkDomains = [];
  try { networkDomains = typeof sdk.networkDomains === 'string' ? JSON.parse(sdk.networkDomains) : (sdk.networkDomains || []); } catch(e) {}

  let configIssues = [];
  try { configIssues = typeof sdk.privacyConfigIssues === 'string' ? JSON.parse(sdk.privacyConfigIssues) : (sdk.privacyConfigIssues || []); } catch(e) {}

  const isAdvertising = sdk.category === 'advertising';

  return (
    <div className={`bento-card overflow-hidden border-l-4 transition-all duration-200 ${
      isAdvertising ? 'border-l-rose-500' : 
      sdk.privacyImpact === 'high' ? 'border-l-orange-500' :
      sdk.privacyImpact === 'critical' ? 'border-l-rose-500' :
      sdk.privacyImpact === 'medium' ? 'border-l-amber-500' : 'border-l-emerald-500'
    }`}>
      {/* Header */}
      <div 
        className="p-4 sm:p-5 cursor-pointer hover:bg-slate-800/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-1.5">
              <CatIcon className={`w-4 h-4 ${impact.text} shrink-0`} />
              <h3 className="text-base sm:text-lg font-bold text-white">{sdk.name}</h3>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${impact.bg} ${impact.text}`}>
                {impact.label}
              </span>
              {sdk.disclosureStatus === 'undisclosed' && (
                <span className="text-[10px] px-2 py-0.5 bg-red-500/20 text-red-300 rounded-full font-bold uppercase">
                  Undisclosed
                </span>
              )}
              {sdk.childAppropriate === false && (
                <span className="text-[10px] px-2 py-0.5 bg-purple-500/20 text-purple-300 rounded-full font-bold uppercase flex items-center gap-1">
                  <Baby size={10} /> Not Child-Safe
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>{sdk.provider || 'Unknown Provider'}</span>
              <span>·</span>
              <span className="px-1.5 py-0.5 bg-slate-800 rounded text-slate-400 font-medium">{catLabel}</span>
            </div>
          </div>

          {/* Risk Score Gauge */}
          <div className="flex items-center gap-3 shrink-0">
            <div className="text-right">
              <div className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">SDK Risk</div>
              <div className={`text-xl font-black ${
                sdk.riskScore >= 70 ? 'text-rose-400' : 
                sdk.riskScore >= 45 ? 'text-amber-400' : 'text-emerald-400'
              }`}>
                {sdk.riskScore}
              </div>
            </div>
            <div className="w-4 flex flex-col items-center">
              {expanded ? <ChevronUp size={16} className="text-slate-500" /> : <ChevronDown size={16} className="text-slate-500" />}
            </div>
          </div>
        </div>

        {/* Quick Info Bar */}
        <div className="flex items-center gap-3 mt-3 flex-wrap">
          <div className="flex items-center gap-1">
            {sdk.coppaAvailable ? (
              <CheckCircle size={12} className="text-emerald-400" />
            ) : (
              <XCircle size={12} className="text-rose-400" />
            )}
            <span className="text-[10px] text-slate-400">COPPA</span>
          </div>
          <div className="flex items-center gap-1">
            {sdk.gdprCompliant ? (
              <CheckCircle size={12} className="text-emerald-400" />
            ) : (
              <XCircle size={12} className="text-rose-400" />
            )}
            <span className="text-[10px] text-slate-400">GDPR</span>
          </div>
          <div className="flex items-center gap-1">
            {sdk.isDisclosed ? (
              <CheckCircle size={12} className="text-emerald-400" />
            ) : (
              <XCircle size={12} className="text-rose-400" />
            )}
            <span className="text-[10px] text-slate-400">Data Safety</span>
          </div>
          {sdk.childRiskMultiplier > 1.2 && (
            <span className="text-[10px] px-1.5 py-0.5 bg-purple-500/10 text-purple-400 rounded font-medium">
              Child ×{sdk.childRiskMultiplier}
            </span>
          )}
        </div>
      </div>

      {/* Expanded Details */}
      {expanded && (
        <div className="border-t border-slate-700/30 p-4 sm:p-5 space-y-4 bg-slate-900/30">
          {/* Description */}
          <p className="text-sm text-slate-400">{sdk.description}</p>

          {/* Data Accessed */}
          {dataAccessed.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Fingerprint size={12} /> Data Accessed
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {dataAccessed.map((d, i) => (
                  <span key={i} className="text-xs px-2 py-1 rounded-lg bg-slate-800/60 text-slate-300 border border-slate-700/30">
                    {d}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Permissions Connected */}
          {permissionsConnected.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Lock size={12} /> Permissions Required
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {permissionsConnected.map((p, i) => (
                  <span key={i} className="text-xs px-2 py-1 rounded-lg bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 font-mono">
                    {p}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Network Domains */}
          {networkDomains.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Globe size={12} /> Network Domains Contacted
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {networkDomains.map((d, i) => (
                  <span key={i} className="text-xs px-2 py-1 rounded-lg bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-mono flex items-center gap-1">
                    <ExternalLink size={10} /> {d}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Privacy Config Issues */}
          {configIssues.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <FileWarning size={12} /> Privacy Configuration Issues
              </h4>
              <div className="space-y-1.5">
                {configIssues.map((issue, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm">
                    <AlertTriangle size={14} className="text-amber-400 shrink-0 mt-0.5" />
                    <span className="text-slate-400">{issue}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendation */}
          {sdk.recommendation && (
            <div className="p-3 rounded-xl bg-indigo-500/5 border border-indigo-500/10">
              <h4 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Info size={12} /> Recommendation
              </h4>
              <p className="text-sm text-slate-400">{sdk.recommendation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function SDKIntelligenceTab({ data }) {
  if (!data || !data.list || data.list.length === 0) {
    return (
      <div className="bento-card p-8 text-center">
        <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-white mb-2">No SDKs Detected</h3>
        <p className="text-sm text-slate-400">No third-party SDKs or trackers were identified in this application.</p>
      </div>
    );
  }

  const advertisingCount = data.advertisingCount || data.list.filter(s => s.category === 'advertising').length;
  const undisclosedCount = data.undisclosedCount || data.list.filter(s => s.disclosureStatus === 'undisclosed').length;
  const childInappropriate = data.childInappropriateCount || data.list.filter(s => s.childAppropriate === false).length;
  const avgRisk = Math.round(data.list.reduce((acc, s) => acc + (s.riskScore || 0), 0) / data.list.length);

  // Group by category
  const byCategory = {};
  data.list.forEach(sdk => {
    const cat = sdk.category || 'unknown';
    if (!byCategory[cat]) byCategory[cat] = [];
    byCategory[cat].push(sdk);
  });

  // Sort categories: advertising first, then by risk
  const categoryOrder = ['advertising', 'social-media', 'analytics', 'location', 'ai-chatbot', 'push-notifications', 'authentication', 'cloud-storage', 'crash-reporting', 'unknown'];
  const sortedCategories = Object.keys(byCategory).sort((a, b) => {
    const aIdx = categoryOrder.indexOf(a);
    const bIdx = categoryOrder.indexOf(b);
    return (aIdx === -1 ? 99 : aIdx) - (bIdx === -1 ? 99 : bIdx);
  });

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <SummaryCard
          label="Total SDKs" value={data.total} icon={Shield}
          color={data.total > 4 ? 'text-amber-400' : 'text-emerald-400'}
        />
        <SummaryCard
          label="Advertising" value={advertisingCount} icon={ShieldAlert}
          color={advertisingCount > 0 ? 'text-rose-400' : 'text-emerald-400'}
        />
        <SummaryCard
          label="Undisclosed" value={undisclosedCount} icon={ShieldX}
          color={undisclosedCount > 0 ? 'text-orange-400' : 'text-emerald-400'}
        />
        <SummaryCard
          label="Avg Risk" value={avgRisk} icon={Activity}
          color={avgRisk >= 60 ? 'text-rose-400' : avgRisk >= 35 ? 'text-amber-400' : 'text-emerald-400'}
          subtext="/100"
        />
      </div>

      {/* Child Inappropriateness Warning */}
      {childInappropriate > 0 && (
        <div className="bento-card p-4 border border-purple-500/20 bg-purple-500/5">
          <div className="flex items-start gap-3">
            <Baby className="w-5 h-5 text-purple-400 shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-purple-300 mb-1">Child Safety Concern</h4>
              <p className="text-sm text-slate-400">
                {childInappropriate} SDK{childInappropriate > 1 ? 's are' : ' is'} not designed for child-directed applications. 
                These SDKs may collect behavioral data, advertising identifiers, or cross-app tracking information 
                that violates COPPA regulations.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* SDK List Grouped by Category */}
      {sortedCategories.map(cat => {
        const catSdks = byCategory[cat];
        const CatIcon = categoryIcons[cat] || AlertTriangle;
        const label = categoryLabels[cat] || cat;

        return (
          <div key={cat}>
            <div className="flex items-center gap-2 mb-3">
              <CatIcon size={16} className="text-slate-500" />
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">{label}</h3>
              <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-500 font-medium">{catSdks.length}</span>
            </div>
            <div className="space-y-3">
              {catSdks.map((sdk, idx) => (
                <SDKCard key={idx} sdk={sdk} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
