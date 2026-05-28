"use client";
import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload, FileText, X, Sparkles, Loader2, ChevronDown,
  Key, CheckCircle2, Wifi, WifiOff, Eye, EyeOff,
} from "lucide-react";
import { checkProviders } from "@/lib/api";

interface Props {
  onAnalyze: (
    file: File,
    jobDescription: string,
    provider: string,
    tone: string,
    userApiKey: string,
  ) => Promise<void>;
  loading: boolean;
}

const TONES = ["professional", "enthusiastic", "concise"];

const PROVIDERS = [
  { value: "auto",   label: "Auto-detect",       hint: "Uses server key"         },
  { value: "groq",   label: "Groq (Llama 3.3)",  hint: "14,400 req/day free"     },
  { value: "gemini", label: "Gemini 2.0 Flash",  hint: "1,500 req/day free"      },
];

export default function UploadSection({ onAnalyze, loading }: Props) {
  const [file, setFile]             = useState<File | null>(null);
  const [jobDesc, setJobDesc]       = useState("");
  const [provider, setProvider]     = useState("auto");
  const [tone, setTone]             = useState("professional");
  const [userApiKey, setUserApiKey] = useState("");
  const [showKey, setShowKey]       = useState(false);
  const [error, setError]           = useState("");

  // Server-side provider detection
  const [serverProviders, setServerProviders] = useState<string[]>([]);
  const [serverChecked, setServerChecked]     = useState(false);

  useEffect(() => {
    checkProviders()
      .then((res) => {
        setServerProviders(res.available);
        // Auto-select the server default if available
        if (res.default) setProvider(res.default);
        else setProvider("groq"); // fallback: user must provide key
      })
      .catch(() => {
        // Backend not reachable — still let user enter their own key
        setServerProviders([]);
        setProvider("groq");
      })
      .finally(() => setServerChecked(true));
  }, []);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) { setFile(accepted[0]); setError(""); }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
  });

  // Whether server already has a key for the selected provider
  const serverHasKey =
    provider === "auto"
      ? serverProviders.length > 0
      : serverProviders.includes(provider);

  const needsKey = !serverHasKey && !userApiKey.trim();

  const handleSubmit = async () => {
    if (!file) return setError("Please upload your resume.");
    if (!jobDesc.trim() || jobDesc.length < 20)
      return setError("Please paste the full job description.");
    if (needsKey)
      return setError("No API key configured. Enter your Groq or Gemini key below.");
    setError("");
    await onAnalyze(file, jobDesc, provider, tone, userApiKey.trim());
  };

  const getKeyPlaceholder = () => {
    if (provider === "gemini") return "AIza... (Gemini API key)";
    return "gsk_... (Groq API key)";
  };

  const getKeyLink = () =>
    provider === "gemini"
      ? "https://aistudio.google.com/app/apikey"
      : "https://console.groq.com/keys";

  return (
    <section id="upload" className="py-20 px-6 max-w-7xl mx-auto">
      {/* Section header */}
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center mb-14"
      >
        <h2 className="text-4xl font-bold text-white mb-3">
          Analyze Your <span className="gradient-text">Fit</span>
        </h2>
        <p className="text-slate-400 max-w-xl mx-auto">
          Upload your resume and paste the job description. AI does the rest in ~30 seconds.
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* ── Left: Resume Upload + Settings ── */}
        <motion.div
          initial={{ opacity: 0, x: -24 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.1 }}
          className="space-y-4"
        >
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Your Resume
          </h3>

          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={`
              relative rounded-2xl border-2 border-dashed p-8 text-center cursor-pointer
              transition-all duration-300 min-h-[200px] flex flex-col items-center justify-center gap-4
              ${isDragActive
                ? "border-brand-500 bg-brand-500/10"
                : file
                ? "border-green-500/50 bg-green-500/5"
                : "border-white/10 bg-white/[0.02] hover:border-brand-500/50 hover:bg-brand-500/5"
              }
            `}
          >
            <input {...getInputProps()} />
            <AnimatePresence mode="wait">
              {file ? (
                <motion.div key="file" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} className="flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-green-500/15 border border-green-500/30 flex items-center justify-center">
                    <FileText className="w-6 h-6 text-green-400" />
                  </div>
                  <div>
                    <p className="text-white font-medium">{file.name}</p>
                    <p className="text-slate-500 text-sm">{(file.size / 1024).toFixed(0)} KB</p>
                  </div>
                  <button onClick={(e) => { e.stopPropagation(); setFile(null); }} className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-red-400 transition-colors">
                    <X className="w-3.5 h-3.5" /> Remove
                  </button>
                </motion.div>
              ) : (
                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-xl glass border border-white/10 flex items-center justify-center">
                    <Upload className="w-6 h-6 text-slate-400" />
                  </div>
                  <div>
                    <p className="text-white font-medium">{isDragActive ? "Drop it here!" : "Drop resume or click to browse"}</p>
                    <p className="text-slate-500 text-sm mt-1">PDF, DOCX, TXT · Max 10 MB</p>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Provider + Tone */}
          <div className="grid grid-cols-2 gap-3">
            {/* Provider */}
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <label className="text-xs text-slate-400 font-medium">AI Provider</label>
                {serverChecked && (
                  <span className={`flex items-center gap-1 text-xs ${serverProviders.length > 0 ? "text-green-400" : "text-slate-600"}`}>
                    {serverProviders.length > 0
                      ? <><Wifi className="w-3 h-3" /> Server key ready</>
                      : <><WifiOff className="w-3 h-3" /> No server key</>
                    }
                  </span>
                )}
              </div>
              <div className="relative">
                <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="w-full glass border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white appearance-none cursor-pointer focus:border-brand-500/50 focus:outline-none transition-colors"
                >
                  {PROVIDERS.map((p) => (
                    <option key={p.value} value={p.value}>
                      {p.label}
                      {serverProviders.includes(p.value) ? " ✓" : ""}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
            </div>

            {/* Tone */}
            <div className="space-y-1">
              <label className="text-xs text-slate-400 font-medium">Cover Letter Tone</label>
              <div className="relative">
                <select
                  value={tone}
                  onChange={(e) => setTone(e.target.value)}
                  className="w-full glass border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white appearance-none cursor-pointer focus:border-brand-500/50 focus:outline-none transition-colors"
                >
                  {TONES.map((t) => (
                    <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
            </div>
          </div>

          {/* ── API Key Input ── */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" />
                Your API Key
                {serverHasKey && <span className="text-slate-600">(optional — server key active)</span>}
                {!serverHasKey && <span className="text-red-400">*required</span>}
              </label>
              <a
                href={getKeyLink()}
                target="_blank"
                rel="noreferrer"
                className="text-xs text-brand-400 hover:text-brand-300 transition-colors"
              >
                Get free key →
              </a>
            </div>
            <div className="relative">
              <input
                type={showKey ? "text" : "password"}
                value={userApiKey}
                onChange={(e) => setUserApiKey(e.target.value)}
                placeholder={serverHasKey ? `Optional — override server ${provider === "gemini" ? "Gemini" : "Groq"} key` : getKeyPlaceholder()}
                className={`
                  w-full glass border rounded-xl px-3 py-2.5 pr-10 text-sm text-white
                  placeholder-slate-600 focus:outline-none transition-colors
                  ${needsKey ? "border-red-500/40 focus:border-red-500/70" : "border-white/10 focus:border-brand-500/50"}
                `}
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {/* Key status indicator */}
            {userApiKey.trim() && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-xs text-green-400 flex items-center gap-1"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                Your key will be used (overrides server key)
              </motion.p>
            )}
            {!userApiKey.trim() && serverHasKey && (
              <p className="text-xs text-slate-600">
                Using server-configured {serverProviders.join(" / ")} key
              </p>
            )}
          </div>
        </motion.div>

        {/* ── Right: Job Description ── */}
        <motion.div
          initial={{ opacity: 0, x: 24 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.2 }}
          className="space-y-4"
        >
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
            Job Description
          </h3>
          <textarea
            value={jobDesc}
            onChange={(e) => setJobDesc(e.target.value)}
            placeholder="Paste the full job description here — including responsibilities, requirements, and preferred skills. More detail = better analysis."
            className="
              w-full h-[370px] glass border border-white/10 rounded-2xl p-4
              text-sm text-slate-200 placeholder-slate-600 resize-none
              focus:border-brand-500/50 focus:outline-none transition-colors leading-relaxed
            "
          />
          <p className="text-xs text-slate-600">
            {jobDesc.length} characters · Recommend 300+ for best results
          </p>
        </motion.div>
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.p
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}
            className="mt-4 text-center text-sm text-red-400"
          >
            {error}
          </motion.p>
        )}
      </AnimatePresence>

      {/* Submit */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mt-8 flex justify-center"
      >
        <motion.button
          onClick={handleSubmit}
          disabled={loading}
          whileHover={!loading ? { scale: 1.03 } : {}}
          whileTap={!loading ? { scale: 0.97 } : {}}
          className="btn-neon flex items-center gap-3 px-10 py-4 rounded-2xl text-white font-semibold text-lg disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading
            ? <><Loader2 className="w-5 h-5 animate-spin" />Analyzing with AI… (~30s)</>
            : <><Sparkles className="w-5 h-5" />Analyze My Resume</>
          }
        </motion.button>
      </motion.div>

      {loading && (
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mt-6 text-center text-sm text-slate-500">
          Parsing resume → Analyzing job → Computing semantic match → Rewriting → Generating cover letter…
        </motion.p>
      )}
    </section>
  );
}
