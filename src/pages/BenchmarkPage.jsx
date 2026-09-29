import { useState } from 'react';
import { apiFetch } from '../api';

const labels = ['CAPABILITY','POTENTIAL_ACCESS','ACTUAL_ACCESS','POTENTIAL_TRANSMISSION','DISCLOSURE_INCONSISTENCY','UNNECESSARY_PERMISSION'];
const categories = ['LOCATION','CONTACTS','DEVICE_IDENTIFIER','ADVERTISING_IDENTIFIER','CAMERA','MICROPHONE','PERSONAL_INFORMATION','EMAIL','NAME','AGE','SCHOOL_INFORMATION','ACADEMIC_DATA','BEHAVIORAL_DATA'];
const inputClass = 'w-full mt-1 rounded-lg border border-slate-700 bg-slate-950 p-2 text-sm text-slate-100';
const buttonClass = 'rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white disabled:opacity-50';

function Form({ title, fields, submit }) {
  const [values, setValues] = useState({});
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  return <details className="bento-card p-4"><summary className="cursor-pointer font-semibold text-slate-100">{title}</summary>
    <form className="mt-4 space-y-3" onSubmit={async event => {
      event.preventDefault(); setBusy(true); setMessage('');
      try { const result = await submit(values); setMessage(JSON.stringify(result, null, 2)); }
      catch (error) { setMessage(error.message); }
      finally { setBusy(false); }
    }}>
      {fields.map(field => <label key={field.key} className="block text-sm text-slate-300">{field.label}
        {field.options ? <select required className={inputClass} value={values[field.key] ?? ''} onChange={event => setValues({ ...values, [field.key]: event.target.value })}><option value="">Select…</option>{field.options.map(option => <option key={option} value={option}>{option}</option>)}</select>
          : field.checkbox ? <input type="checkbox" className="ml-3" checked={!!values[field.key]} onChange={event => setValues({ ...values, [field.key]: event.target.checked })} />
          : field.multiline ? <textarea required={!field.optional} rows="4" className={inputClass} value={values[field.key] ?? ''} onChange={event => setValues({ ...values, [field.key]: event.target.value })} />
          : <input required={!field.optional} type={field.password ? 'password' : 'text'} className={inputClass} value={values[field.key] ?? ''} onChange={event => setValues({ ...values, [field.key]: event.target.value })} />}
      </label>)}
      <button disabled={busy} className={buttonClass}>{busy ? 'Saving…' : title}</button>
      {message && <pre role="status" className="max-h-72 overflow-auto whitespace-pre-wrap break-all text-xs text-slate-300">{message}</pre>}
    </form>
  </details>;
}

const field = (key, label, extra = {}) => ({ key, label, ...extra });
const numberList = value => value.split(',').map(item => Number(item.trim()));
const metric = value => value == null ? 'N/A' : value.toFixed(4);

export default function BenchmarkPage() {
  const [catalog, setCatalog] = useState(null);
  const [datasetId, setDatasetId] = useState('');
  const [versionId, setVersionId] = useState('');
  const [result, setResult] = useState(null);
  const [experiment, setExperiment] = useState(null);
  const [error, setError] = useState('');
  const [errorFilter, setErrorFilter] = useState('FP');
  const [audit, setAudit] = useState(null);
  const dataset = catalog?.datasets.find(item => item.id === Number(datasetId));
  const versions = catalog?.versions.filter(item => item.dataset_id === Number(datasetId)) ?? [];
  const call = async (path, data) => {
    const response = await apiFetch(`/api/benchmark${path}`, data ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) } : {});
    const body = await response.json();
    if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail));
    return body;
  };
  const refresh = async () => { const value = await call(''); setCatalog(value); return value; };
  const mutate = async (path, data) => { const value = await call(path, data); await refresh(); return value; };
  const attempt = async operation => { setError(''); try { await operation(); } catch (failure) { setError(failure.message); } };
  const download = async format => {
    const response = await apiFetch(`/api/benchmark/evaluations/${result.id}/export?format=${format}`);
    if (!response.ok) throw new Error('Export failed');
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a'); link.href = url; link.download = `privacyguard-evaluation-${result.id}.${format}`; link.click(); URL.revokeObjectURL(url);
  };
  return <div className="max-w-7xl mx-auto px-4 space-y-5">
    <h1 className="text-2xl font-bold text-slate-100">Research benchmark</h1>
    <p className="text-sm text-slate-300">Independent evidence and blinded reviews establish ground truth. Automated findings never become truth automatically. Freeze the reviewed dataset before evaluating a single configuration or running ablation.</p>
    <div className="grid md:grid-cols-2 gap-4">
      <div className="bento-card p-4"><h2 className="font-semibold text-slate-100">Implementation validation</h2><p className="mt-2 text-sm text-slate-400">SYNTHETIC evaluations test software behavior. They are not empirical accuracy. Test-suite evidence is recorded in the phase deliverables.</p></div>
      <div className="bento-card p-4"><h2 className="font-semibold text-slate-100">Empirical evaluation</h2><p className="mt-2 text-sm text-slate-400">{catalog?.empirical_status ?? 'N/A — benchmark dataset not yet evaluated'}</p></div>
    </div>
    <Form title="Connect as researcher" fields={[field('key','Researcher key', { password: true })]} submit={async values => { sessionStorage.setItem('privacyguard-research-key', values.key); await refresh(); return { connected: true }; }} />
    <p className="text-xs text-slate-400">Configure PRIVACYGUARD_RESEARCH_KEY on both backend services first. The key is held in this browser tab's session storage. Give reviewers only their assignment token and a separate browser profile/device. The reviewer API runs separately, normally on port 8001.</p>
    <button className={buttonClass} onClick={() => { sessionStorage.removeItem('privacyguard-research-key'); setCatalog(null); setResult(null); setExperiment(null); setAudit(null); }}>Clear researcher credential</button>
    {error && <p role="alert" className="text-red-300">{error}</p>}
    {catalog && <>
      <div className="flex flex-wrap gap-3">
        <label className="text-sm text-slate-300">Dataset<select className={inputClass} value={datasetId} onChange={event => { setDatasetId(event.target.value); setVersionId(''); setResult(null); }}><option value="">Select dataset…</option>{catalog.datasets.map(item => <option key={item.id} value={item.id}>{item.name} / {item.version} / {item.dataset_type}{item.frozen_at ? ' / FROZEN' : ''}</option>)}</select></label>
        <label className="text-sm text-slate-300">Benchmark version<select className={inputClass} value={versionId} onChange={event => setVersionId(event.target.value)}><option value="">Select version…</option>{versions.map(item => <option key={item.id} value={item.id}>#{item.id} · {item.application_version} · {item.apk_sha256.slice(0,12)}{item.sealed_at ? ' · SEALED' : ''}</option>)}</select></label>
        <button className={buttonClass} onClick={() => attempt(refresh)}>Refresh records</button>
      </div>
      <Form title="Create dataset protocol" fields={[field('name','Dataset name'),field('version','Dataset version'),field('dataset_type','Dataset type',{ options:['SYNTHETIC','REAL_WORLD'] }),field('finding_categories',`Finding labels, comma separated: ${labels.join(', ')}`),field('data_categories',`Data categories, comma separated: ${categories.join(', ')}`),field('protocol_rationale','Scope, sampling and label-universe rationale',{multiline:true}),field('actor','Researcher identity')]} submit={values => mutate('/datasets',{...values,finding_categories:values.finding_categories.split(',').map(value=>value.trim()),data_categories:values.data_categories.split(',').map(value=>value.trim())})} />
      {dataset && <Form key={`version-${datasetId}`} title="Register benchmark APK version" fields={[field('name','Application name'),field('package_name','Verified package name'),field('application_version','Application version'),field('apk_sha256','APK SHA-256'),field('artifact_path','Retained APK absolute path (required for REAL_WORLD; under backend/uploads or backend/benchmark_artifacts)',{optional:true}),field('eligibility_source','Free educational eligibility source'),field('eligibility_notes','Eligibility verification and provenance notes',{multiline:true}),field('free_educational_verified','I verified that this is a free educational Android application',{checkbox:true}),field('actor','Researcher identity')]} submit={values => mutate(`/datasets/${datasetId}/versions`,{...values,artifact_path:values.artifact_path || null,free_educational_verified:!!values.free_educational_verified})} />}
      {versionId && <Form key={`evidence-${versionId}`} title="Add independent evidence" fields={[field('source','Source',{options:['MANIFEST','CODE','SDK','NETWORK','POLICY','DATA_SAFETY','RUNTIME','MANUAL_INSPECTION']}),field('raw_evidence','Raw observation/artifact excerpt (exclude automated findings and annotations)',{multiline:true}),field('file_reference','Exact artifact/file reference'),field('artifact_sha256','Artifact SHA-256'),field('independent_and_prediction_free','This evidence was curated independently and contains no automated predictions',{checkbox:true}),field('actor','Evidence curator')]} submit={values => mutate(`/versions/${versionId}/evidence`,values)} />}
      <h2 className="text-lg font-semibold text-slate-100">Independent review</h2>
      <Form title="Register reviewer" fields={[field('identity','Reviewer identity'),field('qualifications','Reviewer qualifications/metadata',{multiline:true}),field('actor','Registering researcher')]} submit={values => mutate('/reviewers',{identity:values.identity,metadata:{qualifications:values.qualifications},actor:values.actor})} />
      <p className="text-sm text-slate-400">Reviewers: {catalog.reviewers.map(item => `${item.id}: ${item.identity}`).join(' · ') || 'None registered'}</p>
      {versionId && <Form key={`assign-${versionId}`} title="Assign blinded review" fields={[field('reviewer_id','Reviewer ID'),field('actor','Assigning researcher')]} submit={async values => { const assignment = await mutate(`/versions/${versionId}/assignments`,{...values,reviewer_id:Number(values.reviewer_id)}); return {...assignment,reviewer_page:`${window.location.origin}/review#${assignment.review_token}`,instruction:'Share privately with the assigned reviewer only. Token is shown once.'}; }} />}
      <p className="text-sm text-slate-400">Submitted reviews for this version: {catalog.reviews.filter(item => item.version_id===Number(versionId)).map(item=>`Review ${item.id} / assignment ${item.assignment_id}`).join(' · ') || 'None'}</p>
      {versionId && <Form key={`seal-${versionId}`} title="Approve independent ground truth" fields={[field('review_ids','Two independent review IDs, comma separated'),field('adjudicator_review_id','Third review ID if the first two disagree',{optional:true}),field('approval_reason','Researcher approval rationale',{multiline:true}),field('actor','Approving researcher')]} submit={values => mutate(`/versions/${versionId}/seal`,{...values,review_ids:numberList(values.review_ids),adjudicator_review_id:values.adjudicator_review_id ? Number(values.adjudicator_review_id) : null})} />}
      {dataset && <Form key={`freeze-${datasetId}`} title="Freeze reviewed dataset" fields={[field('actor','Researcher identity')]} submit={values => mutate(`/datasets/${datasetId}/freeze`,values)} />}
      <h2 className="text-lg font-semibold text-slate-100">Evaluation and ablation</h2>
      <p className="text-sm text-slate-400">Every frozen dataset version must be selected. Use one configuration per evaluation. Ablation holds the reviewed dataset fixed and replays the selected acquisition bundles.</p>
      {dataset && <Form key={`eval-${datasetId}`} title="Run evaluation or ablation" fields={[field('mode','Operation',{options:['Evaluate selected runs','A–E ablation']}),...versions.map(item=>field(`run_${item.id}`,`Analysis run ID for benchmark version ${item.id} (${item.apk_sha256.slice(0,12)}…)`)),field('actor','Researcher identity')]} submit={async values => {
        const response = await mutate(`/datasets/${datasetId}/${values.mode==='A–E ablation' ? 'ablation' : 'evaluate'}`, {dataset_type:dataset.dataset_type,selections:versions.map(item=>({benchmark_version_id:item.id,analysis_run_id:Number(values[`run_${item.id}`])})),actor:values.actor});
        if (response.results) setResult(response); return response.results ? {evaluation_id:response.id,dataset_type:response.dataset_type} : response;
      }} />}
      <div className="flex flex-wrap gap-2">{catalog.evaluations.filter(item=>!datasetId || item.dataset_id===Number(datasetId)).map(item=><button key={item.id} className={buttonClass} onClick={()=>attempt(async()=>setResult(await call(`/evaluations/${item.id}`)))}>Evaluation {item.id} · {item.dataset_type}</button>)}</div>
      <div className="flex flex-wrap gap-2">{catalog.ablations.filter(item=>!datasetId || item.dataset_id===Number(datasetId)).map(item=><button key={item.id} className={buttonClass} onClick={()=>attempt(async()=>setExperiment(await call(`/ablations/${item.id}`)))}>Ablation experiment {item.id}</button>)}</div>
      {experiment && <div className="bento-card p-4 overflow-auto"><h3 className="font-semibold text-slate-100">Ablation {experiment.id} · {experiment.dataset_type}</h3><p className="my-3 text-xs text-slate-400">{experiment.scope}</p><table className="w-full text-sm text-left text-slate-300"><thead><tr><th>Configuration</th><th>Precision (micro)</th><th>Recall (micro)</th><th>F1 (micro)</th><th>TP / FP / FN / TN</th></tr></thead><tbody>{Object.entries(experiment.evaluations).map(([preset,value])=><tr key={preset}><td className="py-2">{preset}</td><td>{metric(value.results.micro.precision)}</td><td>{metric(value.results.micro.recall)}</td><td>{metric(value.results.micro.f1)}</td><td>{['TP','FP','FN','TN'].map(key=>value.results.micro[key]).join(' / ')}</td></tr>)}</tbody></table></div>}
      {result && <>
        <h2 className="text-lg font-semibold text-slate-100">Evaluation {result.id} — {result.dataset_type} — {result.validation_type}</h2>
        <p className="text-sm text-slate-400">{result.results.evaluated_units} reviewed units scored; {result.results.uncertain_units} uncertain units excluded. {result.results.undefined_policy}</p>
        <div className="overflow-auto bento-card p-4"><table className="w-full text-sm text-left text-slate-300"><thead><tr><th>Metric</th><th>Micro</th><th>Macro</th><th>Defined labels</th></tr></thead><tbody>{['precision','recall','f1','false_positive_rate','false_negative_rate'].map(key=><tr key={key}><td className="py-2">{key}</td><td>{metric(result.results.micro[key])}</td><td>{metric(result.results.macro[key].value)}</td><td>{result.results.macro[key].defined_labels}/{result.results.macro[key].total_labels}</td></tr>)}</tbody></table>
          <p className="mt-3">{['TP','FP','FN','TN'].map(key=>`${key}: ${result.results.micro[key]}`).join(' · ')}</p>
        </div>
        <h3 className="font-semibold text-slate-100">Error analysis</h3>
        <select className={inputClass} value={errorFilter} onChange={event=>setErrorFilter(event.target.value)}>{['FP','FN','TP','TN','EXCLUDED_UNCERTAIN'].map(value=><option key={value}>{value}</option>)}</select>
        {result.results.units.filter(unit=>unit.classification===errorFilter).map(unit=><details key={`${unit.version_id}-${unit.finding_category}-${unit.data_category}`} className="bento-card p-3"><summary className="cursor-pointer text-sm text-slate-200">Version {unit.version_id} · {unit.finding_category} · {unit.data_category} · {unit.classification}</summary><pre className="mt-2 whitespace-pre-wrap break-all text-xs text-slate-400">{JSON.stringify(unit,null,2)}</pre></details>)}
        <h3 className="font-semibold text-slate-100">Reproducibility and research export</h3>
        <Form key={`error-note-${result.id}`} title="Record FP/FN cause analysis" fields={[field('version_id','Benchmark version ID'),field('finding_category','Finding category'),field('data_category','Data category'),field('cause_analysis','Evidence-backed cause hypothesis and limitations',{multiline:true}),field('actor','Researcher identity')]} submit={values=>mutate(`/evaluations/${result.id}/error-notes`,{...values,version_id:Number(values.version_id)})} />
        <p className="text-xs text-slate-400 break-all">Snapshot SHA-256: {result.snapshot_sha256}</p>
        <div className="flex gap-2">{['json','csv'].map(format=><button key={format} className={buttonClass} onClick={()=>attempt(()=>download(format))}>Export {format.toUpperCase()}</button>)}</div>
        <details className="bento-card p-4"><summary className="cursor-pointer text-slate-200">Full results, predictions, reviews and reproducibility manifest</summary><pre className="max-h-96 overflow-auto whitespace-pre-wrap break-all text-xs text-slate-400">{JSON.stringify(result,null,2)}</pre></details>
      </>}
      <button className={buttonClass} onClick={()=>attempt(async()=>setAudit(await call('/audit')))}>Read reviewer audit trail</button>
      {audit && <pre className="bento-card p-4 max-h-96 overflow-auto whitespace-pre-wrap break-all text-xs text-slate-400">{JSON.stringify(audit,null,2)}</pre>}
    </>}
  </div>;
}
