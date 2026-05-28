"use client";
import { useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart2,
  TrendingUp,
  FileEdit,
  Mail,
  User,
  Briefcase,
  LayoutTemplate,
  MessageSquare,
} from "lucide-react";
import { AnalysisResponse } from "@/lib/types";
import ScoreGauge from "./ScoreGauge";
import SkillMatrix from "./SkillMatrix";
import GapAnalysis from "./GapAnalysis";
import ResumeRewrite from "./ResumeRewrite";
import CoverLetter from "./CoverLetter";
import ResumeDownload from "./ResumeDownload";
import InterviewPrep from "./InterviewPrep";

interface Props {
  data: AnalysisResponse;
}

type Tab = "overview" | "skills" | "gaps" | "rewrite" | "coverletter" | "templates" | "interview";

const TABS: { key: Tab; label: string; icon: React.ReactNode }[] = [
  { key: "overview",     label: "Overview",       icon: <BarChart2 className="w-4 h-4" /> },
  { key: "skills",       label: "Skill Matrix",   icon: <TrendingUp className="w-4 h-4" /> },
  { key: "gaps",         label: "Gap Analysis",   icon: <TrendingUp className="w-4 h-4" /> },
  { key: "rewrite",      label: "Resume Rewrite", icon: <FileEdit className="w-4 h-4" /> },
  { key: "coverletter",  label: "Cover Letter",   icon: <Mail className="w-4 h-4" /> },
  { key: "templates",    label: "Templates",      icon: <LayoutTemplate className="w-4 h-4" /> },
  { key: "interview",    label: "Interview Prep", icon: <MessageSquare className="w-4 h-4" /> },
];

export default function ResultsPanel({ data }: Props) {
  const [tab, setTab] = useState<Tab>("overview");
  const { resume_data, job_data, match_result, rewritten_resume, cover_letter, interview_prep } = data;

  return (
    <section id="results" className="py-16 px-6 max-w-7xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        {/* Header */}
        <div className="text-center mb-10">
          <span className="pill pill-green text-sm mb-3 inline-block">Analysis Complete</span>
          <h2 className="text-4xl font-bold text-white">
            Your <span className="gradient-text">Results</span>
          </h2>
          <p className="text-slate-400 mt-2">
            {resume_data.name && `${resume_data.name} · `}
            Applying for{" "}
            <span className="text-white font-medium">
              {job_data.title || "the role"}
              {job_data.company && ` at ${job_data.company}`}
            </span>
          </p>
        </div>

        {/* Top info cards */}
        <div className="grid md:grid-cols-2 gap-4 mb-8">
          {/* Candidate card */}
          <div className="glass rounded-2xl p-5 border border-white/[0.06] flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-brand-500/15 border border-brand-500/30 flex items-center justify-center flex-shrink-0">
              <User className="w-5 h-5 text-brand-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Candidate</p>
              <p className="text-white font-semibold">{resume_data.name || "You"}</p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {resume_data.skills.slice(0, 5).map((s) => (
                  <span key={s.name} className="pill pill-blue text-xs">
                    {s.name}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Job card */}
          <div className="glass rounded-2xl p-5 border border-white/[0.06] flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center flex-shrink-0">
              <Briefcase className="w-5 h-5 text-accent" />
            </div>
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Target Role</p>
              <p className="text-white font-semibold">
                {job_data.title || "Role"}
                {job_data.company && (
                  <span className="text-slate-400 font-normal"> · {job_data.company}</span>
                )}
              </p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                <span className="pill pill-yellow capitalize">{job_data.seniority}</span>
                {job_data.domain && <span className="pill pill-blue">{job_data.domain}</span>}
              </div>
            </div>
          </div>
        </div>

        {/* Tabs + content */}
        <div className="flex gap-6 flex-col lg:flex-row">
          {/* Sidebar tabs (lg) / Top tabs (sm) */}
          <div className="lg:w-48 flex-shrink-0">
            <div className="flex lg:flex-col gap-2 overflow-x-auto lg:overflow-visible pb-2 lg:pb-0">
              {TABS.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className={`
                    flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium transition-all whitespace-nowrap
                    ${tab === t.key
                      ? "bg-brand-500 text-white shadow-lg shadow-brand-500/30"
                      : "glass border border-white/10 text-slate-400 hover:text-white"
                    }
                  `}
                >
                  {t.icon}
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Main content */}
          <div className="flex-1 min-w-0">
            {tab === "overview" && (
              <div className="grid sm:grid-cols-2 gap-6">
                <ScoreGauge
                  score={match_result.fit_score}
                  atsScore={match_result.ats_score}
                  provider={data.provider_used}
                  processingTime={data.processing_time}
                />
                <div className="space-y-4">
                  {/* Quick stats */}
                  {[
                    {
                      label: "Skills Matched",
                      value: `${match_result.skill_breakdown.filter((s) => s.in_resume).length} / ${match_result.skill_breakdown.length}`,
                      color: "#22c55e",
                    },
                    {
                      label: "Critical Gaps",
                      value: match_result.gaps.filter((g) => g.gap_type === "missing" && g.importance === "required").length,
                      color: "#ef4444",
                    },
                    {
                      label: "Easy Wins",
                      value: match_result.gaps.filter((g) => g.gap_type === "present_but_unstated").length,
                      color: "#f59e0b",
                    },
                    {
                      label: "Certifications",
                      value: resume_data.certifications.length,
                      color: "#818cf8",
                    },
                  ].map((stat) => (
                    <div
                      key={stat.label}
                      className="glass rounded-xl p-4 border border-white/[0.06] flex items-center justify-between"
                    >
                      <span className="text-sm text-slate-400">{stat.label}</span>
                      <span className="text-xl font-bold" style={{ color: stat.color }}>
                        {stat.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {tab === "skills" && (
              <SkillMatrix
                skillBreakdown={match_result.skill_breakdown}
                gaps={match_result.gaps}
                strengths={match_result.strengths}
              />
            )}

            {tab === "gaps" && <GapAnalysis gaps={match_result.gaps} />}

            {tab === "rewrite" && <ResumeRewrite data={rewritten_resume} />}

            {tab === "coverletter" && <CoverLetter data={cover_letter} />}

            {tab === "templates" && (
              <ResumeDownload
                resumeData={resume_data}
                jobData={job_data}
                rewrittenText={rewritten_resume.rewritten_text}
              />
            )}

            {tab === "interview" && (
              <InterviewPrep interviewPrep={interview_prep} />
            )}
          </div>
        </div>
      </motion.div>
    </section>
  );
}
