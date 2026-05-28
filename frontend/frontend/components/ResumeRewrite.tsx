"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Copy, Check, GitCompare, FileText, Lightbulb } from "lucide-react";
import { RewrittenResume } from "@/lib/types";

interface Props {
  data: RewrittenResume;
}

type View = "split" | "rewritten" | "changes";

export default function ResumeRewrite({ data }: Props) {
  const [view, setView] = useState<View>("rewritten");
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(data.rewritten_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4">
      {/* Tabs */}
      <div className="flex items-center gap-2 flex-wrap">
        {(
          [
            { key: "rewritten", label: "Rewritten Resume", icon: <FileText className="w-3.5 h-3.5" /> },
            { key: "split", label: "Side-by-Side Diff", icon: <GitCompare className="w-3.5 h-3.5" /> },
            { key: "changes", label: `Changes (${data.changes.length})`, icon: <Lightbulb className="w-3.5 h-3.5" /> },
          ] as { key: View; label: string; icon: React.ReactNode }[]
        ).map((tab) => (
          <button
            key={tab.key}
            onClick={() => setView(tab.key)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              view === tab.key
                ? "bg-brand-500 text-white"
                : "glass border border-white/10 text-slate-400 hover:text-white"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
        <button
          onClick={copy}
          className="ml-auto flex items-center gap-1.5 px-3 py-2 rounded-xl glass border border-white/10 text-sm text-slate-400 hover:text-white transition-colors"
        >
          {copied ? (
            <><Check className="w-3.5 h-3.5 text-green-400" /> Copied!</>
          ) : (
            <><Copy className="w-3.5 h-3.5" /> Copy</>
          )}
        </button>
      </div>

      <AnimatePresence mode="wait">
        {/* Rewritten resume */}
        {view === "rewritten" && (
          <motion.div
            key="rewritten"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="glass rounded-2xl border border-white/[0.06] p-6"
          >
            <pre className="whitespace-pre-wrap text-sm text-slate-300 leading-relaxed font-mono max-h-96 overflow-y-auto">
              {data.rewritten_text}
            </pre>
          </motion.div>
        )}

        {/* Split diff view */}
        {view === "split" && (
          <motion.div
            key="split"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="grid grid-cols-2 gap-4"
          >
            <div className="glass rounded-2xl border border-red-500/20 p-5">
              <p className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-3">
                Original
              </p>
              <pre className="whitespace-pre-wrap text-xs text-slate-400 leading-relaxed font-mono max-h-80 overflow-y-auto">
                {data.original_text}
              </pre>
            </div>
            <div className="glass rounded-2xl border border-green-500/20 p-5">
              <p className="text-xs font-semibold text-green-400 uppercase tracking-wider mb-3">
                AI-Rewritten
              </p>
              <pre className="whitespace-pre-wrap text-xs text-slate-300 leading-relaxed font-mono max-h-80 overflow-y-auto">
                {data.rewritten_text}
              </pre>
            </div>
          </motion.div>
        )}

        {/* Changes list */}
        {view === "changes" && (
          <motion.div
            key="changes"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            className="space-y-3 max-h-[500px] overflow-y-auto pr-1"
          >
            {data.changes.length === 0 ? (
              <p className="text-slate-500 text-sm text-center py-8">
                No specific changes logged. See the rewritten tab.
              </p>
            ) : (
              data.changes.map((change, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="glass rounded-2xl border border-white/[0.06] p-4 space-y-3"
                >
                  <div className="diff-original rounded-lg p-3 text-sm">
                    <span className="text-xs text-red-400 font-semibold block mb-1">Before</span>
                    {change.original}
                  </div>
                  <div className="diff-improved rounded-lg p-3 text-sm">
                    <span className="text-xs text-green-400 font-semibold block mb-1">After</span>
                    {change.improved}
                  </div>
                  <div className="flex items-start gap-2">
                    <Lightbulb className="w-3.5 h-3.5 text-yellow-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-slate-500">{change.reason}</p>
                  </div>
                </motion.div>
              ))
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
