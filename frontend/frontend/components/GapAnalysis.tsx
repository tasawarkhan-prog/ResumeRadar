"use client";
import { motion } from "framer-motion";
import { AlertTriangle, Info, TrendingUp } from "lucide-react";
import { GapItem } from "@/lib/types";

interface Props {
  gaps: GapItem[];
}

export default function GapAnalysis({ gaps }: Props) {
  const critical = gaps.filter((g) => g.gap_type === "missing" && g.importance === "required");
  const unstated = gaps.filter((g) => g.gap_type === "present_but_unstated");
  const preferred = gaps.filter((g) => g.gap_type === "missing" && g.importance === "preferred");

  if (gaps.length === 0) {
    return (
      <div className="glass rounded-2xl p-8 border border-green-500/20 text-center">
        <TrendingUp className="w-10 h-10 text-green-400 mx-auto mb-3" />
        <p className="text-green-400 font-semibold text-lg">No critical gaps detected!</p>
        <p className="text-slate-500 text-sm mt-1">
          Your resume matches all required skills for this role.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Critical missing */}
      {critical.length > 0 && (
        <GapGroup
          title="Critical Gaps — Missing Required Skills"
          icon={<AlertTriangle className="w-4 h-4 text-red-400" />}
          items={critical}
          cardClass="border-red-500/20"
          badgeClass="pill-red"
          delay={0}
        />
      )}

      {/* Unstated skills */}
      {unstated.length > 0 && (
        <GapGroup
          title="Easy Wins — You Have These, Just Not Stated"
          icon={<Info className="w-4 h-4 text-yellow-400" />}
          items={unstated}
          cardClass="border-yellow-500/20"
          badgeClass="pill-yellow"
          delay={0.1}
        />
      )}

      {/* Preferred gaps */}
      {preferred.length > 0 && (
        <GapGroup
          title="Nice-to-Have Gaps"
          icon={<Info className="w-4 h-4 text-slate-400" />}
          items={preferred}
          cardClass="border-white/[0.06]"
          badgeClass="pill-blue"
          delay={0.2}
        />
      )}
    </div>
  );
}

function GapGroup({
  title,
  icon,
  items,
  cardClass,
  badgeClass,
  delay,
}: {
  title: string;
  icon: React.ReactNode;
  items: GapItem[];
  cardClass: string;
  badgeClass: string;
  delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className={`glass rounded-2xl p-5 border ${cardClass}`}
    >
      <div className="flex items-center gap-2 mb-4">
        {icon}
        <h4 className="text-sm font-semibold text-slate-300">{title}</h4>
        <span className="ml-auto text-xs text-slate-500">{items.length} item{items.length > 1 ? "s" : ""}</span>
      </div>
      <div className="space-y-3">
        {items.map((gap, i) => (
          <motion.div
            key={gap.skill}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: delay + i * 0.06 }}
            className="flex items-start gap-3"
          >
            <span className={`pill ${badgeClass} mt-0.5 flex-shrink-0`}>
              {gap.skill}
            </span>
            {gap.suggestion && (
              <p className="text-sm text-slate-400 leading-relaxed">{gap.suggestion}</p>
            )}
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
