import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, Download, Calendar, Package, Star, Users, Hash, ShieldCheck, Clock } from 'lucide-react';
import { appDetailData } from '../data/mockData';
import RiskGradeBadge from '../components/RiskGradeBadge';
import RiskRadarChart from '../components/RiskRadarChart';
import DisclosureMismatch from '../components/DisclosureMismatch';
import RiskFactorsList from '../components/RiskFactorsList';
import TrackersAndNetwork from '../components/TrackersAndNetwork';

export default function AppDetailView() {
  const app = appDetailData;
  const analysisDate = new Date(app.analysisMetadata.analyzedAt).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  });

  return (
    <div className="responsive-container py-4 sm:py-6 lg:py-8 space-y-4 sm:space-y-6 lg:space-y-8">
      {/* Back link + Export */}
      <div className="flex items-center justify-between animate-fade-in-up">
        <div className="flex items-center gap-2 sm:gap-3">
          <Link to="/" className="p-1.5 sm:p-2 rounded-lg hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-200">
            <ArrowLeft size={18} className="sm:w-5 sm:h-5" />
          </Link>
          <div>
            <h1 className="text-base sm:text-lg font-bold text-slate-100">Privacy Analysis Report</h1>
            <p className="text-[10px] sm:text-xs text-slate-500">Analyzed {analysisDate}</p>
          </div>
        </div>
        <button className="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs sm:text-sm font-medium transition-colors">
          <Download size={14} className="sm:w-4 sm:h-4" />
          <span className="hidden sm:inline">Export Report</span>
          <span className="sm:hidden">Export</span>
        </button>
      </div>

      {/* App Identity & Grade Hero */}
      <section className="glass-card p-4 sm:p-6 lg:p-8 animate-fade-in-up stagger-1">
        <div className="flex flex-col items-center gap-5 sm:gap-6 lg:flex-row lg:items-start lg:gap-8">
          {/* App icon */}
          <div className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl sm:text-2xl lg:text-3xl font-black shadow-lg shadow-indigo-500/20 shrink-0">
            KM
          </div>

          {/* App info */}
          <div className="flex-1 text-center lg:text-left min-w-0 w-full">
            <h2 className="text-lg sm:text-2xl lg:text-3xl font-bold text-white">{app.appName}</h2>
            <p className="text-sm sm:text-base text-slate-400 mt-0.5 sm:mt-1">{app.developer}</p>

            {/* Tags */}
            <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mt-2 sm:mt-3 justify-center lg:justify-start">
              <TagBadge icon={Package} label={app.category} accent />
              <TagBadge icon={Users} label={app.targetAge} />
              <TagBadge icon={Star} label={String(app.playStoreRating)} />
              <TagBadge icon={Download} label={app.installs} />
              <TagBadge icon={Hash} label={`v${app.version}`} />
            </div>

            <p className="text-xs sm:text-sm text-slate-500 mt-2 sm:mt-3 max-w-xl mx-auto lg:mx-0 line-clamp-2 sm:line-clamp-none">
              {app.description}
            </p>
          </div>

          {/* Risk Grade */}
          <div className="shrink-0">
            <RiskGradeBadge grade={app.riskGrade} score={app.privacyRiskScore} />
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mt-4 sm:mt-6 pt-4 sm:pt-6 border-t border-slate-700/40">
          <QuickStat label="Permissions" value={app.permissions.declared} sub={`${app.permissions.dangerous} dangerous`} color="text-amber-400" />
          <QuickStat label="Trackers" value={app.trackers.total} sub="SDKs detected" color="text-red-400" />
          <QuickStat label="Endpoints" value={app.networkEndpoints.total} sub={`${app.networkEndpoints.unencrypted} insecure`} color="text-orange-400" />
          <QuickStat label="Disclosure Match" value={`${app.disclosureMismatch.overallMatch}%`} sub="accuracy rate" color={app.disclosureMismatch.overallMatch < 50 ? 'text-red-400' : 'text-emerald-400'} />
        </div>
      </section>

      {/* Risk Radar + Permissions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in-up stagger-2">
        <RiskRadarChart dimensions={app.riskDimensions} height={325} />

        {/* Permissions summary */}
        <div className="glass-card p-4 sm:p-6 flex flex-col justify-between">
          <div>
            <h3 className="text-base sm:text-lg font-semibold text-slate-200 flex items-center gap-2 mb-1">
              <ShieldCheck size={18} className="text-indigo-400 sm:w-5 sm:h-5" /> Permissions Overview
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 mb-4">
              {app.permissions.declared} declared, {app.permissions.used} actively used, {app.permissions.dangerous} marked dangerous
            </p>
          </div>
          <div className="space-y-2 max-h-[345px] overflow-y-auto pr-1 flex-1">
            {app.permissions.list.map((perm, i) => (
              <div key={i} className={`flex items-start sm:items-center gap-2 sm:gap-3 p-2 sm:p-2.5 rounded-lg text-sm transition-colors ${perm.isDangerous ? 'bg-red-500/5 hover:bg-red-500/10' : 'bg-slate-800/30 hover:bg-slate-800/60'}`}>
                <span className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full shrink-0 mt-1.5 sm:mt-0 ${perm.isDangerous ? 'bg-red-400' : 'bg-slate-500'}`} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                    <span className="font-mono text-[10px] sm:text-xs text-slate-300 break-all sm:break-normal">{perm.name}</span>
                    {perm.isDangerous && <span className="text-[9px] sm:text-[10px] px-1.5 py-0.5 bg-red-500/20 text-red-300 rounded-full font-medium whitespace-nowrap">DANGEROUS</span>}
                    {!perm.isUsed && <span className="text-[9px] sm:text-[10px] px-1.5 py-0.5 bg-slate-600/50 text-slate-400 rounded-full whitespace-nowrap">UNUSED</span>}
                  </div>
                  <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5 line-clamp-1">{perm.justification}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>


      {/* Disclosure Mismatch */}
      <div className="animate-fade-in-up stagger-3">
        <DisclosureMismatch data={app.disclosureMismatch} />
      </div>

      {/* Risk Factors */}
      <div className="animate-fade-in-up stagger-4">
        <RiskFactorsList factors={app.riskFactors} />
      </div>

      {/* Trackers & Network */}
      <div className="animate-fade-in-up stagger-5">
        <TrackersAndNetwork trackers={app.trackers} network={app.networkEndpoints} />
      </div>

      {/* Analysis Metadata Footer */}
      <section className="glass-card p-4 sm:p-6 animate-fade-in-up stagger-6">
        <h3 className="text-xs sm:text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 sm:mb-3 flex items-center gap-2">
          <Clock size={12} className="sm:w-3.5 sm:h-3.5" /> Analysis Metadata
        </h3>
        <div className="stat-grid text-sm">
          <MetaItem label="APK Size" value={app.analysisMetadata.apkSize} />
          <MetaItem label="Target SDK" value={`API ${app.analysisMetadata.targetSdkVersion}`} />
          <MetaItem label="Static Analysis" value={app.analysisMetadata.staticAnalysisComplete ? '✅ Complete' : '❌ Incomplete'} />
          <MetaItem label="Dynamic Analysis" value={app.analysisMetadata.dynamicAnalysisComplete ? '✅ Complete' : '❌ Incomplete'} />
        </div>
        <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-slate-700/30">
          <p className="text-[10px] sm:text-xs text-slate-600 font-mono break-all">APK Hash: {app.analysisMetadata.apkHash}</p>
        </div>
      </section>
    </div>
  );
}

function TagBadge({ icon: Icon, label, accent = false }) {
  return (
    <span className={`flex items-center gap-1 text-[10px] sm:text-xs px-2 py-0.5 sm:py-1 rounded-full ${
      accent
        ? 'bg-indigo-500/15 text-indigo-300'
        : 'bg-slate-700/60 text-slate-300'
    }`}>
      <Icon size={10} className="sm:w-3 sm:h-3" /> {label}
    </span>
  );
}

function QuickStat({ label, value, sub, color }) {
  let glowClass = 'glow-indigo';
  let borderClass = 'border-indigo-500/20';
  let bgClass = 'bg-indigo-500/5';
  
  if (color.includes('amber')) {
    glowClass = 'glow-medium';
    borderClass = 'border-amber-500/20';
    bgClass = 'bg-amber-500/5';
  } else if (color.includes('red')) {
    glowClass = 'glow-high';
    borderClass = 'border-red-500/20';
    bgClass = 'bg-red-500/5';
  } else if (color.includes('orange')) {
    glowClass = 'glow-medium';
    borderClass = 'border-orange-500/20';
    bgClass = 'bg-orange-500/5';
  } else if (color.includes('emerald')) {
    glowClass = 'glow-low';
    borderClass = 'border-emerald-500/20';
    bgClass = 'bg-emerald-500/5';
  }

  return (
    <div className={`text-center p-3 sm:p-4 rounded-xl border transition-premium ${bgClass} ${borderClass} ${glowClass}`}>
      <div className={`text-xl sm:text-2xl lg:text-3xl font-extrabold ${color}`}>{value}</div>
      <div className="text-xs sm:text-sm text-slate-200 font-semibold mt-1">{label}</div>
      <div className="text-[10px] sm:text-xs text-slate-500 font-medium mt-0.5">{sub}</div>
    </div>
  );
}


function MetaItem({ label, value }) {
  return (
    <div>
      <span className="text-slate-500 text-[10px] sm:text-xs">{label}</span>
      <p className="text-slate-300 font-medium text-xs sm:text-sm">{value}</p>
    </div>
  );
}
