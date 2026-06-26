import React from 'react';

const gradeConfig = {
  A: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', border: 'border-emerald-500/40', label: 'Excellent' },
  B: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/40', label: 'Good' },
  C: { bg: 'bg-amber-500/20', text: 'text-amber-400', border: 'border-amber-500/40', label: 'Fair' },
  D: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/40', label: 'Poor' },
  F: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/40', label: 'Failing' },
};

export default function RiskGradeBadge({ grade, score, size = 'lg' }) {
  const config = gradeConfig[grade] || gradeConfig.F;
  const isLarge = size === 'lg';

  return (
    <div className="flex flex-col items-center gap-2 sm:gap-3">
      <div className={`relative ${isLarge ? 'w-20 h-20 sm:w-28 sm:h-28 lg:w-32 lg:h-32' : 'w-16 h-16 sm:w-20 sm:h-20'} rounded-full ${config.bg} border-2 ${config.border} flex items-center justify-center animate-float`}>
        <div className={`absolute inset-0 rounded-full ${config.bg} animate-pulse-risk opacity-40`} />
        <span className={`${config.text} font-black ${isLarge ? 'text-3xl sm:text-4xl lg:text-5xl' : 'text-2xl sm:text-3xl'} relative z-10`}>{grade}</span>
      </div>
      <div className="text-center">
        <p className={`${config.text} font-semibold ${isLarge ? 'text-sm sm:text-lg' : 'text-xs sm:text-sm'}`}>{config.label}</p>
        <p className="text-slate-400 text-xs sm:text-sm">Risk Score: {score}/100</p>
      </div>
    </div>
  );
}
