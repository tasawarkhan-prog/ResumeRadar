"use client";
import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import UploadSection from "@/components/UploadSection";
import ResultsPanel from "@/components/ResultsPanel";
import FogBackground from "@/components/FogBackground";
import { analyzeResume } from "@/lib/api";
import { AnalysisResponse } from "@/lib/types";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (
    file: File,
    jobDescription: string,
    provider: string,
    tone: string,
    userApiKey: string = "",
  ) => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = await analyzeResume(file, jobDescription, provider, tone, userApiKey);
      setResults(data);
      // Smooth scroll to results
      setTimeout(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth" });
      }, 200);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <FogBackground />
    <main className="relative min-h-screen" style={{ zIndex: 1, isolation: "isolate" }}>
      <Navbar />

      <Hero />

      <UploadSection onAnalyze={handleAnalyze} loading={loading} />

      {/* Global error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -16 }}
            className="max-w-3xl mx-auto px-6 mb-8"
          >
            <div className="glass rounded-2xl border border-red-500/30 bg-red-500/10 p-5 text-center">
              <p className="text-red-400 font-medium">{error}</p>
              <p className="text-slate-500 text-sm mt-1">
                Make sure the backend is running and your API key is configured.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Results */}
      <AnimatePresence>
        {results && (
          <motion.div
            key="results"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <ResultsPanel data={results} />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Footer */}
      <footer className="border-t border-white/[0.06] py-8 px-6 text-center text-slate-600 text-sm">
        <p>
          ResumeRadar · Built with Next.js + FastAPI + Sentence-Transformers ·{" "}
          <span className="text-slate-500">Free & Open Source</span>
        </p>
        <p className="mt-1 text-slate-700">
          Powered by Groq (Llama 3.3) · Gemini 2.0 Flash · all-MiniLM-L6-v2
        </p>
      </footer>
    </main>
    </>
  );
}
