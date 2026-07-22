import { useState, useEffect, useRef } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Download, Package, Star, Users, Hash, ShieldCheck, Clock, Loader2, Database, CreditCard, AlertTriangle, TrendingUp, Shield, Bot, Lock, Fingerprint, Search, Sparkles } from 'lucide-react';
import * as htmlToImage from 'html-to-image';
import jsPDF from 'jspdf';
import RiskGradeBadge from '../components/RiskGradeBadge';
import RiskRadarChart from '../components/RiskRadarChart';
import DisclosureMismatch from '../components/DisclosureMismatch';
import RiskFactorsList from '../components/RiskFactorsList';
import TrackersAndNetwork from '../components/TrackersAndNetwork';
import PersonalDataTab from '../components/PersonalDataTab';
import PaymentSecurityTab from '../components/PaymentSecurityTab';
import SecurityMechanismsTab from '../components/SecurityMechanismsTab';
import IncidentTimeline from '../components/IncidentTimeline';
import RiskPredictions from '../components/RiskPredictions';
import ContextAwarePermissionsTab from '../components/ContextAwarePermissionsTab';
import SDKIntelligenceTab from '../components/SDKIntelligenceTab';
import EvidenceSourcesTab from '../components/EvidenceSourcesTab';
import LLMReportTab from '../components/LLMReportTab';

const TABS = [
  { id: 'overview', label: 'Overview', icon: Shield },
  { id: 'ai-report', label: 'AI Educator Brief', icon: Sparkles },
  { id: 'permissions', label: 'Permissions Context', icon: Lock },
  { id: 'evidence', label: 'Evidence Sources', icon: Search },
  { id: 'sdk-intelligence', label: 'SDK Intelligence', icon: Fingerprint },
  { id: 'personal-data', label: 'Personal Data', icon: Database },
  { id: 'payment', label: 'Payment Security', icon: CreditCard },
  { id: 'security', label: 'Security Mechanisms', icon: ShieldCheck },
  { id: 'incidents', label: 'Incidents', icon: AlertTriangle },
  { id: 'predictions', label: 'Risk Predictions', icon: TrendingUp },
];

export default function AppDetailView() {
  const { appId } = useParams();
  const [app, setApp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isExporting, setIsExporting] = useState(false);
  const reportRef = useRef();

  const handleExportPDF = async () => {
    if (!reportRef.current || !app) return;
    setIsExporting(true);
    
    try {
      const node = reportRef.current;
      const scale = 2;
      
      const dataUrl = await htmlToImage.toJpeg(node, {
        quality: 1.0,
        pixelRatio: scale,
        backgroundColor: '#0f172a'
      });
      
      const pdf = new jsPDF({
        orientation: node.offsetWidth > node.offsetHeight ? 'landscape' : 'portrait',
        unit: 'px',
        format: [node.offsetWidth * scale, node.offsetHeight * scale]
      });
      
      pdf.addImage(dataUrl, 'JPEG', 0, 0, node.offsetWidth * scale, node.offsetHeight * scale);
      pdf.save(`${app.name.replace(/\s+/g, '_')}_Privacy_Report.pdf`);
    } catch (err) {
      console.error("Failed to generate PDF", err);
    } finally {
      setIsExporting(false);
    }
  };

  useEffect(() => {
    fetch(`/api/apps/${appId}`)
      .then(res => {
        if (!res.ok) {
          if (res.status === 404) throw new Error('Not Found');
          throw new Error('Failed to fetch data');
        }
        return res.json();
      })
      .then(data => {
        setApp(data);
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, [appId]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
      </div>
    );
  }

  if (error === 'Not Found' || !app) {
    return (
      <div className="responsive-container py-16 flex flex-col items-center justify-center text-center min-h-[60vh]">
        <h2 className="text-2xl sm:text-3xl font-bold text-white mb-2">App Not Found</h2>
        <p className="text-sm text-slate-400 mb-6">The requested application analysis could not be found.</p>
        <Link to="/" className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-xl text-white font-medium transition-colors">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const analysisDate = new Date(app.analyzedAt || Date.now()).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  });

  const riskDimensionsData = app.dimensions ? Object.entries(app.dimensions).map(([key, value]) => ({
    dimension: key,
    score: value
  })) : [];

  const analysisMetadata = app.analysisMetadata || {};

  const trackersData = app.trackers ? {
    total: app.trackers.total || 0,
    list: (app.trackers.list || []).map(t => ({
      name: t.name,
      risk: t.risk?.toLowerCase() || 'medium',
      description: t.description || "Tracker detected during analysis.",
      category: t.category || "Unknown"
    }))
  } : { total: 0, list: [] };

  const networkData = {
    total: 0,
    unencrypted: 0,
    encrypted: 0,
    endpoints: []
  };

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
        <div className="flex items-center gap-2 sm:gap-3">
          <Link 
            to={`/chatbot?appId=${app.id}`}
            className="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs sm:text-sm font-medium transition-colors"
          >
            <Bot size={14} className="sm:w-4 sm:h-4" />
            <span className="hidden sm:inline">Ask AI Advisor</span>
            <span className="sm:hidden">AI</span>
          </Link>
          <button 
            onClick={handleExportPDF}
            disabled={isExporting}
            className="flex items-center gap-1.5 sm:gap-2 px-3 sm:px-4 py-1.5 sm:py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-600/50 text-white text-xs sm:text-sm font-medium transition-colors"
          >
            {isExporting ? <Loader2 size={14} className="sm:w-4 sm:h-4 animate-spin" /> : <Download size={14} className="sm:w-4 sm:h-4" />}
            <span className="hidden sm:inline">{isExporting ? 'Generating PDF...' : 'Generate PDF Report'}</span>
            <span className="sm:hidden">{isExporting ? '...' : 'PDF'}</span>
          </button>
        </div>
      </div>

      {/* Hidden Report for PDF */}
      <div style={{ position: 'absolute', left: '-9999px', top: 0 }}>
        <div ref={reportRef}>
          <div className="p-8 bg-slate-900 text-white" style={{ width: '800px' }}>
            <h1 className="text-2xl font-bold mb-4">{app.name} — Privacy Analysis Report</h1>
            <p className="text-sm text-slate-400 mb-6">Analyzed {analysisDate} | Risk Grade: {app.riskGrade} | Score: {app.riskScore}/100</p>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-slate-500">Developer:</span> {app.developer}</div>
              <div><span className="text-slate-500">Category:</span> {app.category}</div>
              <div><span className="text-slate-500">Target Age:</span> {app.targetAge}</div>
              <div><span className="text-slate-500">Compliance:</span> {app.complianceStandards}</div>
              <div><span className="text-slate-500">Permissions:</span> {app.permissions?.total} ({app.permissions?.dangerous} dangerous)</div>
              <div><span className="text-slate-500">Trackers:</span> {app.trackers?.total}</div>
              <div><span className="text-slate-500">Personal Data Items:</span> {app.personalData?.total}</div>
              <div><span className="text-slate-500">Security Incidents:</span> {app.securityIncidents?.total}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4 sm:space-y-6 lg:space-y-8 pb-4">
        {/* App Identity & Grade Hero */}
        <section className="bento-card p-4 sm:p-6 lg:p-8 animate-fade-in-up stagger-1">
          <div className="flex flex-col items-center gap-5 sm:gap-6 lg:flex-row lg:items-start lg:gap-8">
            {/* App icon */}
            <div className="w-16 h-16 sm:w-20 sm:h-20 lg:w-24 lg:h-24 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xl sm:text-2xl lg:text-3xl font-black shadow-lg shadow-indigo-500/20 shrink-0">
              {app.name.substring(0, 2).toUpperCase()}
            </div>

            {/* App info */}
            <div className="flex-1 text-center lg:text-left min-w-0 w-full">
              <h2 className="text-lg sm:text-2xl lg:text-3xl font-bold text-white">{app.name}</h2>
              <p className="text-sm sm:text-base text-slate-400 mt-0.5 sm:mt-1">{app.developer}</p>

              {/* Tags */}
              <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mt-2 sm:mt-3 justify-center lg:justify-start">
                <TagBadge icon={Package} label={app.category} accent />
                <TagBadge icon={Users} label={app.targetAge || "4-12 Years"} />
                <TagBadge icon={Star} label={String(app.playStoreRating || 4.5)} />
                <TagBadge icon={Download} label={app.installs || "1M+"} />
                <TagBadge icon={Hash} label={`v${app.version || "1.0"}`} />
              </div>

              <p className="text-xs sm:text-sm text-slate-500 mt-2 sm:mt-3 max-w-xl mx-auto lg:mx-0 line-clamp-2 sm:line-clamp-none">
                {app.description || "Educational application focusing on foundational learning concepts."}
              </p>
            </div>

            {/* Risk Grade */}
            <div className="shrink-0">
              <RiskGradeBadge grade={app.riskGrade} score={app.riskScore} />
            </div>
          </div>

          {/* Quick stats */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4 mt-4 sm:mt-6 pt-4 sm:pt-6 border-t border-slate-700/40">
            <QuickStat label="Permissions" value={app.permissions?.total || 0} sub={`${app.permissions?.dangerous || 0} dangerous`} color="text-amber-400" />
            <QuickStat label="Trackers" value={app.trackers?.total || 0} sub="SDKs detected" color="text-red-400" />
            <QuickStat label="Personal Data" value={app.personalData?.total || 0} sub={`${app.personalData?.sharedWithThirdParties || 0} shared`} color="text-purple-400" />
            <QuickStat label="Payment Methods" value={app.paymentGateways?.total || 0} sub="gateways" color="text-indigo-400" />
            <QuickStat label="Incidents" value={app.securityIncidents?.total || 0} sub="recorded" color="text-orange-400" />
          </div>
        </section>

        {/* Tab Navigation */}
        <div className="animate-fade-in-up stagger-2">
          <div className="flex overflow-x-auto hide-scrollbar gap-1 p-1 bg-slate-900/50 rounded-2xl border border-slate-700/30">
            {TABS.map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold whitespace-nowrap transition-all shrink-0 ${
                    isActive
                      ? 'bg-slate-800 text-white shadow-md border border-slate-700/50'
                      : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/30'
                  }`}
                >
                  <Icon size={15} className={isActive ? 'text-indigo-400' : ''} />
                  {tab.label}
                  {/* Badge counts */}
                  {tab.id === 'personal-data' && app.personalData?.total > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300">{app.personalData.total}</span>
                  )}
                  {tab.id === 'incidents' && app.securityIncidents?.total > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-rose-500/20 text-rose-300">{app.securityIncidents.total}</span>
                  )}
                  {tab.id === 'predictions' && app.riskPredictions?.total > 0 && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300">{app.riskPredictions.total}</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Tab Content */}
        <div className="animate-fade-in-up stagger-3">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Risk Radar + Permissions */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <RiskRadarChart dimensions={riskDimensionsData} height={325} />

                {/* Permissions summary */}
                <div className="bento-card p-4 sm:p-6 flex flex-col justify-between">
                  <div>
                    <h3 className="text-base sm:text-lg font-semibold text-slate-200 flex items-center gap-2 mb-1">
                      <ShieldCheck size={18} className="text-indigo-400 sm:w-5 sm:h-5" /> Permissions Overview
                    </h3>
                    <p className="text-xs sm:text-sm text-slate-400 mb-2">
                      {app.permissions?.total || 0} declared, {app.permissions?.dangerous || 0} marked dangerous
                    </p>
                    <button 
                      onClick={() => setActiveTab('permissions')}
                      className="text-[10px] sm:text-xs text-indigo-400 hover:text-indigo-300 font-semibold uppercase tracking-wide flex items-center gap-1 mb-4 w-fit bg-indigo-500/10 px-2 py-1 rounded-md transition-colors"
                    >
                      View Full Context & Necessity Scores <ArrowLeft size={12} className="rotate-180" />
                    </button>
                  </div>
                  <div className="space-y-2 max-h-[345px] overflow-y-auto pr-1 flex-1">
                    {app.permissions?.list?.map((perm, i) => (
                      <div key={i} className={`flex items-start sm:items-center gap-2 sm:gap-3 p-2 sm:p-2.5 rounded-lg text-sm transition-colors ${perm.status === 'dangerous' ? 'bg-red-500/5 hover:bg-red-500/10' : 'bg-slate-800/30 hover:bg-slate-800/60'}`}>
                        <span className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full shrink-0 mt-1.5 sm:mt-0 ${perm.status === 'dangerous' ? 'bg-red-400' : 'bg-slate-500'}`} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                            <span className="font-mono text-[10px] sm:text-xs text-slate-300 break-all sm:break-normal">{perm.name}</span>
                            {perm.status === 'dangerous' && <span className="text-[9px] sm:text-[10px] px-1.5 py-0.5 bg-red-500/20 text-red-300 rounded-full font-medium whitespace-nowrap">DANGEROUS</span>}
                            {perm.justified && <span className="text-[9px] sm:text-[10px] px-1.5 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-full font-medium whitespace-nowrap">JUSTIFIED</span>}
                          </div>
                          <p className="text-[10px] sm:text-xs text-slate-500 mt-0.5 line-clamp-1">{perm.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Trackers */}
              <TrackersAndNetwork trackers={trackersData} network={networkData} />

              {/* Compliance & 2FA Quick Info */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="bento-card p-4">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Compliance</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {(app.complianceStandards || '').split(',').map((std, i) => (
                      <span key={i} className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-medium">
                        {std.trim()}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="bento-card p-4">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Authentication</h4>
                  <p className="text-sm text-slate-300">{app.authenticationMethod}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className={`w-2 h-2 rounded-full ${app.has2fa ? 'bg-emerald-400' : 'bg-rose-400'}`} />
                    <span className="text-xs text-slate-400">{app.has2fa ? '2FA Available' : 'No 2FA'}</span>
                  </div>
                </div>
                <div className="bento-card p-4">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">Encryption</h4>
                  <p className="text-sm text-slate-300">{app.encryptionProtocol}</p>
                </div>
              </div>

              {/* Analysis Metadata */}
              <section className="bento-card p-4 sm:p-6">
                <h3 className="text-xs sm:text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2 sm:mb-3 flex items-center gap-2">
                  <Clock size={12} className="sm:w-3.5 sm:h-3.5" /> Analysis Metadata
                </h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                  <MetaItem label="APK Size" value={analysisMetadata.apkSize} />
                  <MetaItem label="Target SDK" value={`API ${analysisMetadata.targetSdkVersion}`} />
                  <MetaItem label="Static Analysis" value={analysisMetadata.staticAnalysisComplete ? 'Complete' : 'Incomplete'} />
                  <MetaItem label="Dynamic Analysis" value={analysisMetadata.dynamicAnalysisComplete ? 'Complete' : 'Incomplete'} />
                </div>
                <div className="mt-2 sm:mt-3 pt-2 sm:pt-3 border-t border-slate-700/30">
                  <p className="text-[10px] sm:text-xs text-slate-600 font-mono break-all">APK Hash: {analysisMetadata.apkHash}</p>
                </div>
              </section>
            </div>
          )}

          {activeTab === 'ai-report' && (
            <LLMReportTab 
              appId={app.id} 
              initialReport={app.llmReport} 
              onReportGenerated={(newReport) => setApp(prev => ({...prev, llmReport: newReport}))}
            />
          )}

          {activeTab === 'permissions' && (
            <ContextAwarePermissionsTab data={app.permissions} />
          )}

          {activeTab === 'evidence' && (
            <div className="space-y-6">
              <EvidenceSourcesTab data={app.evidenceSources} />
              <DisclosureMismatch data={app.disclosureMismatches} />
            </div>
          )}

          {activeTab === 'sdk-intelligence' && (
            <SDKIntelligenceTab data={app.trackers} />
          )}

          {activeTab === 'personal-data' && (
            <PersonalDataTab data={app.personalData} />
          )}

          {activeTab === 'payment' && (
            <PaymentSecurityTab data={app.paymentGateways} />
          )}

          {activeTab === 'security' && (
            <SecurityMechanismsTab data={app.securityMechanisms} />
          )}

          {activeTab === 'incidents' && (
            <IncidentTimeline data={app.securityIncidents} />
          )}

          {activeTab === 'predictions' && (
            <RiskPredictions data={app.riskPredictions} />
          )}
        </div>
      </div>
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
  return (
    <div className="text-center p-3 sm:p-4 rounded-xl border transition-all bg-slate-800/20 border-slate-700/20 hover:bg-slate-800/40">
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
