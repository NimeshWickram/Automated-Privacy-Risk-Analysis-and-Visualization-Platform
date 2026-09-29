import { apiFetch } from '../api';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, UploadCloud, File, Loader2, CheckCircle2, Shield } from 'lucide-react';

const ANALYSIS_STEPS = [
  { id: 'selected', label: 'APK selected', icon: UploadCloud },
  { id: 'analysis', label: 'Uploading, analyzing static evidence and applying fusion rules…', icon: Shield },
  { id: 'saved', label: 'Analysis saved', icon: CheckCircle2 },
];

export default function UploadModal({ isOpen, onClose }) {
  const [file, setFile] = useState(null);
  const [policyUrl, setPolicyUrl] = useState("");
  const [configuration, setConfiguration] = useState('E');
  const [stepIndex, setStepIndex] = useState(-1);
  const navigate = useNavigate();

  // Reset state when opened
  useEffect(() => {
    if (isOpen) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setFile(null);
      setPolicyUrl("");
      setStepIndex(-1);
      setConfiguration('E');
    }
  }, [isOpen]);

  useEffect(() => {
    if (stepIndex === 0 && file) {
      const uploadFile = async () => {
        try {
          setStepIndex(1);
          
          const formData = new FormData();
          formData.append("file", file);
          formData.append('analysis_configuration', configuration);
          if (policyUrl) {
            formData.append("policy_url", policyUrl);
          }
          

          const res = await apiFetch("http://localhost:8000/api/analyze", {
            method: "POST",
            body: formData,
          });

          if (!res.ok) {
            throw new Error("Analysis failed");
          }
          
          
          const data = await res.json();
          
          setStepIndex(2);
          
          setTimeout(() => {
            onClose();
            navigate(`/analyze/${data.app_id}`);
          }, 1000);
          
        } catch (error) {
          alert("Error analyzing APK: " + error.message);
          setStepIndex(-1);
          setFile(null);
        }
      };
      
      uploadFile();
    }
  }, [stepIndex, file, policyUrl, configuration, navigate, onClose]);

  const handleFileSelect = (e) => {
    const selected = e.target.files?.[0];
    if (selected && selected.name.endsWith('.apk')) {
      setFile(selected);
      setStepIndex(0); // Start the process
    } else {
      alert("Please select a valid .apk file.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div 
        className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity" 
        onClick={() => stepIndex === -1 && onClose()}
      />
      
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-700/60 rounded-2xl shadow-2xl overflow-hidden animate-fade-in-up">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Shield className="text-indigo-400" size={20} />
            Analyze New APK
          </h2>
          {stepIndex === -1 && (
            <button 
              onClick={onClose}
              className="text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          )}
        </div>

        {/* Content */}
        <div className="p-6">
          {stepIndex === -1 ? (
            // Idle State: File Selection
            <div className="border-2 border-dashed border-slate-700 hover:border-indigo-500/50 rounded-xl p-8 text-center transition-colors bg-slate-800/20 group relative cursor-pointer">
              <input 
                type="file" 
                accept=".apk"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                onChange={handleFileSelect}
              />
              <div className="w-14 h-14 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:bg-indigo-500/20 group-hover:scale-110 transition-all">
                <UploadCloud className="text-indigo-400 w-7 h-7" />
              </div>
              <p className="text-slate-200 font-semibold mb-1">Upload Android APK</p>
              <p className="text-xs text-slate-400 mb-4">Static APK analysis; network capture is not performed.</p>
              <span className="inline-flex items-center justify-center px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors mb-4">
                Browse Files
              </span>
              <div className="mt-4" onClick={(e) => e.stopPropagation()}>
                <label className="block text-left text-xs text-slate-400 relative z-20 mb-3">Evidence configuration
                  <select value={configuration} onChange={event => setConfiguration(event.target.value)} className="mt-1 w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white">
                    <option value="A">A — Manifest</option>
                    <option value="B">B — Manifest + Code</option>
                    <option value="C">C — Manifest + Code + SDK</option>
                    <option value="D">D — Manifest + Code + SDK + Network</option>
                    <option value="E">E — All available sources</option>
                  </select>
                </label>
                <input
                  type="url"
                  placeholder="Privacy Policy URL (Optional)"
                  className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors z-20 relative"
                  value={policyUrl}
                  onChange={(e) => setPolicyUrl(e.target.value)}
                />
              </div>
            </div>
          ) : (
            // Processing State
            <div className="space-y-6">
              <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                <File className="text-indigo-400 w-8 h-8 shrink-0" />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold text-white truncate">{file?.name}</p>
                  <p className="text-xs text-slate-400">{(file?.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
              </div>

              <div className="space-y-4">
                {ANALYSIS_STEPS.map((step, idx) => {
                  const isActive = idx === stepIndex;
                  const isPast = idx < stepIndex;
                  const isFuture = idx > stepIndex;
                  
                  const StepIcon = step.icon;

                  return (
                    <div key={step.id} className={`flex items-start gap-3 transition-opacity duration-300 ${isFuture ? 'opacity-30' : 'opacity-100'}`}>
                      <div className="shrink-0 mt-0.5">
                        {isPast ? (
                          <CheckCircle2 className="text-emerald-500 w-5 h-5" />
                        ) : isActive ? (
                          <Loader2 className="text-indigo-400 w-5 h-5 animate-spin" />
                        ) : (
                          <StepIcon className="text-slate-500 w-5 h-5" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-medium ${isPast ? 'text-slate-300' : isActive ? 'text-indigo-300' : 'text-slate-500'}`}>
                          {step.label}
                        </p>
                        {isActive && (
                          <div className="mt-2 h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                            <div 
                              className="h-full w-full bg-indigo-500 rounded-full animate-pulse"
                            />
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
