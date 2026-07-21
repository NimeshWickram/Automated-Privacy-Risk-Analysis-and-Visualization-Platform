import { CreditCard, ShieldAlert, ShieldCheck, AlertTriangle, Lock, Unlock, RefreshCw, XCircle } from 'lucide-react';

const riskColors = {
  High: { bg: 'bg-rose-500/10', text: 'text-rose-400', border: 'border-rose-500/20' },
  Medium: { bg: 'bg-amber-500/10', text: 'text-amber-400', border: 'border-amber-500/20' },
  Low: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/20' },
};

export default function PaymentSecurityTab({ data }) {
  if (!data || !data.list || data.list.length === 0) {
    return (
      <div className="bento-card p-8 text-center">
        <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-white mb-2">No Payment Processing</h3>
        <p className="text-sm text-slate-400">
          This app does not process payments directly, which means <strong className="text-emerald-300">zero payment security risk</strong>.
          This is ideal for children's educational apps.
        </p>
      </div>
    );
  }

  const hasInstallment = data.list.some(g => g.installmentAvailable);
  const hasAutoRenewal = data.list.some(g => g.autoRenewal);

  return (
    <div className="space-y-6">
      {/* Stolen Card Scenario Alert */}
      <div className="bento-card p-5 border-rose-500/20 bg-rose-500/5">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-xl bg-rose-500/15">
            <ShieldAlert className="w-6 h-6 text-rose-400" />
          </div>
          <div className="flex-1">
            <h3 className="text-base font-bold text-rose-300 mb-1">🚨 Stolen Card Scenario</h3>
            <p className="text-sm text-slate-400 mb-3">
              If someone steals an ATM/credit card and uses it on this app, the following protections apply:
            </p>
            <div className="space-y-2">
              {data.list.map((gw, i) => (
                <div key={i} className="bg-slate-900/40 rounded-xl p-3 text-sm">
                  <span className="font-bold text-slate-200">{gw.paymentMethod}</span>
                  <span className="text-slate-500"> via {gw.provider}</span>
                  <p className="text-xs text-slate-400 mt-1">{gw.stolenCardProtection || 'No specific protection documented'}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs">
                    <span className={`flex items-center gap-1 ${gw.fraudDetection ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {gw.fraudDetection ? <ShieldCheck size={12} /> : <XCircle size={12} />}
                      Fraud Detection
                    </span>
                    <span className={`flex items-center gap-1 ${gw.pciDssCompliant ? 'text-emerald-400' : 'text-rose-400'}`}>
                      {gw.pciDssCompliant ? <Lock size={12} /> : <Unlock size={12} />}
                      PCI-DSS
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Auto-Renewal & Installment Warnings */}
      {(hasAutoRenewal || hasInstallment) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {hasAutoRenewal && (
            <div className="bento-card p-4 border-amber-500/20">
              <div className="flex items-center gap-3 mb-2">
                <RefreshCw size={18} className="text-amber-400" />
                <span className="font-bold text-sm text-amber-300">Auto-Renewal Active</span>
              </div>
              <p className="text-xs text-slate-400">
                Some payment methods auto-renew subscriptions. Users must manually cancel to avoid recurring charges.
              </p>
            </div>
          )}
          {hasInstallment && (
            <div className="bento-card p-4 border-purple-500/20">
              <div className="flex items-center gap-3 mb-2">
                <CreditCard size={18} className="text-purple-400" />
                <span className="font-bold text-sm text-purple-300">Installment Payments Available</span>
              </div>
              <p className="text-xs text-slate-400">
                Installment plans retain payment data longer and may auto-charge. Failed payments could affect credit.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Payment Methods Detail */}
      {data.list.map((gw, i) => {
        const risk = riskColors[gw.riskLevel] || riskColors.Low;
        return (
          <div key={i} className={`bento-card overflow-hidden ${risk.border}`}>
            <div className="p-5 border-b border-slate-700/30 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-xl bg-slate-800/80">
                  <CreditCard size={18} className="text-indigo-400" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white">{gw.paymentMethod}</h3>
                  <p className="text-xs text-slate-500">Provider: {gw.provider}</p>
                </div>
              </div>
              <span className={`text-xs px-3 py-1 rounded-full font-bold ${risk.bg} ${risk.text}`}>
                {gw.riskLevel} Risk
              </span>
            </div>

            <div className="p-5 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <SecurityDetail label="Encryption" value={gw.encryptionStandard} ok={true} />
              <SecurityDetail label="PCI-DSS Compliant" value={gw.pciDssCompliant ? 'Yes' : 'No'} ok={gw.pciDssCompliant} />
              <SecurityDetail label="Fraud Detection" value={gw.fraudDetection ? 'Yes' : 'No'} ok={gw.fraudDetection} />
              <SecurityDetail label="Auto-Renewal" value={gw.autoRenewal ? 'Enabled' : 'Disabled'} ok={!gw.autoRenewal} />
              <SecurityDetail label="Cancellation" value={gw.cancellationDifficulty} ok={gw.cancellationDifficulty === 'Easy'} />
              <SecurityDetail label="Installments" value={gw.installmentAvailable ? 'Available' : 'Not Available'} ok={!gw.installmentAvailable} />

              {gw.fraudDetectionDetails && (
                <div className="sm:col-span-2">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Fraud Detection Details</span>
                  <p className="text-sm text-slate-300 mt-1">{gw.fraudDetectionDetails}</p>
                </div>
              )}

              {gw.chargebackPolicy && (
                <div className="sm:col-span-2">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Chargeback Policy</span>
                  <p className="text-sm text-slate-300 mt-1">{gw.chargebackPolicy}</p>
                </div>
              )}

              {gw.installmentDetails && (
                <div className="sm:col-span-2">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Installment Details</span>
                  <p className="text-sm text-slate-300 mt-1">{gw.installmentDetails}</p>
                </div>
              )}

              {gw.dataRetainedAfterPayment && (
                <div className="sm:col-span-2">
                  <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Data Retained After Payment</span>
                  <p className="text-sm text-slate-300 mt-1">{gw.dataRetainedAfterPayment}</p>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function SecurityDetail({ label, value, ok }) {
  return (
    <div className="flex items-center gap-2">
      <span className={`w-2 h-2 rounded-full ${ok ? 'bg-emerald-400' : 'bg-amber-400'}`} />
      <div>
        <span className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">{label}</span>
        <p className="text-sm text-slate-200 font-medium">{value}</p>
      </div>
    </div>
  );
}
