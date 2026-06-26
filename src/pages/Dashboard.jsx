import React from 'react';
import { Link } from 'react-router-dom';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { TrendingUp, Shield, AlertTriangle, CheckCircle, ArrowRight, Search, Eye, Activity, BarChart3 } from 'lucide-react';
import { dashboardOverviewData } from '../data/mockData';

const gradeStyles = {
  A: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
  B: 'bg-green-500/15 text-green-400 border-green-500/30',
  C: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
  D: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
  F: 'bg-red-500/15 text-red-400 border-red-500/30',
};

const riskLevelStyles = {
  Low: 'text-emerald-400',
  Medium: 'text-amber-400',
  High: 'text-red-400',
};

const CustomPieTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass-card px-3 py-2 text-sm">
        <p className="text-slate-200 font-medium">{payload[0].name}</p>
        <p style={{ color: payload[0].payload.color }} className="font-bold">{payload[0].value} apps</p>
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const data = dashboardOverviewData;

  return (
    <div className="responsive-container py-6 sm:py-8 lg:py-10 space-y-6 sm:space-y-8 lg:space-y-10">
      {/* Page title */}
      <div className="animate-fade-in-up">
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
          Privacy Risk <span className="gradient-text">Dashboard</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-400 mt-1.5 font-medium">
          Overview of analyzed educational Android applications
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 animate-fade-in-up stagger-1">
        <StatCard
          icon={Search}
          label="Apps Analyzed"
          value={data.totalAppsAnalyzed}
          accent="text-indigo-400"
          bg="bg-indigo-500/10"
        />
        <StatCard
          icon={Activity}
          label="Avg Risk Score"
          value={data.averageRiskScore}
          suffix="/100"
          accent="text-amber-400"
          bg="bg-amber-500/10"
        />
        <StatCard
          icon={AlertTriangle}
          label="High Risk"
          value={data.riskDistribution.find(d => d.name === 'High Risk')?.value || 0}
          accent="text-red-400"
          bg="bg-red-500/10"
        />
        <StatCard
          icon={CheckCircle}
          label="Low Risk"
          value={data.riskDistribution.find(d => d.name === 'Low Risk')?.value || 0}
          accent="text-emerald-400"
          bg="bg-emerald-500/10"
        />
      </div>

      {/* Risk distribution chart + Quick actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in-up stagger-2">
        {/* Pie chart */}
        <div className="glass-card p-6 lg:col-span-2 flex flex-col justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-slate-200 flex items-center gap-2 mb-1">
              <BarChart3 size={18} className="text-indigo-400" /> Risk Distribution
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mb-6">
              Breakdown of {data.totalAppsAnalyzed} analyzed applications by risk level
            </p>
          </div>
          <div className="flex flex-col sm:flex-row items-center justify-around gap-6 lg:gap-12 flex-1">
            <div className="w-full sm:w-60 h-60 shrink-0 flex items-center justify-center relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.riskDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={95}
                    paddingAngle={4}
                    dataKey="value"
                    strokeWidth={0}
                  >
                    {data.riskDistribution.map((entry, i) => (
                      <Cell key={i} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomPieTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute flex flex-col items-center justify-center">
                <span className="text-3xl font-extrabold text-white">{data.totalAppsAnalyzed}</span>
                <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Total Apps</span>
              </div>
            </div>
            <div className="flex sm:flex-col gap-4 sm:gap-3 flex-wrap justify-center w-full sm:w-auto">
              {data.riskDistribution.map((item) => (
                <div key={item.name} className="flex items-center gap-3 bg-slate-800/20 border border-slate-800/40 p-3 rounded-xl min-w-[140px] transition-premium hover:bg-slate-800/40">
                  <span className="w-3.5 h-3.5 rounded-full shrink-0 shadow-sm" style={{ backgroundColor: item.color, boxShadow: `0 0 10px ${item.color}40` }} />
                  <div>
                    <p className="text-xs sm:text-sm text-slate-200 font-semibold">{item.name}</p>
                    <p className="text-xs text-slate-400 font-medium">{item.value} apps</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick actions */}
        <div className="glass-card p-6 flex flex-col justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-slate-200 mb-1">Quick Actions</h2>
            <p className="text-xs sm:text-sm text-slate-400 mb-6">Shortcuts to platform features</p>
          </div>
          <div className="space-y-4 flex-1">
            <Link
              to="/analyze"
              className="flex items-center gap-4 p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/20 transition-premium glow-indigo group"
            >
              <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400">
                <Eye size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-200">View Analysis</p>
                <p className="text-xs text-slate-500 mt-0.5">Detailed app report</p>
              </div>
              <ArrowRight size={16} className="text-slate-500 group-hover:text-indigo-400 group-hover:translate-x-1 transition-all" />
            </Link>
            <Link
              to="/compare"
              className="flex items-center gap-4 p-4 rounded-xl bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 transition-premium glow-purple group"
            >
              <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                <TrendingUp size={20} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-200">Compare Apps</p>
                <p className="text-xs text-slate-500 mt-0.5">Side-by-side analysis</p>
              </div>
              <ArrowRight size={16} className="text-slate-500 group-hover:text-purple-400 group-hover:translate-x-1 transition-all" />
            </Link>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-700/30">
            <p className="text-xs text-slate-500">Last scan: {data.lastScanDate}</p>
          </div>
        </div>
      </div>

      {/* Recent apps table */}
      <div className="glass-card p-6 animate-fade-in-up stagger-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-slate-200 flex items-center gap-2">
              <Shield size={18} className="text-indigo-400" /> Recently Analyzed Apps
            </h2>
            <p className="text-xs sm:text-sm text-slate-400 mt-0.5">Latest privacy analysis results</p>
          </div>
          <Link
            to="/analyze"
            className="text-xs sm:text-sm text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1 shrink-0 font-semibold"
          >
            View all <ArrowRight size={14} />
          </Link>
        </div>

        {/* Desktop table */}
        <div className="hidden md:block overflow-hidden rounded-xl border border-slate-800/60 bg-slate-900/40">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="bg-slate-800/40 border-b border-slate-800/80 text-slate-300">
                <th className="text-left text-xs font-semibold uppercase tracking-wider py-3.5 px-4 text-slate-400">App Name</th>
                <th className="text-left text-xs font-semibold uppercase tracking-wider py-3.5 px-4 text-slate-400">Developer</th>
                <th className="text-left text-xs font-semibold uppercase tracking-wider py-3.5 px-4 text-slate-400">Category</th>
                <th className="text-center text-xs font-semibold uppercase tracking-wider py-3.5 px-4 text-slate-400">Grade</th>
                <th className="text-center text-xs font-semibold uppercase tracking-wider py-3.5 px-4 text-slate-400">Risk Score</th>
                <th className="text-center text-xs font-semibold uppercase tracking-wider py-3.5 px-4 text-slate-400">Risk Level</th>
                <th className="text-right text-xs font-semibold uppercase tracking-wider py-3.5 px-4 text-slate-400">Analyzed</th>
              </tr>
            </thead>
            <tbody>
              {data.recentApps.map((app) => (
                <tr key={app.id} className="border-b border-slate-800/30 hover:bg-slate-800/40 transition-premium hover:translate-x-1 duration-200">
                  <td className="py-4 px-4">
                    <span className="font-semibold text-slate-100 hover:text-indigo-400 transition-colors cursor-pointer">{app.name}</span>
                  </td>
                  <td className="py-4 px-4 text-slate-300">{app.developer}</td>
                  <td className="py-4 px-4 text-slate-400">
                    <span className="px-2.5 py-1 bg-slate-800/50 rounded-lg text-xs border border-slate-700/20">{app.category}</span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className={`inline-flex items-center justify-center w-8 h-8 rounded-lg border font-bold text-sm shadow-sm ${gradeStyles[app.riskGrade]}`}>
                      {app.riskGrade}
                    </span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className={`font-bold ${riskLevelStyles[app.riskLevel]}`}>{app.riskScore}</span>
                    <span className="text-slate-500 font-medium text-xs">/100</span>
                  </td>
                  <td className="py-4 px-4 text-center">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold tracking-wide border shadow-sm ${
                      app.riskLevel === 'Low' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' :
                      app.riskLevel === 'Medium' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                      'bg-red-500/10 text-red-400 border-red-500/20'
                    }`}>{app.riskLevel}</span>
                  </td>
                  <td className="py-4 px-4 text-right text-slate-400 text-xs font-medium">{app.analyzedAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile cards */}
        <div className="md:hidden space-y-3">
          {data.recentApps.map((app) => (
            <div key={app.id} className="p-3 rounded-xl bg-slate-800/30 border border-slate-700/20">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-sm text-slate-200 truncate">{app.name}</h3>
                  <p className="text-xs text-slate-500 truncate">{app.developer}</p>
                </div>
                <span className={`inline-flex items-center justify-center w-8 h-8 rounded-lg border font-bold text-xs shrink-0 ${gradeStyles[app.riskGrade]}`}>
                  {app.riskGrade}
                </span>
              </div>
              <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-700/20">
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
                  app.riskLevel === 'Low' ? 'bg-emerald-500/15 text-emerald-400' :
                  app.riskLevel === 'Medium' ? 'bg-amber-500/15 text-amber-400' :
                  'bg-red-500/15 text-red-400'
                }`}>{app.riskLevel} · {app.riskScore}/100</span>
                <span className="text-[10px] text-slate-600">{app.analyzedAt}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, suffix = '', accent, bg }) {
  let glowClass = 'glow-indigo';
  if (accent.includes('amber')) glowClass = 'glow-medium';
  if (accent.includes('red')) glowClass = 'glow-high';
  if (accent.includes('emerald')) glowClass = 'glow-low';

  return (
    <div className={`glass-card p-4 lg:p-6 ${glowClass}`}>
      <div className="flex items-center gap-3 mb-3">
        <div className={`p-2 lg:p-3 rounded-xl ${bg} transition-premium`}>
          <Icon size={18} className={`${accent}`} />
        </div>
        <span className="text-[10px] sm:text-xs text-slate-400 font-semibold uppercase tracking-wider">{label}</span>
      </div>
      <div className={`text-2xl sm:text-3xl lg:text-4xl font-extrabold ${accent}`}>
        {value}<span className="text-sm sm:text-lg text-slate-500 ml-1">{suffix}</span>
      </div>
    </div>
  );
}

