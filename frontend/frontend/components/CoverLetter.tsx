"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import { Copy, Check, Download, Star } from "lucide-react";
import { CoverLetterResult } from "@/lib/types";

interface Props {
  data: CoverLetterResult;
}

export default function CoverLetter({ data }: Props) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(data.cover_letter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const download = () => {
    const blob = new Blob([data.cover_letter], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "cover_letter.txt";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Meta */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="pill pill-blue capitalize">{data.tone} tone</span>
        {data.key_points_addressed.map((pt) => (
          <span key={pt} className="pill pill-green text-xs">
            ✓ {pt}
          </span>
        ))}
        <div className="ml-auto flex gap-2">
          <button
            onClick={copy}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg glass border border-white/10 text-xs text-slate-400 hover:text-white transition-colors"
          >
            {copied ? (
              <><Check className="w-3.5 h-3.5 text-green-400" /> Copied!</>
            ) : (
              <><Copy className="w-3.5 h-3.5" /> Copy</>
            )}
          </button>
          <button
            onClick={download}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg glass border border-white/10 text-xs text-slate-400 hover:text-white transition-colors"
          >
            <Download className="w-3.5 h-3.5" /> Download
          </button>
        </div>
      </div>

      {/* Cover letter text */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl border border-white/[0.06] p-6 relative overflow-hidden"
      >
        {/* Decorative gradient */}
        <div
          className="absolute top-0 right-0 w-32 h-32 opacity-10 pointer-events-none"
          style={{
            background: "radial-gradient(circle, #6366f1 0%, transparent 70%)",
          }}
        />

        <div className="relative">
          <div className="flex items-center gap-2 mb-4">
            <Star className="w-4 h-4 text-brand-400" />
            <span className="text-xs font-semibold text-brand-400 uppercase tracking-wider">
              AI-Generated Cover Letter
            </span>
          </div>
          <p className="text-slate-300 text-sm leading-[1.9] whitespace-pre-wrap">
            {data.cover_letter}
          </p>
        </div>
      </motion.div>

      <p className="text-xs text-slate-600 text-center">
        Review and personalize before sending. AI content should complement your authentic voice.
      </p>
    </div>
  );
}
