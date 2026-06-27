import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="glass-card px-3 sm:px-4 py-2 sm:py-3 text-xs sm:text-sm">
        <p className="text-slate-200 font-semibold">{data.dimension}</p>
        <p className="text-indigo-400">Risk Score: <span className="font-bold">{data.score}</span>/100</p>
      </div>
    );
  }
  return null;
};

export default function RiskRadarChart({ dimensions, height = 260 }) {
  const isLarge = height > 300;
  
  return (
    <div className="glass-card p-4 sm:p-6 h-full flex flex-col justify-between">
      <div>
        <h3 className="text-base sm:text-lg font-semibold text-slate-200 mb-0.5 sm:mb-1">Risk Dimension Analysis</h3>
        <p className="text-xs sm:text-sm text-slate-400 mb-3 sm:mb-4">Higher values indicate greater risk in each category</p>
      </div>
      <div className="flex-1 flex items-center justify-center">
        <ResponsiveContainer width="100%" height={height}>
          <RadarChart data={dimensions} cx="50%" cy="50%" outerRadius="70%">
            <PolarGrid stroke="#334155" strokeDasharray="3 3" />
            <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: isLarge ? 12 : 11 }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#64748b', fontSize: isLarge ? 11 : 10 }} axisLine={false} />
            <Tooltip content={<CustomTooltip />} />
            <Radar name="Risk" dataKey="score" stroke="#818cf8" fill="#6366f1" fillOpacity={0.25} strokeWidth={2} dot={{ r: 3, fill: '#818cf8' }} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

