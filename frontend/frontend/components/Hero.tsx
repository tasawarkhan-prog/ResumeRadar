"use client";
import { motion } from "framer-motion";
import { ArrowDown, Sparkles, Zap, Target } from "lucide-react";
import ParticleBackground from "./ParticleBackground";

const FEATURES = [
  { icon: <Target className="w-3.5 h-3.5" />, label: "Semantic Match Score" },
  { icon: <Zap className="w-3.5 h-3.5" />, label: "Gap Detection" },
  { icon: <Sparkles className="w-3.5 h-3.5" />, label: "Resume Rewriter" },
  { icon: <Sparkles className="w-3.5 h-3.5" />, label: "Cover Letter AI" },
];

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background layers */}
      <ParticleBackground />
      <div className="absolute inset-0 bg-hero-glow" />
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 60% 50% at 50% 100%, rgba(6,182,212,0.08), transparent)",
        }}
      />

      {/* 3D floating orbs */}
      <motion.div
        animate={{ y: [0, -24, 0], rotate: [0, 180, 360] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-1/4 left-1/4 w-48 h-48 rounded-full opacity-10"
        style={{
          background: "radial-gradient(circle, #6366f1 0%, transparent 70%)",
          filter: "blur(32px)",
        }}
      />
      <motion.div
        animate={{ y: [0, 24, 0], rotate: [360, 180, 0] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut", delay: 2 }}
        className="absolute bottom-1/4 right-1/4 w-64 h-64 rounded-full opacity-10"
        style={{
          background: "radial-gradient(circle, #06b6d4 0%, transparent 70%)",
          filter: "blur(40px)",
        }}
      />

      {/* Hero content */}
      <div className="relative z-10 text-center px-6 max-w-4xl mx-auto">
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="inline-flex items-center gap-2 mb-8 px-4 py-1.5 rounded-full glass border border-brand-500/30 text-sm text-brand-400"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse-slow" />
          AI/ML · RAG · Agentic Workflows · NLP
        </motion.div>

        {/* Title */}
        <motion.h1
          initial={{ opacity: 0, y: 32 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.7 }}
          className="text-6xl sm:text-7xl md:text-8xl font-black leading-[0.9] tracking-tighter mb-6"
        >
          <span className="text-white">Resume</span>
          <span className="gradient-text">Radar</span>
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="text-lg sm:text-xl text-slate-400 max-w-2xl mx-auto mb-4 leading-relaxed"
        >
          Paste a job description and your resume.{" "}
          <span className="text-white font-medium">
            AI tells you fit score, missing skills, and rewrites your resume + cover letter
          </span>{" "}
          to maximize match — all explained with extracted evidence.
        </motion.p>

        {/* Quote */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="text-slate-600 text-sm italic mb-10"
        >
          ATS rejects 75% of resumes before a human sees them. Not anymore.
        </motion.p>

        {/* Feature pills */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="flex flex-wrap justify-center gap-2 mb-12"
        >
          {FEATURES.map((f, i) => (
            <motion.span
              key={f.label}
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.65 + i * 0.08 }}
              className="pill pill-blue flex items-center gap-1.5"
            >
              {f.icon}
              {f.label}
            </motion.span>
          ))}
        </motion.div>

        {/* CTA */}
        <motion.a
          href="#upload"
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.85 }}
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.97 }}
          className="btn-neon inline-flex items-center gap-3 px-8 py-4 rounded-2xl text-white font-semibold text-lg cursor-pointer no-underline"
        >
          <Sparkles className="w-5 h-5" />
          Start Analysis — It's Free
        </motion.a>

        {/* Scroll hint */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.2 }}
          className="mt-16 flex flex-col items-center gap-2 text-slate-600 text-sm"
        >
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 1.8, repeat: Infinity }}
          >
            <ArrowDown className="w-5 h-5" />
          </motion.div>
          Scroll to analyze
        </motion.div>
      </div>
    </section>
  );
}
