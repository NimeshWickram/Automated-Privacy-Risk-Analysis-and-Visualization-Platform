import { apiFetch } from '../api';
import { useState } from 'react';

export default function ProvenanceFindings({ data, appId, onUpdated }) {
  const [selectedRun, setSelectedRun] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  if (!data || data.status !== 'available') {
    return <div className="bento-card p-5 text-amber-300">Legacy analysis — finding provenance is unverified. Re-analyze the APK after applying the provenance migration. Existing records are preserved.</div>;
  }
  const run = data.runs.find(item => item.id === selectedRun) ?? data.runs.at(-1);
  const findings = data.findings.filter(item => item.runId === run?.id);
  const ablate = async () => {
    setBusy(true);
    setError('');
    try {
      const response = await apiFetch(`http://localhost:8000/api/apps/${appId}/ablation`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source_run_id: run.id, configurations: ['A', 'B', 'C', 'D', 'E'] }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Ablation failed');
      onUpdated(result.provenance);
      setSelectedRun(result.run_ids.at(-1));
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-400">Static evidence does not prove runtime collection. Evidence Strength Score is a fixed rule-based score, not a probability of a privacy violation.</p>
      <label className="block text-sm text-slate-300">Analysis run
        <select value={run?.id ?? ''} disabled={busy} onChange={event => setSelectedRun(Number(event.target.value))} className="block mt-2 w-full rounded-lg bg-slate-900 border border-slate-700 p-2">
          {data.runs.map(item => <option key={item.id} value={item.id}>Run {item.id} — {item.configuration ? `Configuration ${item.configuration}` : 'Phase 1'} — {item.startedAt}</option>)}
        </select>
      </label>
      {run && <div className="bento-card p-4 text-xs text-slate-400 break-all space-y-2">
        <p>Run {run.id} · Version {run.applicationVersion} · {run.analysisVersion}</p>
        <p>APK SHA-256: {run.apkSha256}</p>
        <p>Source coverage: {Object.entries(run.sourceStatus).filter(([source]) => source !== 'enabled_sources').map(([source, status]) => `${source}: ${status}`).join(' · ')}</p>
        {run.analysisConfigurationId && <>
          <p>Configuration {run.configuration}: {run.enabledSources.join(' + ')}</p>
          <p>Configuration ID: {run.analysisConfigurationId}</p>
          <p>{run.ontologyVersion} · {run.ruleVersion}</p>
          <p>Normalized input SHA-256: {run.normalizedInputSha256}</p>
          <p>Semantic output SHA-256: {run.semanticOutputSha256}</p>
          {run.replayOfRunId && <p>Replayed from run {run.replayOfRunId}</p>}
          <p>Ablation reuses the saved acquisition bundle and varies admitted sources. It does not measure acquisition time. Unavailable sources remain unavailable.</p>
          <button disabled={busy} onClick={ablate} className="rounded-lg bg-indigo-600 px-3 py-2 text-white disabled:opacity-50">{busy ? 'Running configurations…' : 'Run ablation A–E'}</button>
        </>}
      </div>}
      {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
      {run?.normalizedEvidence && <details className="bento-card p-4">
        <summary className="cursor-pointer text-slate-200">Normalized evidence ({run.normalizedEvidence.length})</summary>
        <p className="mt-2 text-xs text-slate-400">Raw observations and explicit category/claim annotations are retained separately from findings. Annotations require review and are not ground truth.</p>
        {run.normalizedEvidence.map(item => <details key={item.id} className="mt-3 p-3 bg-slate-900/50 rounded-lg">
          <summary className="cursor-pointer text-sm text-indigo-300">#{item.evidenceSourceId} · {item.source} · {item.behavior ?? item.claim} · {item.data_category}</summary>
          <p className="mt-2 text-xs text-slate-400 break-all">{item.file_reference}</p>
          <pre className="mt-2 text-xs text-slate-300 whitespace-pre-wrap break-all">{item.raw_evidence}</pre>
          <pre className="mt-2 text-xs text-slate-400 whitespace-pre-wrap break-all">{JSON.stringify(item.attributes, null, 2)}</pre>
        </details>)}
      </details>}
      {!findings.length && <p className="text-slate-400">No supported findings generated in this run. This does not establish absence of privacy risks.</p>}
      {findings.map(finding => <article key={finding.id} className="bento-card p-5 space-y-3">
        <h3 className="font-semibold text-slate-100">{finding.category}: {finding.dataCategory}</h3>
        <p className="text-sm text-slate-300"><strong>Interpretation:</strong> {finding.interpretation}</p>
        <p className="text-xs text-slate-500">Rule: {finding.ruleId}</p>
        <p className="text-xs text-slate-400">Evidence Strength Score: {finding.evidenceStrengthScore == null ? 'Not assigned (Phase 1)' : finding.evidenceStrengthScore.toFixed(2)}{finding.severity ? ` · Rule-based severity: ${finding.severity}` : ''}</p>
        {finding.domain && <p className="text-xs text-slate-400 break-all">Destination: {finding.domain}</p>}
        {finding.evidence.map(link => <details key={`${link.evidenceSourceId}-${link.relationship}`} className="rounded-lg bg-slate-900/50 p-3">
          <summary className="cursor-pointer text-sm text-indigo-300">{link.relationship} — Evidence #{link.evidenceSourceId}: {link.observation.observation_kind}</summary>
          <p className="mt-3 text-sm text-slate-300"><strong>Observation:</strong> {link.observation.description}</p>
          <p className="text-xs text-slate-400">{link.observation.file_reference}{link.observation.line_number ? `:${link.observation.line_number}` : ''}</p>
          <p className="text-xs text-slate-400">{link.analyzer} · {link.capturedAt}</p>
          <pre className="mt-2 whitespace-pre-wrap break-all text-xs text-slate-300">{link.observation.raw_evidence}</pre>
          <p className="mt-2 text-xs text-slate-500 break-all">Snapshot SHA-256: {link.snapshotSha256}</p>
          <p className="text-xs text-slate-400">{link.rationale}</p>
        </details>)}
      </article>)}
    </div>
  );
}
