"use client";
import { motion } from "framer-motion";
import { getScoreColor, getScoreLabel } from "@/lib/api";

interface Props {
  score: number;
  atsScore: number;
  provider: string;
  processingTime: number;
}

export default function ScoreGauge({ score, atsScore, provider, processingTime }: Props) {
  const color = getScoreColor(score);
  const label = getScoreLabel(score);
  const atsColor = getScoreColor(atsScore);

  // SVG arc parameters
  const r = 70;
  const cx = 90;
  const cy = 90;
  const circumference = Math.PI * r; // half circle
  const dashOffset = circumference - (score / 100) * circumference;

  return (
    <div className="glass rounded-3xl p-6 border border-white/[0.06] flex flex-col items-center gap-6">
      <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
        Match Score
      </h3>

      {/* Semicircular gauge */}
      <div className="relative">
        <svg width="180" height="100" viewBox="0 0 180 100">
          {/* Track */}
          <path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke="rgba(255,255,255,0.06)"
            strokeWidth="12"
            strokeLinecap="round"
          />
          {/* Animated progress */}
          <motion.path
            d="M 20 90 A 70 70 0 0 1 160 90"
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: dashOffset }}
            transition={{ duration: 1.4, ease: "easeOut", delay: 0.3 }}
            style={{ filter: `drop-shadow(0 0 8px ${color})` }}
          />
        </svg>

        {/* Center score */}
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
          <motion.span
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6, type: "spring" }}
            className="text-5xl font-black"
            style={{ color }}
          >
            {Math.round(score)}
          </motion.span>
          <span className="text-xs text-slate-500">/ 100</span>
        </div>
      </div>

      {/* Label */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.8 }}
        className="text-center"
      >
        <p className="text-lg font-bold" style={{ color }}>
          {label}
        </p>
      </motion.div>

      {/* ATS Score */}
      <div className="w-full space-y-2">
        <div className="flex justify-between text-xs text-slate-400">
          <span>ATS Keyword Score</span>
          <span style={{ color: atsColor }} className="font-semibold">
            {Math.round(atsScore)}%
          </span>
        </div>
        <div className="h-2 w-full bg-white/[0.05] rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: atsColor }}
            initial={{ width: 0 }}
            animate={{ width: `${atsScore}%` }}
            transition={{ duration: 1.2, ease: "easeOut", delay: 0.5 }}
          />
        </div>
      </div>

      {/* Meta */}
      <div className="flex gap-4 text-xs text-slate-600 w-full justify-center">
        <span>Provider: <span className="text-slate-400">{provider}</span></span>
        <span>Time: <span className="text-slate-400">{processingTime}s</span></span>
      </div>
    </div>
  );
}
