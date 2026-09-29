import { useState } from 'react';

const base = import.meta.env.VITE_REVIEW_API || 'http://localhost:8001';
const style = 'mt-1 w-full rounded border border-slate-700 bg-slate-900 p-2 text-sm text-slate-100';
const defaults = {decision:'UNCERTAIN',observation:'',interpretation:'',observation_status:'UNKNOWN',access_status:'UNKNOWN',transmission_status:'UNKNOWN',disclosure_status:'UNKNOWN',evidence_ids:[]};
const options = {decision:['UNCERTAIN','POSITIVE','NEGATIVE'],observation_status:['UNKNOWN','OBSERVED','NOT_OBSERVED'],access_status:['UNKNOWN','CAPABILITY_ONLY','STATIC_REFERENCE','OBSERVED','NOT_OBSERVED','NOT_APPLICABLE'],transmission_status:['UNKNOWN','OBSERVED','NOT_OBSERVED','NOT_APPLICABLE'],disclosure_status:['UNKNOWN','CONSISTENT','INCONSISTENT','NOT_APPLICABLE']};

export default function ReviewerPage() {
  const [token,setToken]=useState(()=>window.location.hash.slice(1));
  const [packet,setPacket]=useState(null);
  const [units,setUnits]=useState([]);
  const [attest,setAttest]=useState(false);
  const [message,setMessage]=useState('');
  const [busy,setBusy]=useState(false);
  const request=async(data)=>{
    const response=await fetch(`${base}/api/review`,{method:data?'POST':'GET',headers:{Authorization:`Bearer ${token}`,'Content-Type':'application/json'},...(data?{body:JSON.stringify(data)}:{})});
    const result=await response.json();if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:JSON.stringify(result.detail));return result;
  };
  const update=(index,key,value)=>setUnits(previous=>previous.map((unit,i)=>i===index?{...unit,[key]:value}:unit));
  return <main className="min-h-screen bg-slate-950 p-5"><div className="max-w-4xl mx-auto space-y-5">
    <h1 className="text-2xl font-bold text-slate-100">Independent blinded review</h1>
    <p className="text-sm text-slate-300">Review raw evidence independently. Permission declarations show capability; static API references do not establish execution; domains alone do not show sensitive transmission. Use UNCERTAIN when coverage is insufficient. This review service provides no automated predictions.</p>
    <form onSubmit={async event=>{event.preventDefault();setBusy(true);setMessage('');try{const value=await request();setPacket(value);setUnits(value.units.map(unit=>({...defaults,...unit,evidence_ids:[]})));window.history.replaceState(null,'',window.location.pathname);}catch(error){setMessage(error.message);}finally{setBusy(false);}}} className="space-y-2">
      <label className="block text-sm text-slate-300">Assignment token<input type="password" required className={style} value={token} onChange={event=>{setToken(event.target.value);setPacket(null);}} /></label>
      <button disabled={busy} className="rounded bg-indigo-600 px-4 py-2 text-white">Open assigned evidence</button>
    </form>
    {message && <p role="status" className="text-sm text-amber-200">{message}</p>}
    {packet && <>
      <p className="text-slate-200">Reviewer: {packet.reviewer} · {packet.submitted?'Submitted — immutable':'Pending independent review'}</p>
      <pre className="text-xs text-slate-400 whitespace-pre-wrap break-all">{JSON.stringify(packet.application,null,2)}</pre>
      {packet.evidence.map(item=><details key={item.id} className="rounded-lg border border-slate-700 p-3"><summary className="cursor-pointer text-sky-300">Evidence {item.id} · {item.source}</summary><p className="mt-2 text-xs text-slate-400 break-all">{item.file_reference} · SHA-256 {item.artifact_sha256}</p><pre className="mt-2 text-sm text-slate-300 whitespace-pre-wrap break-all">{item.raw_evidence}</pre></details>)}
      {!packet.submitted && <form className="space-y-5" onSubmit={async event=>{event.preventDefault();setBusy(true);setMessage('');try{await request({independent_review:attest,predictions_not_seen:attest,units});setPacket({...packet,submitted:true});setMessage('Independent review submitted.');}catch(error){setMessage(error.message);}finally{setBusy(false);}}}>
        {units.map((unit,index)=><fieldset key={`${unit.finding_category}-${unit.data_category}`} className="rounded-xl border border-slate-700 p-4 space-y-3"><legend className="px-2 text-slate-100">{unit.finding_category} · {unit.data_category}</legend>
          <div className="grid sm:grid-cols-2 gap-3">{Object.entries(options).map(([key,values])=><label key={key} className="text-xs text-slate-400">{key}<select className={style} value={unit[key]} onChange={event=>update(index,key,event.target.value)}>{values.map(value=><option key={value}>{value}</option>)}</select></label>)}</div>
          <label className="block text-sm text-slate-300">Observation — what was actually inspected/observed?<textarea required minLength="5" className={style} value={unit.observation} onChange={event=>update(index,'observation',event.target.value)} /></label>
          <label className="block text-sm text-slate-300">Interpretation — your conclusion and scope/limitations<textarea required minLength="5" className={style} value={unit.interpretation} onChange={event=>update(index,'interpretation',event.target.value)} /></label>
          <p className="text-xs text-slate-400">Select supporting evidence, including review scope for negative/uncertain decisions.</p>
          {packet.evidence.map(item=><label key={item.id} className="inline-flex gap-2 mr-4 text-sm text-slate-300"><input type="checkbox" checked={unit.evidence_ids.includes(item.id)} onChange={event=>update(index,'evidence_ids',event.target.checked?[...unit.evidence_ids,item.id]:unit.evidence_ids.filter(id=>id!==item.id))} />Evidence {item.id}</label>)}
        </fieldset>)}
        <label className="flex gap-2 text-sm text-slate-300"><input type="checkbox" required checked={attest} onChange={event=>setAttest(event.target.checked)} />I reviewed this evidence independently and have not seen this system's predictions or another reviewer's decisions.</label>
        <button disabled={busy || !attest} className="rounded bg-indigo-600 px-4 py-2 text-white disabled:opacity-50">Submit immutable review</button>
      </form>}
    </>}
  </div></main>;
}
