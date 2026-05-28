"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronDown, MessageSquare, Lightbulb,
  Target, Star, TrendingUp, CheckCircle2, User,
} from "lucide-react";
import { InterviewPrepResult } from "@/lib/types";

interface Props {
  interviewPrep: InterviewPrepResult;
}

const CATEGORY_META: Record<string, { label: string; icon: string; color: string; border: string; bg: string }> = {
  behavioral: {
    label: "Behavioral",
    icon: "🗣",
    color: "text-brand-400",
    border: "border-brand-500/30",
    bg: "bg-brand-500/8",
  },
  technical: {
    label: "Technical",
    icon: "⚙️",
    color: "text-cyan-400",
    border: "border-cyan-500/30",
    bg: "bg-cyan-500/8",
  },
  situational: {
    label: "Situational",
    icon: "🎯",
    color: "text-emerald-400",
    border: "border-emerald-500/30",
    bg: "bg-emerald-500/8",
  },
};

const TIP_ICONS = [
  <Star key="s" className="w-4 h-4 text-yellow-400" />,
  <Target key="t" className="w-4 h-4 text-brand-400" />,
  <TrendingUp key="tr" className="w-4 h-4 text-green-400" />,
  <Lightbulb key="l" className="w-4 h-4 text-cyan-400" />,
  <MessageSquare key="m" className="w-4 h-4 text-purple-400" />,
  <CheckCircle2 key="c" className="w-4 h-4 text-emerald-400" />,
  <User key="u" className="w-4 h-4 text-rose-400" />,
];

function QACard({
  question,
  answer,
  index,
}: {
  question: string;
  answer: string;
  index: number;
}) {
  const [open, setOpen] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04 }}
      className="glass rounded-2xl border border-white/10 overflow-hidden"
    >
      {/* Question row */}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-start gap-3 px-5 py-4 text-left hover:bg-white/[0.03] transition-colors group"
      >
        <span className="flex-shrink-0 w-6 h-6 rounded-full bg-brand-500/20 border border-brand-500/30 flex items-center justify-center text-xs font-bold text-brand-400 mt-0.5">
          {index + 1}
        </span>
        <span className="flex-1 text-slate-200 text-sm font-medium leading-relaxed">
          {question}
        </span>
        <ChevronDown
          className={`w-4 h-4 text-slate-500 flex-shrink-0 mt-0.5 transition-transform duration-200 group-hover:text-slate-300 ${open ? "rotate-180" : ""}`}
        />
      </button>

      {/* Answer panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            style={{ overflow: "hidden" }}
          >
            <div className="px-5 pb-5 pt-1">
              <div className="flex gap-2 mb-2">
                <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-xs text-green-400 font-semibold uppercase tracking-wider">
                  Sample Answer
                </span>
              </div>
              <div className="bg-white/[0.04] border border-white/[0.08] rounded-xl p-4">
                <p className="text-slate-300 text-sm leading-relaxed">{answer}</p>
              </div>
              <p className="text-xs text-slate-600 mt-2">
                ✏️ Personalise this answer with your own specific examples before your interview.
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function CategorySection({
  category,
  qaPairs,
}: {
  category: string;
  qaPairs: { question: string; answer: string; index: number }[];
}) {
  const meta = CATEGORY_META[category] ?? CATEGORY_META.behavioral;
  const [sectionOpen, setSectionOpen] = useState(true);

  if (qaPairs.length === 0) return null;

  return (
    <div className="space-y-3">
      {/* Section header */}
      <button
        onClick={() => setSectionOpen((v) => !v)}
        className="flex items-center gap-3 w-full text-left group"
      >
        <span className="text-lg">{meta.icon}</span>
        <h3 className={`text-sm font-bold uppercase tracking-widest ${meta.color}`}>
          {meta.label} Questions
        </h3>
        <span className="text-xs text-slate-600 ml-1">({qaPairs.length})</span>
        <ChevronDown
          className={`w-3.5 h-3.5 text-slate-600 ml-auto transition-transform ${sectionOpen ? "rotate-180" : ""}`}
        />
      </button>

      <AnimatePresence>
        {sectionOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2"
          >
            {qaPairs.map((qa) => (
              <QACard key={qa.index} question={qa.question} answer={qa.answer} index={qa.index} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function InterviewPrep({ interviewPrep }: Props) {
  const { qa_pairs, tips } = interviewPrep;

  const behavioral   = qa_pairs.filter((q) => q.category === "behavioral");
  const technical    = qa_pairs.filter((q) => q.category === "technical");
  const situational  = qa_pairs.filter((q) => q.category === "situational");

  let globalIdx = 0;
  const behavioralWithIdx  = behavioral.map((q)  => ({ ...q, index: globalIdx++ }));
  const technicalWithIdx   = technical.map((q)   => ({ ...q, index: globalIdx++ }));
  const situationalWithIdx = situational.map((q) => ({ ...q, index: globalIdx++ }));

  return (
    <div className="space-y-8">
      {/* Intro banner */}
      <div className="glass rounded-2xl border border-brand-500/20 bg-brand-500/5 p-4 flex items-start gap-3">
        <MessageSquare className="w-5 h-5 text-brand-400 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-white font-medium text-sm">AI-generated Q&A — tailored to your profile</p>
          <p className="text-slate-400 text-xs mt-0.5">
            Click any question to reveal a sample answer written from your perspective.
            Personalise the answers with your real stories before your interview.
          </p>
        </div>
      </div>

      {/* Q&A sections */}
      {qa_pairs.length === 0 ? (
        <p className="text-slate-500 text-sm text-center py-8">
          No questions generated — this may happen if the analysis was very short.
        </p>
      ) : (
        <div className="space-y-8">
          <CategorySection category="behavioral"  qaPairs={behavioralWithIdx}  />
          <CategorySection category="technical"   qaPairs={technicalWithIdx}   />
          <CategorySection category="situational" qaPairs={situationalWithIdx} />
        </div>
      )}

      {/* Tips */}
      {tips.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-4">
            Interview Tips
          </h3>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {tips.map((tip, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.07 }}
                className="glass rounded-2xl border border-white/10 p-4 flex gap-3"
              >
                <span className="flex-shrink-0 mt-0.5">
                  {TIP_ICONS[i % TIP_ICONS.length]}
                </span>
                <p className="text-slate-300 text-xs leading-relaxed">{tip}</p>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
