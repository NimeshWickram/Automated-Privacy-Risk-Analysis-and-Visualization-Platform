import { Database, Eye, EyeOff, AlertTriangle, Shield, Users, BookOpen, Smartphone, Activity } from 'lucide-react';

const categoryIcons = {
  'Student Marks': BookOpen,
  'Identity': Users,
  'Contact': Users,
  'Device': Smartphone,
  'Behavioral': Activity,
  'Location': Eye,
};

const riskColors = {
  Critical: { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20', dot: 'bg-rose-400' },
  High: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', dot: 'bg-orange-400' },
  Medium: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20', dot: 'bg-amber-400' },
  Low: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20', dot: 'bg-emerald-400' },
};

export default function PersonalDataTab({ data }) {
  if (!data || !data.list || data.list.length === 0) {
    return (
      <div className="bento-card p-8 text-center">
        <Shield className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-white mb-2">No Personal Data Collected</h3>
        <p className="text-sm text-slate-400">This app does not appear to collect personal data.</p>
      </div>
    );
  }

  // Group by category
  const categories = {};
  data.list.forEach(item => {
    if (!categories[item.dataCategory]) categories[item.dataCategory] = [];
    categories[item.dataCategory].push(item);
  });

  const sharedCount = data.list.filter(d => d.sharedWithThirdParties).length;

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <SummaryCard label="Data Types" value={data.total} icon={Database} color="text-indigo-400" />
        <SummaryCard label="Collected" value={data.collected} icon={Eye} color="text-amber-400" />
        <SummaryCard label="Shared with 3rd Party" value={sharedCount} icon={AlertTriangle} color="text-rose-400" />
        <SummaryCard label="Private" value={data.collected - sharedCount} icon={EyeOff} color="text-emerald-400" />
      </div>

      {/* Student Marks Alert */}
      {categories['Student Marks'] && (
        <div className="bento-card p-5 border-amber-500/20 bg-amber-500/5">
          <div className="flex items-start gap-4">
            <div className="p-3 rounded-xl bg-amber-500/15">
              <AlertTriangle className="w-6 h-6 text-amber-400" />
            </div>
            <div className="flex-1">
              <h3 className="text-base font-bold text-amber-300 mb-1">⚠️ Student Academic Data Collected</h3>
              <p className="text-sm text-slate-400 mb-3">
                This app collects student marks/grades — one of the most sensitive data categories under FERPA and COPPA.
                If this data is accessed by unauthorized third parties, it could be used for profiling or discrimination.
              </p>
              <div className="space-y-2">
                {categories['Student Marks'].map((item, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className={`w-2 h-2 rounded-full ${riskColors[item.riskLevel]?.dot || 'bg-slate-400'}`} />
                    <span className="text-slate-200 font-medium">{item.dataType}</span>
                    <span className="text-slate-500">—</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${item.sharedWithThirdParties ? 'bg-rose-500/15 text-rose-300' : 'bg-emerald-500/15 text-emerald-300'}`}>
                      {item.sharedWithThirdParties ? `Shared: ${item.thirdPartyNames}` : 'Not shared externally'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Data Categories */}
      {Object.entries(categories).map(([category, items]) => {
        const Icon = categoryIcons[category] || Database;
        return (
          <div key={category} className="bento-card overflow-hidden">
            <div className="p-5 border-b border-slate-700/30 flex items-center gap-3">
              <div className="p-2 rounded-xl bg-slate-800/80">
                <Icon size={18} className="text-indigo-400" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">{category}</h3>
                <p className="text-xs text-slate-500">{items.length} data types</p>
              </div>
            </div>
            <div className="divide-y divide-slate-800/30">
              {items.map((item, i) => {
                const risk = riskColors[item.riskLevel] || riskColors.Low;
                return (
                  <div key={i} className="p-4 hover:bg-slate-800/20 transition-colors">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${risk.dot}`} />
                        <span className="font-semibold text-sm text-slate-200">{item.dataType}</span>
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold ${risk.bg} ${risk.text}`}>
                          {item.riskLevel}
                        </span>
                      </div>
                      {item.sharedWithThirdParties && (
                        <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-300 font-medium whitespace-nowrap">
                          SHARED: {item.thirdPartyNames}
                        </span>
                      )}
                    </div>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                      <MetaLabel label="Collection" value={item.collectionMethod} />
                      <MetaLabel label="Storage" value={item.storageLocation} />
                      <MetaLabel label="Encryption" value={item.encryptionStatus} />
                      <MetaLabel label="Retention" value={item.retentionPeriod} />
                    </div>
                    <p className="text-xs text-slate-500 mt-2">
                      <span className="text-slate-400 font-medium">Purpose:</span> {item.purpose}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SummaryCard({ label, value, icon: Icon, color }) {
  return (
    <div className="bento-card p-4 text-center">
      <Icon size={18} className={`${color} mx-auto mb-2`} />
      <div className={`text-2xl font-black ${color}`}>{value}</div>
      <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-1">{label}</div>
    </div>
  );
}

function MetaLabel({ label, value }) {
  return (
    <div>
      <span className="text-slate-500 font-medium">{label}:</span>
      <span className="text-slate-300 ml-1">{value}</span>
    </div>
  );
}
