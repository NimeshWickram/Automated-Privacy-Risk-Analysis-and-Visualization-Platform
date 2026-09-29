import { apiFetch } from '../api';
import { useId, useState } from 'react';

const COLUMN = { RISK_FINDING: 0, EVIDENCE_SOURCE: 1, DATA_CATEGORY: 2, SDK: 3, DOMAIN: 3 };

function GraphCanvas({ graph, selected, onSelect }) {
  const marker = useId().replaceAll(':', '');
  const counts = [0, 0, 0, 0];
  const positions = Object.fromEntries(graph.nodes.map(node => {
    const column = COLUMN[node.type];
    return [node.id, { x: 20 + column * 350, y: 65 + counts[column]++ * 95 }];
  }));
  const height = Math.max(260, Math.max(...counts) * 95 + 80);
  return <div className="overflow-auto max-h-[650px] rounded-xl border border-slate-700 bg-slate-950/50">
    <svg width="1420" height={height} role="img" aria-label="Privacy evidence graph. Select a node to inspect its source or interpretation.">
      <defs><marker id={marker} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8" /></marker></defs>
      {['Derived findings', 'Observed source records', 'Derived categories', 'Observed SDKs / domains'].map((label, index) => <text key={label} x={20 + index * 350} y="28" fill="#cbd5e1" fontSize="13">{label}</text>)}
      {graph.edges.map(edge => {
        const start = positions[edge.source], end = positions[edge.target];
        const forward = end.x > start.x;
        const fromX = start.x + (forward ? 285 : 0), toX = end.x + (forward ? 0 : 285);
        const active = !selected || selected === edge.source || selected === edge.target;
        return <g key={edge.id} opacity={active ? 0.8 : 0.12}>
          <path d={`M${fromX},${start.y + 30} C${(fromX + toX) / 2},${start.y + 30} ${(fromX + toX) / 2},${end.y + 30} ${toX},${end.y + 30}`} stroke={edge.relation === 'CONTRADICTED_BY' ? '#f87171' : '#94a3b8'} fill="none" strokeWidth="1.5" markerEnd={`url(#${marker})`}>
            <title>{edge.relation}: {edge.qualification}</title>
          </path>
        </g>;
      })}
      {graph.nodes.map(node => {
        const position = positions[node.id];
        const color = node.layer === 'OBSERVED' ? '#38bdf8' : '#c084fc';
        return <g key={node.id} transform={`translate(${position.x},${position.y})`} role="button" tabIndex="0" aria-label={`${node.layer}: ${node.label}`} aria-pressed={selected === node.id} onClick={() => onSelect(node.id)} onKeyDown={event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); onSelect(node.id); } }} className="cursor-pointer outline-none">
          <title>{node.label}</title>
          <rect width="285" height="62" rx="8" fill={selected === node.id ? '#243047' : '#0f172a'} stroke={color} strokeWidth={selected === node.id ? 3 : 1} />
          <text x="12" y="20" fill={color} fontSize="10">{node.layer} · {node.type}</text>
          <text x="12" y="43" fill="#e2e8f0" fontSize="12">{node.label.length > 36 ? node.label.slice(0, 33) + '…' : node.label}</text>
        </g>;
      })}
    </svg>
  </div>;
}

export default function PrivacyEvidenceGraph({ appId, provenance }) {
  const [runId, setRunId] = useState(null);
  const [graph, setGraph] = useState(null);
  const [selected, setSelected] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const runs = (provenance?.runs ?? []).filter(run => run.analysisConfigurationId);
  const run = runs.find(item => item.id === runId) ?? runs.at(-1);
  const node = graph?.nodes.find(item => item.id === selected);
  const load = async () => {
    setBusy(true); setError(''); setGraph(null); setSelected(null);
    try {
      const response = await apiFetch(`http://localhost:8000/api/apps/${appId}/runs/${run.id}/graph`, { method: 'POST' });
      const result = await response.json();
      if (!response.ok) throw new Error(typeof result.detail === 'string' ? result.detail : 'Graph validation failed');
      setGraph(result);
    } catch (failure) {
      setError(failure.message);
    } finally {
      setBusy(false);
    }
  };
  if (!runs.length) return <div className="bento-card p-5 text-sm text-amber-300">A Phase 2 analysis is required to build an evidence-backed graph. Legacy records are preserved and are not automatically converted into graph claims.</div>;
  return <div className="space-y-4">
    <p className="text-sm text-slate-300">Each graph belongs to one application version and analysis run. Blue nodes identify observed records or entities; purple nodes identify derived categories or findings.</p>
    <p className="text-sm text-amber-200">Static API references do not prove runtime access. A shared data category does not prove that code sent data to a domain. Payload and disclosure annotations require review.</p>
    <label className="block text-sm text-slate-300">Version / analysis run
      <select disabled={busy} value={run.id} onChange={event => { setRunId(Number(event.target.value)); setGraph(null); setSelected(null); setError(''); }} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 p-2">
        {runs.map(item => <option key={item.id} value={item.id}>Version {item.applicationVersion} · Run {item.id} · Configuration {item.configuration} · APK {item.apkSha256.slice(0, 12)}</option>)}
      </select>
    </label>
    <button onClick={load} disabled={busy} className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white disabled:opacity-50">{busy ? 'Validating graph…' : 'Open validated graph'}</button>
    <p className="text-xs text-slate-400">Creates a graph from this run's retained evidence if needed; otherwise verifies the saved graph. It does not acquire new evidence.</p>
    {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
    {graph && <>
      <div className="bento-card p-4 text-xs text-slate-400 space-y-2 break-all">
        <p>Version ID {graph.app_version_id} · Run {graph.run_id} · Configuration {graph.configuration} · {graph.graph_version}</p>
        <p>APK SHA-256: {graph.apk_sha256}</p><p>Graph SHA-256: {graph.graph_sha256}</p>
        <p>Enabled sources: {graph.enabled_sources.join(', ')}</p>
        <p>Coverage: {Object.entries(graph.source_status).filter(([key]) => key !== 'enabled_sources').map(([key, value]) => `${key}: ${value}`).join(' · ')}</p>
        <p>{graph.nodes.length} nodes · {graph.edges.length} evidence-backed relations · {graph.omitted_evidence.length} observations without a justified graph relation</p>
      </div>
      {graph.nodes.length > 0 ? <GraphCanvas graph={graph} selected={selected} onSelect={setSelected} /> : <p className="text-sm text-slate-400">No justified graph relations for this run. This does not establish absence of privacy risks.</p>}
      <label className="block text-sm text-slate-300">Inspect a node
        <select value={selected ?? ''} onChange={event => setSelected(event.target.value || null)} className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-900 p-2">
          <option value="">All nodes / relations</option>
          {graph.nodes.map(item => <option key={item.id} value={item.id}>{item.layer} · {item.label}</option>)}
        </select>
      </label>
      {node && <div className="bento-card p-4 space-y-2">
        <h3 className="font-semibold text-slate-100">{node.label}</h3>
        {node.type === 'EVIDENCE_SOURCE' && <p className="text-xs text-slate-400">Evidence source #{graph.evidence_source_ids[node.data.id]} · {node.data.file_reference}</p>}
        {node.type === 'RISK_FINDING' && <p className="text-sm text-slate-300">Interpretation: {node.data.interpretation} Evidence Strength Score: {node.data.evidence_strength_score.toFixed(2)} (rule-based; not a probability).</p>}
        <pre className="max-h-80 overflow-auto text-xs text-slate-300 whitespace-pre-wrap break-all">{JSON.stringify(node.data, null, 2)}</pre>
      </div>}
      <div className="bento-card p-4 space-y-3">
        <h3 className="font-semibold text-slate-100">Relations and supporting observations</h3>
        {graph.edges.filter(edge => !selected || edge.source === selected || edge.target === selected).map(edge => <details key={edge.id} className="rounded-lg bg-slate-900/50 p-3">
          <summary className="cursor-pointer text-sm text-indigo-300">{edge.relation} · Evidence #{graph.evidence_source_ids[edge.evidence_id]}</summary>
          <p className="mt-2 text-sm text-slate-300">{graph.explanations.find(path => path.edge_ids.length === 1 && path.edge_ids[0] === edge.id)?.text}</p>
          <button onClick={() => setSelected(`EVIDENCE_SOURCE:${edge.evidence_id}`)} className="mt-2 text-xs text-sky-300 underline">Inspect supporting evidence</button>
        </details>)}
      </div>
      <details className="bento-card p-4">
        <summary className="cursor-pointer text-slate-200">Payload transmission paths</summary>
        {!graph.explanations.some(path => path.edge_ids.length > 1) && <p className="mt-2 text-sm text-slate-400">No supported payload transmission path in this run.</p>}
        {graph.explanations.filter(path => path.edge_ids.length > 1).map(path => <p key={path.edge_ids.join('-')} className="mt-3 text-sm text-slate-300">{path.text}</p>)}
      </details>
      {graph.omitted_evidence.length > 0 && <details className="bento-card p-4"><summary className="cursor-pointer text-slate-200">Observations retained outside the graph</summary>{graph.omitted_evidence.map(item => <p key={item.evidence_id} className="mt-2 text-xs text-slate-400">Evidence #{graph.evidence_source_ids[item.evidence_id]}: {item.reason} Inspect it in Findings & Provenance.</p>)}</details>}
    </>}
  </div>;
}
