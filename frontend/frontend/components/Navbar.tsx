"use client";
import { motion } from "framer-motion";
import { Radar, Github, ExternalLink } from "lucide-react";

export default function Navbar() {
  return (
    <motion.nav
      initial={{ y: -64, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/[0.06]"
    >
      <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-accent flex items-center justify-center">
            <Radar className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-white tracking-tight">
            Resume<span className="gradient-text">Radar</span>
          </span>
        </div>

        {/* Links */}
        <div className="hidden sm:flex items-center gap-6 text-sm text-slate-400">
          <a
            href="#upload"
            className="hover:text-white transition-colors"
          >
            Analyze
          </a>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1 hover:text-white transition-colors"
          >
            <Github className="w-4 h-4" />
            GitHub
          </a>
          <a
            href="https://huggingface.co"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-500/15 border border-brand-500/30 text-brand-400 hover:bg-brand-500/25 transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            HuggingFace
          </a>
        </div>
      </div>
    </motion.nav>
  );
}
