import { useState, useMemo, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { TrendingUp, Shield, AlertTriangle, CheckCircle, ArrowRight, Search, Eye, Activity, BarChart3, UploadCloud, Loader2 } from 'lucide-react';
import UploadModal from '../components/UploadModal';

const gradeStyles = {
  A: 'bg-teal-500/15 text-teal-300 border border-teal-500/30',
  B: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30',
  C: 'bg-amber-500/15 text-amber-300 border border-amber-500/30',
  D: 'bg-orange-500/15 text-orange-300 border border-orange-500/30',
  F: 'bg-rose-500/15 text-rose-300 border border-rose-500/30',
};

const CustomPieTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-900/90 backdrop-blur-md px-4 py-2 rounded-xl border border-slate-700/50 shadow-2xl">
        <p className="text-slate-300 text-xs font-semibold uppercase tracking-wider mb-1">{payload[0].name}</p>
        <p style={{ color: payload[0].payload.color }} className="font-extrabold text-lg">{payload[0].value} <span className="text-xs text-slate-500 font-medium">apps</span></p>
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [riskFilter, setRiskFilter] = useState('All');
  const [isUploadOpen, setIsUploadOpen] = useState(false);

  useEffect(() => {
    fetch('/api/apps')
      .then(res => {
        if (!res.ok) throw new Error('Failed to fetch data');
        return res.json();
      })
      .then(data => {
        setData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setError(err.message);
        setLoading(false);
      });
  }, []);

  const filteredApps = useMemo(() => {
    if (!data) return [];
    return data.recentApps.filter(app => {
      const matchesSearch = app.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                            app.developer.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesFilter = riskFilter === 'All' || app.riskLevel === riskFilter;
      return matchesSearch && matchesFilter;
    });
  }, [data, searchTerm, riskFilter]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center p-12 min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 text-indigo-400 animate-spin" />
          <p className="text-slate-400 font-medium text-sm tracking-wide">Initializing Dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="bento-card border-rose-500/20 p-8 flex flex-col items-center max-w-md text-center">
          <AlertTriangle className="text-rose-400 w-12 h-12 mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">Analysis Engine Offline</h2>
          <p className="text-slate-400 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="responsive-container">
      
      {/* Hero Section */}
      <div className="mb-8 md:mb-12 animate-fade-in-up stagger-1">
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-white tracking-tight mb-3">
          Platform <span className="gradient-text">Overview</span>
        </h1>
        <p className="text-sm sm:text-base text-slate-400 font-medium max-w-2xl leading-relaxed">
          Monitor the privacy risks of educational applications through automated, state-of-the-art static and dynamic analysis.
        </p>
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 animate-fade-in-up stagger-2">
        
        {/* STATS ROW (4 Cards) */}
        <StatCard
          icon={Shield}
          label="Total Analyzed"
          value={data.totalAppsAnalyzed}
          accent="text-indigo-400"
          bg="bg-indigo-500/10"
          borderHover="hover:border-indigo-500/30"
          colSpan="md:col-span-6 lg:col-span-3"
        />
        <StatCard
          icon={Activity}
          label="Avg Risk Score"
          value={data.averageRiskScore}
          suffix="/100"
          accent="text-amber-400"
          bg="bg-amber-500/10"
          borderHover="hover:border-amber-500/30"
          colSpan="md:col-span-6 lg:col-span-3"
        />
        <StatCard
          icon={AlertTriangle}
          label="Critical Risk"
          value={data.riskDistribution.find(d => d.name === 'High Risk')?.value || 0}
          accent="text-rose-400"
          bg="bg-rose-500/10"
          borderHover="hover:border-rose-500/30"
          colSpan="md:col-span-6 lg:col-span-3"
        />
        <StatCard
          icon={CheckCircle}
          label="Safe Apps"
          value={data.riskDistribution.find(d => d.name === 'Low Risk')?.value || 0}
          accent="text-teal-400"
          bg="bg-teal-500/10"
          borderHover="hover:border-teal-500/30"
          colSpan="md:col-span-6 lg:col-span-3"
        />

        {/* RISK DISTRIBUTION CHART */}
        <div className="bento-card p-6 md:p-8 md:col-span-12 lg:col-span-8 flex flex-col justify-between group">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-lg md:text-xl font-bold text-white flex items-center gap-3">
                <div className="p-2 rounded-xl bg-slate-800/80 text-indigo-400"><BarChart3 size={18} /></div>
                Risk Distribution
              </h2>
              <p className="text-sm text-slate-400 mt-2">Breakdown of analyzed applications by severity</p>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row items-center justify-around gap-8 flex-1">
            <div className="w-full sm:w-64 h-64 shrink-0 flex items-center justify-center relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.riskDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={70}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                    strokeWidth={0}
                    cornerRadius={8}
                  >
                    {data.riskDistribution.map((entry, i) => (
                      <Cell key={i} fill={entry.color} className="drop-shadow-lg" />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomPieTooltip />} cursor={{fill: 'transparent'}} />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute flex flex-col items-center justify-center pointer-events-none">
                <span className="text-4xl font-black text-white">{data.totalAppsAnalyzed}</span>
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-widest mt-1">Total</span>
              </div>
            </div>
            
            <div className="flex flex-col gap-4 w-full sm:w-auto">
              {data.riskDistribution.map((item) => (
                <div key={item.name} className="flex items-center justify-between sm:justify-start gap-4 p-3 rounded-2xl bg-slate-800/30 border border-slate-700/20 hover:bg-slate-800/50 transition-colors min-w-[180px]">
                  <div className="flex items-center gap-3">
                    <span className="status-dot shrink-0" style={{ color: item.color }} />
                    <p className="text-sm text-slate-200 font-semibold">{item.name}</p>
                  </div>
                  <span className="text-sm font-bold text-slate-400 bg-slate-900/50 px-2 py-0.5 rounded-lg">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* QUICK ACTIONS */}
        <div className="bento-card p-6 md:p-8 md:col-span-12 lg:col-span-4 flex flex-col">
          <h2 className="text-lg md:text-xl font-bold text-white mb-2">Actions</h2>
          <p className="text-sm text-slate-400 mb-6">Common platform tasks</p>
          
          <div className="space-y-3 flex-1 flex flex-col justify-center">
            <button
              onClick={() => setIsUploadOpen(true)}
              className="flex items-center justify-between p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 hover:border-indigo-500/40 transition-all group text-left"
            >
              <div className="flex items-center gap-4">
                <div className="p-2.5 bg-indigo-500/20 rounded-xl text-indigo-400">
                  <UploadCloud size={20} />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-100">Analyze APK</p>
                  <p className="text-xs text-slate-500 font-medium">Upload new app</p>
                </div>
              </div>
              <ArrowRight size={18} className="text-slate-600 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
            </button>
            
            <Link
              to="/compare"
              className="flex items-center justify-between p-4 rounded-2xl bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 hover:border-purple-500/40 transition-all group"
            >
              <div className="flex items-center gap-4">
                <div className="p-2.5 bg-purple-500/20 rounded-xl text-purple-400">
                  <TrendingUp size={20} />
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-100">Compare Apps</p>
                  <p className="text-xs text-slate-500 font-medium">Side-by-side view</p>
                </div>
              </div>
              <ArrowRight size={18} className="text-slate-600 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
            </Link>
          </div>
        </div>

        {/* TABLE SECTION */}
        <div className="bento-card md:col-span-12 overflow-hidden animate-fade-in-up stagger-3 flex flex-col">
          
          {/* Table Header & Filters */}
          <div className="p-6 md:p-8 border-b border-slate-700/30 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div>
              <h2 className="text-lg md:text-xl font-bold text-white flex items-center gap-3 mb-2">
                <div className="p-2 rounded-xl bg-slate-800/80 text-teal-400"><Search size={18} /></div>
                Analysis History
              </h2>
              <p className="text-sm text-slate-400">Review past scan reports and risk evaluations</p>
            </div>
            
            <div className="flex flex-col sm:flex-row items-center gap-3">
              <div className="relative w-full sm:w-64">
                <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="text"
                  placeholder="Search apps..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-slate-900/50 border border-slate-700/50 rounded-full pl-11 pr-4 py-2 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50 focus:ring-2 focus:ring-indigo-500/20 transition-all placeholder:text-slate-600 font-medium"
                />
              </div>
              <div className="flex bg-slate-900/50 rounded-full p-1 border border-slate-700/50 w-full sm:w-auto">
                {['All', 'Low', 'Medium', 'High'].map(level => (
                  <button
                    key={level}
                    onClick={() => setRiskFilter(level)}
                    className={`flex-1 sm:flex-none px-4 py-1.5 text-xs font-bold rounded-full transition-all ${
                      riskFilter === level
                        ? 'bg-slate-700 text-white shadow-md'
                        : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'
                    }`}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Desktop Table View */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="bg-slate-900/40 text-xs uppercase font-bold text-slate-500 tracking-wider">
                <tr>
                  <th className="py-4 px-8 font-semibold">Application</th>
                  <th className="py-4 px-6 font-semibold">Category</th>
                  <th className="py-4 px-6 font-semibold text-center">Score</th>
                  <th className="py-4 px-6 font-semibold">Risk Level</th>
                  <th className="py-4 px-8 font-semibold text-right">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/30">
                {filteredApps.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="py-12 text-center text-slate-500 font-medium">No records found.</td>
                  </tr>
                ) : filteredApps.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-800/20 transition-colors group">
                    <td className="py-4 px-8">
                      <Link to={`/analyze/${app.id}`} className="block">
                        <p className="font-bold text-slate-200 group-hover:text-indigo-400 transition-colors">{app.name}</p>
                        <p className="text-xs text-slate-500 mt-1 font-medium">{app.developer}</p>
                      </Link>
                    </td>
                    <td className="py-4 px-6">
                      <span className="px-3 py-1 bg-slate-800/60 rounded-lg text-xs font-semibold text-slate-300 border border-slate-700/30">{app.category}</span>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center justify-center gap-3">
                        <span className={`flex items-center justify-center w-8 h-8 rounded-lg font-black text-sm shadow-inner ${gradeStyles[app.riskGrade]}`}>
                          {app.riskGrade}
                        </span>
                        <div className="text-center min-w-[40px]">
                          <span className="font-bold text-slate-200">{app.riskScore}</span>
                          <span className="text-[10px] text-slate-500 block -mt-1 uppercase">Score</span>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2">
                        <span className="status-dot" style={{
                          color: app.riskLevel === 'Low' ? '#2dd4bf' : app.riskLevel === 'Medium' ? '#fbbf24' : '#fb7185'
                        }} />
                        <span className="font-bold text-slate-300">{app.riskLevel}</span>
                      </div>
                    </td>
                    <td className="py-4 px-8 text-right text-slate-500 font-medium text-xs">
                      {app.analyzedAt}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile List View */}
          <div className="md:hidden divide-y divide-slate-800/30">
            {filteredApps.length === 0 ? (
              <div className="py-12 text-center text-slate-500 font-medium text-sm">No records found.</div>
            ) : filteredApps.map((app) => (
              <Link key={app.id} to={`/analyze/${app.id}`} className="block p-5 hover:bg-slate-800/20 transition-colors active:bg-slate-800/40">
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <h3 className="font-bold text-slate-200">{app.name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{app.developer}</p>
                  </div>
                  <span className={`shrink-0 flex items-center justify-center w-8 h-8 rounded-lg font-black text-sm shadow-inner ${gradeStyles[app.riskGrade]}`}>
                    {app.riskGrade}
                  </span>
                </div>
                <div className="flex items-center justify-between mt-4">
                  <div className="flex items-center gap-2 bg-slate-900/50 px-3 py-1.5 rounded-full border border-slate-700/50">
                    <span className="status-dot" style={{
                      color: app.riskLevel === 'Low' ? '#2dd4bf' : app.riskLevel === 'Medium' ? '#fbbf24' : '#fb7185'
                    }} />
                    <span className="text-xs font-bold text-slate-300">{app.riskLevel}</span>
                  </div>
                  <span className="text-xs text-slate-500 font-medium">{app.analyzedAt}</span>
                </div>
              </Link>
            ))}
          </div>

        </div>
      </div>
      
      <UploadModal isOpen={isUploadOpen} onClose={() => setIsUploadOpen(false)} />
    </div>
  );
}

function StatCard({ icon: Icon, label, value, suffix = '', accent, bg, borderHover, colSpan }) {
  return (
    <div className={`bento-card p-6 flex flex-col justify-between ${colSpan} ${borderHover} group`}>
      <div className="flex items-center justify-between mb-4">
        <div className={`p-3 rounded-2xl ${bg} text-opacity-90 group-hover:scale-110 transition-transform duration-300`}>
          <Icon size={20} className={accent} />
        </div>
      </div>
      <div>
        <div className="flex items-baseline gap-1">
          <span className={`text-4xl lg:text-5xl font-black tracking-tight ${accent}`}>{value}</span>
          {suffix && <span className="text-sm font-bold text-slate-500">{suffix}</span>}
        </div>
        <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mt-2">{label}</p>
      </div>
    </div>
  );
}
