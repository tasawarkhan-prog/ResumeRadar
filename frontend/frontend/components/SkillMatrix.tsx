"use client";
import { motion } from "framer-motion";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { CheckCircle2, XCircle, AlertCircle } from "lucide-react";
import { SkillMatch, GapItem } from "@/lib/types";

interface Props {
  skillBreakdown: SkillMatch[];
  gaps: GapItem[];
  strengths: string[];
}

export default function SkillMatrix({ skillBreakdown, gaps, strengths }: Props) {
  // Build radar data from top 8 required skills
  const radarData = skillBreakdown.slice(0, 8).map((s) => ({
    skill: s.skill.length > 14 ? s.skill.slice(0, 12) + "…" : s.skill,
    score: Math.round(s.in_resume ? Math.max(70, s.similarity_score * 100) : s.similarity_score * 60),
    fullMark: 100,
  }));

  const matched = skillBreakdown.filter((s) => s.in_resume);
  const missing = skillBreakdown.filter((s) => !s.in_resume && s.importance === "required");
  const partial = skillBreakdown.filter(
    (s) => !s.in_resume && s.importance === "preferred"
  );

  return (
    <div className="space-y-6">
      {/* Summary row */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Matched", count: matched.length, color: "#22c55e", icon: <CheckCircle2 className="w-4 h-4" /> },
          { label: "Missing", count: missing.length, color: "#ef4444", icon: <XCircle className="w-4 h-4" /> },
          { label: "Preferred", count: partial.length, color: "#f59e0b", icon: <AlertCircle className="w-4 h-4" /> },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass rounded-2xl p-4 border border-white/[0.06] text-center"
          >
            <div className="flex items-center justify-center gap-1.5 mb-1" style={{ color: stat.color }}>
              {stat.icon}
              <span className="text-xs font-medium">{stat.label}</span>
            </div>
            <p className="text-3xl font-black" style={{ color: stat.color }}>
              {stat.count}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Radar chart */}
      {radarData.length > 2 && (
        <div className="glass rounded-2xl p-6 border border-white/[0.06]">
          <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
            Skill Radar
          </h4>
          <ResponsiveContainer width="100%" height={260}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="rgba(255,255,255,0.08)" />
              <PolarAngleAxis
                dataKey="skill"
                tick={{ fill: "#64748b", fontSize: 11 }}
              />
              <Radar
                dataKey="score"
                stroke="#6366f1"
                fill="#6366f1"
                fillOpacity={0.25}
                strokeWidth={2}
              />
              <Tooltip
                contentStyle={{
                  background: "rgba(4,4,15,0.95)",
                  border: "1px solid rgba(99,102,241,0.3)",
                  borderRadius: "12px",
                  color: "#e2e8f0",
                  fontSize: "12px",
                }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Skill breakdown list */}
      <div className="glass rounded-2xl p-6 border border-white/[0.06]">
        <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Skill Breakdown
        </h4>
        <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
          {skillBreakdown.map((s, i) => (
            <motion.div
              key={s.skill}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.04 }}
              className="flex items-center gap-3"
            >
              {s.in_resume ? (
                <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
              )}
              <span className="text-sm text-slate-300 flex-1 truncate">{s.skill}</span>
              <span
                className={`pill text-xs ${
                  s.importance === "required" ? "pill-blue" : "pill-yellow"
                }`}
              >
                {s.importance}
              </span>
              <div className="w-24 h-1.5 bg-white/[0.05] rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{
                    backgroundColor: s.in_resume ? "#22c55e" : "#ef444455",
                  }}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.round(s.similarity_score * 100)}%` }}
                  transition={{ duration: 0.8, delay: i * 0.04 }}
                />
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Strengths */}
      {strengths.length > 0 && (
        <div className="glass rounded-2xl p-5 border border-green-500/15">
          <h4 className="text-sm font-semibold text-green-400 uppercase tracking-wider mb-3">
            Your Strengths for This Role
          </h4>
          <div className="flex flex-wrap gap-2">
            {strengths.map((s) => (
              <span key={s} className="pill pill-green">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
