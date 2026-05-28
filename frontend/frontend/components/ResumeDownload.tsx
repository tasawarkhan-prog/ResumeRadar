"use client";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Download, FileText, FileType2, Eye, CheckCircle2 } from "lucide-react";
import { ResumeData, JobData } from "@/lib/types";

interface Props {
  resumeData: ResumeData;
  jobData: JobData;
  rewrittenText: string;
}

// ─── Template definitions ───────────────────────────────────────────────
const TEMPLATES = [
  {
    id: "modern",
    name: "Modern Pro",
    description: "Clean two-column with indigo accent bar",
    accent: "#6366f1",
    preview: "◼ ░░░░░░░░░░\n──────────────\n● Skills  ● Exp",
    tag: "Popular",
    tagColor: "pill-blue",
  },
  {
    id: "executive",
    name: "Executive",
    description: "Classic centered header, serif elegance",
    accent: "#1e293b",
    preview: "  ══ NAME ══\n  ──────────\n  Experience",
    tag: "Formal",
    tagColor: "pill-yellow",
  },
  {
    id: "creative",
    name: "Creative",
    description: "Left sidebar gradient, bold typography",
    accent: "#06b6d4",
    preview: "▌ NAME    ░░\n▌ Skills  ░░\n▌ Work    ░░",
    tag: "Designer",
    tagColor: "pill-green",
  },
  {
    id: "minimal",
    name: "Minimal Clean",
    description: "Ultra-minimal, ATS-first, whitespace heavy",
    accent: "#374151",
    preview: "Name\n─────────────\nExperience\nSkills",
    tag: "ATS Safe",
    tagColor: "pill-green",
  },
  {
    id: "tech",
    name: "Tech Stack",
    description: "Dark header, monospace touches, tag badges",
    accent: "#0f172a",
    preview: "▓▓▓ NAME ▓▓▓\n░ Skills ░░░\n─ Projects ─",
    tag: "Dev",
    tagColor: "pill-blue",
  },
  {
    id: "elegant",
    name: "Elegant Rose",
    description: "Rose/gold accent with double-rule dividers",
    accent: "#e11d48",
    preview: "✦ Name ✦\n══════════\nExperience",
    tag: "Premium",
    tagColor: "pill-red",
  },
  {
    id: "compact",
    name: "Compact Impact",
    description: "Dense layout, fits more on one page",
    accent: "#7c3aed",
    preview: "NAME | role\n────────────\n▸ Exp ▸ Edu",
    tag: "One-page",
    tagColor: "pill-blue",
  },
  {
    id: "infographic",
    name: "Infographic",
    description: "Progress bars for skills, icon-led sections",
    accent: "#059669",
    preview: "NAME ●●●●○\nSkill ████░\nSkill ███░░",
    tag: "Visual",
    tagColor: "pill-green",
  },
];

// ─── HTML builders per template ─────────────────────────────────────────

function buildHtml(templateId: string, r: ResumeData, j: JobData, body: string): string {
  const name = r.name || "Your Name";
  const email = r.email || "";
  const phone = r.phone || "";
  const summary = r.summary || "";
  const skills = r.skills.map((s) => s.name);
  const exps = r.experiences;
  const edus = r.education;
  const certs = r.certifications;
  const role = j.title || "";

  const contactLine = [email, phone].filter(Boolean).join(" · ");

  const expHtml = exps
    .map(
      (e) => `
    <div class="exp-item">
      <div class="exp-header">
        <strong>${e.role}</strong> — <span class="company">${e.company}</span>
        <span class="duration">${e.duration}</span>
      </div>
      <ul>${e.responsibilities.map((r) => `<li>${r}</li>`).join("")}</ul>
    </div>`
    )
    .join("");

  const eduHtml = edus
    .map(
      (e) => `
    <div class="edu-item">
      <strong>${e.degree}</strong> — ${e.institution}
      ${e.year ? `<span class="duration">${e.year}</span>` : ""}
      ${e.gpa ? `<span class="gpa"> · GPA: ${e.gpa}</span>` : ""}
    </div>`
    )
    .join("");

  const certHtml =
    certs.length > 0
      ? `<section><h2>Certifications</h2><ul>${certs.map((c) => `<li>${c}</li>`).join("")}</ul></section>`
      : "";

  const skillBadges = skills
    .map((s) => `<span class="skill-badge">${s}</span>`)
    .join("");

  const skillList = skills.map((s) => `<li>${s}</li>`).join("");

  const templates: Record<string, string> = {
    // ── MODERN PRO ──────────────────────────────────────────────────────
    modern: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #1e293b; }
  .wrap { display: flex; min-height: 100vh; }
  .sidebar { width: 220px; background: #6366f1; color: white; padding: 28px 18px; flex-shrink: 0; }
  .sidebar h1 { font-size: 20px; font-weight: 700; line-height: 1.2; margin-bottom: 4px; }
  .sidebar .role { font-size: 11px; opacity: 0.8; margin-bottom: 20px; }
  .sidebar .contact { font-size: 11px; opacity: 0.85; line-height: 1.8; margin-bottom: 20px; }
  .sidebar h3 { font-size: 10px; letter-spacing: 1.5px; text-transform: uppercase; opacity: 0.7; margin-bottom: 8px; margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 12px; }
  .sidebar .skill-badge { display: inline-block; background: rgba(255,255,255,0.15); border-radius: 4px; padding: 2px 8px; margin: 2px 2px 2px 0; font-size: 11px; }
  .main { flex: 1; padding: 28px 28px; }
  .main h2 { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #6366f1; border-bottom: 2px solid #6366f1; padding-bottom: 4px; margin-bottom: 14px; margin-top: 24px; }
  .main h2:first-child { margin-top: 0; }
  .summary { color: #475569; line-height: 1.6; }
  .exp-item { margin-bottom: 14px; }
  .exp-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
  .company { color: #6366f1; }
  .duration { font-size: 11px; color: #94a3b8; }
  ul { padding-left: 16px; color: #475569; line-height: 1.7; }
  .edu-item { margin-bottom: 10px; }
  .gpa { color: #94a3b8; }
</style></head><body>
<div class="wrap">
  <div class="sidebar">
    <h1>${name}</h1>
    <div class="role">${role}</div>
    <div class="contact">${email}<br/>${phone}</div>
    <h3>Skills</h3>
    <div>${skillBadges}</div>
    ${certs.length > 0 ? `<h3>Certifications</h3><ul style="padding-left:14px;opacity:.85;font-size:11px;">${certs.map((c) => `<li>${c}</li>`).join("")}</ul>` : ""}
  </div>
  <div class="main">
    ${summary ? `<h2>Profile</h2><p class="summary">${summary}</p>` : ""}
    ${exps.length > 0 ? `<h2>Experience</h2>${expHtml}` : ""}
    ${edus.length > 0 ? `<h2>Education</h2>${eduHtml}` : ""}
  </div>
</div></body></html>`,

    // ── EXECUTIVE ───────────────────────────────────────────────────────
    executive: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Georgia, 'Times New Roman', serif; font-size: 13px; color: #111827; background: #fff; max-width: 800px; margin: 0 auto; padding: 48px 52px; }
  .header { text-align: center; margin-bottom: 28px; padding-bottom: 20px; border-bottom: 2.5px double #1e293b; }
  .header h1 { font-size: 28px; letter-spacing: 4px; text-transform: uppercase; font-weight: 700; }
  .header .role { font-size: 12px; letter-spacing: 2px; color: #6b7280; margin: 4px 0 8px; }
  .header .contact { font-size: 11px; color: #6b7280; letter-spacing: 0.5px; }
  h2 { font-size: 11px; letter-spacing: 3px; text-transform: uppercase; border-bottom: 1px solid #1e293b; padding-bottom: 4px; margin: 24px 0 12px; }
  .summary { font-style: italic; color: #374151; line-height: 1.7; }
  .exp-header { display: flex; justify-content: space-between; }
  .company { color: #374151; }
  .duration { font-size: 11px; color: #9ca3af; font-style: italic; }
  .exp-item { margin-bottom: 14px; }
  ul { padding-left: 18px; color: #4b5563; line-height: 1.75; }
  .edu-item { margin-bottom: 8px; }
  .skill-badge { display: inline-block; border: 1px solid #d1d5db; border-radius: 3px; padding: 1px 8px; margin: 2px; font-size: 11px; font-family: 'Segoe UI', sans-serif; }
</style></head><body>
<div class="header">
  <h1>${name}</h1>
  <div class="role">${role}</div>
  <div class="contact">${contactLine}</div>
</div>
${summary ? `<h2>Executive Profile</h2><p class="summary">${summary}</p>` : ""}
${exps.length > 0 ? `<h2>Professional Experience</h2>${expHtml}` : ""}
${edus.length > 0 ? `<h2>Education</h2>${eduHtml}` : ""}
${skills.length > 0 ? `<h2>Core Competencies</h2><div style="margin-top:8px">${skillBadges}</div>` : ""}
${certHtml}
</body></html>`,

    // ── CREATIVE ────────────────────────────────────────────────────────
    creative: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; background: #fff; }
  .wrap { display: flex; }
  .sidebar { width: 200px; background: linear-gradient(160deg,#0f172a,#06b6d4); color: white; padding: 32px 16px; flex-shrink: 0; }
  .sidebar h1 { font-size: 18px; font-weight: 800; line-height: 1.2; margin-bottom: 6px; }
  .sidebar .role { font-size: 10px; opacity: 0.75; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 20px; }
  .sidebar .contact { font-size: 10.5px; opacity: 0.8; line-height: 2; }
  .sidebar h3 { font-size: 9px; letter-spacing: 2px; text-transform: uppercase; opacity: 0.6; margin: 20px 0 8px; }
  .sidebar li { font-size: 11px; opacity: 0.9; line-height: 1.9; list-style: none; }
  .sidebar li::before { content: "› "; opacity: 0.5; }
  .main { flex: 1; padding: 32px 28px; }
  h2 { font-size: 14px; font-weight: 700; color: #06b6d4; margin: 22px 0 10px; position: relative; padding-left: 14px; }
  h2::before { content:""; position:absolute; left:0; top:2px; width:4px; height:14px; background:#06b6d4; border-radius:2px; }
  .exp-item { margin-bottom: 14px; padding-left: 14px; }
  .exp-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
  .company { color: #06b6d4; font-size: 12px; }
  .duration { font-size: 11px; color: #94a3b8; }
  ul { padding-left: 16px; color: #475569; line-height: 1.7; }
  .summary { color: #475569; line-height: 1.65; padding-left: 14px; }
  .edu-item { padding-left: 14px; margin-bottom: 8px; }
</style></head><body>
<div class="wrap">
  <div class="sidebar">
    <h1>${name}</h1>
    <div class="role">${role}</div>
    <div class="contact">${email}<br/>${phone}</div>
    ${skills.length > 0 ? `<h3>Skills</h3><ul>${skillList}</ul>` : ""}
    ${certs.length > 0 ? `<h3>Certifications</h3><ul>${certs.map((c) => `<li>${c}</li>`).join("")}</ul>` : ""}
  </div>
  <div class="main">
    ${summary ? `<h2>About Me</h2><p class="summary">${summary}</p>` : ""}
    ${exps.length > 0 ? `<h2>Experience</h2>${expHtml}` : ""}
    ${edus.length > 0 ? `<h2>Education</h2>${eduHtml}` : ""}
  </div>
</div></body></html>`,

    // ── MINIMAL ─────────────────────────────────────────────────────────
    minimal: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #111; background: #fff; max-width: 760px; margin: 0 auto; padding: 42px 48px; }
  h1 { font-size: 22px; font-weight: 700; margin-bottom: 2px; }
  .contact { font-size: 11px; color: #555; margin-bottom: 28px; }
  h2 { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; border-bottom: 1px solid #999; padding-bottom: 3px; margin: 22px 0 10px; }
  .summary { color: #333; line-height: 1.65; }
  .exp-item { margin-bottom: 12px; }
  .exp-header { display: flex; justify-content: space-between; }
  .company { color: #444; }
  .duration { font-size: 11px; color: #888; }
  ul { padding-left: 16px; color: #333; line-height: 1.75; }
  .edu-item { margin-bottom: 8px; }
  .skills { display: flex; flex-wrap: wrap; gap: 4px; }
  .skills span { border: 1px solid #ccc; border-radius: 3px; padding: 1px 7px; font-size: 11px; }
</style></head><body>
<h1>${name}</h1>
<div class="contact">${contactLine}${role ? " · " + role : ""}</div>
${summary ? `<h2>Summary</h2><p class="summary">${summary}</p>` : ""}
${exps.length > 0 ? `<h2>Experience</h2>${expHtml}` : ""}
${edus.length > 0 ? `<h2>Education</h2>${eduHtml}` : ""}
${skills.length > 0 ? `<h2>Skills</h2><div class="skills">${skills.map((s) => `<span>${s}</span>`).join("")}</div>` : ""}
${certHtml}
</body></html>`,

    // ── TECH STACK ──────────────────────────────────────────────────────
    tech: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Consolas','Courier New', monospace; font-size: 12px; background: #fff; color: #1e293b; }
  .header { background: #0f172a; color: #e2e8f0; padding: 24px 32px; }
  .header h1 { font-size: 24px; font-weight: 700; color: #38bdf8; letter-spacing: 2px; }
  .header .meta { font-size: 11px; color: #94a3b8; margin-top: 4px; }
  .body { padding: 28px 32px; }
  h2 { font-size: 11px; color: #0f172a; background: #e2e8f0; padding: 4px 10px; margin: 20px 0 10px; border-left: 4px solid #38bdf8; font-family: 'Segoe UI',sans-serif; letter-spacing: 1px; text-transform: uppercase; }
  .summary { font-family: 'Segoe UI',sans-serif; color: #475569; line-height: 1.65; }
  .exp-item { margin-bottom: 14px; }
  .exp-header { display: flex; justify-content: space-between; font-family: 'Segoe UI',sans-serif; }
  .company { color: #38bdf8; }
  .duration { font-size: 10px; color: #94a3b8; }
  ul { padding-left: 16px; color: #475569; line-height: 1.75; font-family: 'Segoe UI',sans-serif; }
  .skill-badge { display: inline-block; background: #0f172a; color: #38bdf8; border-radius: 4px; padding: 2px 9px; margin: 2px; font-size: 11px; }
  .edu-item { font-family: 'Segoe UI',sans-serif; margin-bottom: 8px; }
</style></head><body>
<div class="header">
  <h1>${name}</h1>
  <div class="meta">${role ? "// " + role + " · " : ""}${contactLine}</div>
</div>
<div class="body">
  ${summary ? `<h2>// Profile</h2><p class="summary">${summary}</p>` : ""}
  ${skills.length > 0 ? `<h2>// Tech Stack</h2><div style="margin-top:6px">${skillBadges}</div>` : ""}
  ${exps.length > 0 ? `<h2>// Experience</h2>${expHtml}` : ""}
  ${edus.length > 0 ? `<h2>// Education</h2>${eduHtml}` : ""}
  ${certHtml}
</div></body></html>`,

    // ── ELEGANT ROSE ────────────────────────────────────────────────────
    elegant: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Lato:wght@300;400;700&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Lato', sans-serif; font-size: 13px; color: #1f2937; background: #fff; max-width: 800px; margin: 0 auto; padding: 48px 56px; }
  .header { text-align: center; margin-bottom: 32px; }
  .header h1 { font-family: 'Playfair Display', Georgia, serif; font-size: 32px; color: #e11d48; letter-spacing: 2px; }
  .header .role { font-size: 12px; letter-spacing: 3px; text-transform: uppercase; color: #9ca3af; margin: 6px 0 10px; }
  .header .contact { font-size: 11px; color: #6b7280; }
  .divider { text-align: center; color: #e11d48; margin: 4px 0; font-size: 18px; letter-spacing: 6px; }
  h2 { font-family: 'Playfair Display', serif; font-size: 15px; color: #e11d48; margin: 26px 0 10px; border-bottom: 1px solid #fecdd3; padding-bottom: 6px; }
  .summary { font-style: italic; color: #374151; line-height: 1.75; }
  .exp-header { display: flex; justify-content: space-between; }
  .company { color: #e11d48; font-size: 12px; }
  .duration { font-size: 11px; color: #9ca3af; }
  .exp-item { margin-bottom: 14px; }
  ul { padding-left: 18px; color: #4b5563; line-height: 1.8; }
  .edu-item { margin-bottom: 8px; }
  .skill-badge { display: inline-block; border: 1px solid #fecdd3; background: #fff1f2; border-radius: 3px; padding: 2px 9px; margin: 2px; font-size: 11px; color: #9f1239; }
</style></head><body>
<div class="header">
  <h1>${name}</h1>
  <div class="role">${role}</div>
  <div class="divider">✦ ✦ ✦</div>
  <div class="contact">${contactLine}</div>
</div>
${summary ? `<h2>Profile</h2><p class="summary">${summary}</p>` : ""}
${exps.length > 0 ? `<h2>Experience</h2>${expHtml}` : ""}
${edus.length > 0 ? `<h2>Education</h2>${eduHtml}` : ""}
${skills.length > 0 ? `<h2>Core Skills</h2><div style="margin-top:8px">${skillBadges}</div>` : ""}
${certHtml}
</body></html>`,

    // ── COMPACT IMPACT ──────────────────────────────────────────────────
    compact: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11.5px; color: #111; background: #fff; max-width: 760px; margin: 0 auto; padding: 30px 36px; }
  .header { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid #7c3aed; padding-bottom: 8px; margin-bottom: 14px; }
  .header h1 { font-size: 20px; font-weight: 700; color: #7c3aed; }
  .header .meta { text-align: right; font-size: 10.5px; color: #6b7280; line-height: 1.7; }
  h2 { font-size: 10px; text-transform: uppercase; letter-spacing: 2px; color: #7c3aed; border-left: 3px solid #7c3aed; padding-left: 7px; margin: 14px 0 7px; }
  .summary { color: #374151; line-height: 1.55; }
  .exp-item { margin-bottom: 8px; }
  .exp-header { display: flex; justify-content: space-between; }
  .company { color: #7c3aed; }
  .duration { font-size: 10px; color: #9ca3af; }
  ul { padding-left: 14px; color: #374151; line-height: 1.65; }
  ul li { margin-bottom: 1px; }
  .edu-item { margin-bottom: 6px; }
  .skills { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
  .skill-badge { background: #ede9fe; color: #5b21b6; border-radius: 4px; padding: 1px 7px; font-size: 10.5px; }
</style></head><body>
<div class="header">
  <div>
    <h1>${name}</h1>
    <div style="font-size:11px;color:#7c3aed;margin-top:2px">${role}</div>
  </div>
  <div class="meta">${email}<br/>${phone}</div>
</div>
${summary ? `<h2>Summary</h2><p class="summary">${summary}</p>` : ""}
${exps.length > 0 ? `<h2>Experience</h2>${expHtml}` : ""}
${edus.length > 0 ? `<h2>Education</h2>${eduHtml}` : ""}
${skills.length > 0 ? `<h2>Skills</h2><div class="skills">${skillBadges}</div>` : ""}
${certHtml}
</body></html>`,

    // ── INFOGRAPHIC ─────────────────────────────────────────────────────
    infographic: `<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; background: #fff; }
  .wrap { display: flex; min-height: 100vh; }
  .sidebar { width: 230px; background: #064e3b; color: white; padding: 30px 18px; flex-shrink: 0; }
  .sidebar h1 { font-size: 20px; font-weight: 700; margin-bottom: 4px; }
  .sidebar .role { font-size: 11px; opacity: 0.7; margin-bottom: 20px; }
  .sidebar .contact { font-size: 11px; opacity: 0.8; line-height: 2; margin-bottom: 20px; }
  .sidebar h3 { font-size: 9px; letter-spacing: 2px; text-transform: uppercase; opacity: 0.55; margin: 18px 0 8px; }
  .bar-label { display: flex; justify-content: space-between; font-size: 10.5px; margin-bottom: 2px; }
  .bar-bg { background: rgba(255,255,255,0.15); border-radius: 4px; height: 6px; margin-bottom: 8px; }
  .bar-fill { background: #10b981; border-radius: 4px; height: 6px; }
  .main { flex: 1; padding: 30px 28px; }
  h2 { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #059669; border-bottom: 2px solid #059669; padding-bottom: 4px; margin: 22px 0 12px; }
  h2:first-child { margin-top: 0; }
  .summary { color: #374151; line-height: 1.65; }
  .exp-item { margin-bottom: 12px; }
  .exp-header { display: flex; justify-content: space-between; }
  .company { color: #059669; }
  .duration { font-size: 11px; color: #9ca3af; }
  ul { padding-left: 16px; color: #475569; line-height: 1.7; }
  .edu-item { margin-bottom: 8px; }
</style></head><body>
<div class="wrap">
  <div class="sidebar">
    <h1>${name}</h1>
    <div class="role">${role}</div>
    <div class="contact">${email}<br/>${phone}</div>
    ${
      skills.length > 0
        ? `<h3>Skills</h3>${skills
            .slice(0, 8)
            .map((s, i) => {
              const pct = Math.max(60, 100 - i * 8);
              return `<div class="bar-label"><span>${s}</span><span>${pct}%</span></div>
              <div class="bar-bg"><div class="bar-fill" style="width:${pct}%"></div></div>`;
            })
            .join("")}`
        : ""
    }
    ${certs.length > 0 ? `<h3>Certifications</h3><ul style="padding-left:14px;font-size:11px;opacity:.85;">${certs.map((c) => `<li>${c}</li>`).join("")}</ul>` : ""}
  </div>
  <div class="main">
    ${summary ? `<h2>Profile</h2><p class="summary">${summary}</p>` : ""}
    ${exps.length > 0 ? `<h2>Experience</h2>${expHtml}` : ""}
    ${edus.length > 0 ? `<h2>Education</h2>${eduHtml}` : ""}
  </div>
</div></body></html>`,
  };

  return templates[templateId] ?? templates["modern"];
}

// ─── Download helpers ────────────────────────────────────────────────────

function downloadPdf(html: string, filename: string) {
  const win = window.open("", "_blank");
  if (!win) { alert("Allow popups for PDF download."); return; }
  win.document.write(html);
  win.document.close();
  win.focus();
  setTimeout(() => { win.print(); }, 600);
}

function downloadWord(html: string, filename: string) {
  const wordHtml = `<html xmlns:o='urn:schemas-microsoft-com:office:office'
    xmlns:w='urn:schemas-microsoft-com:office:word'
    xmlns='http://www.w3.org/TR/REC-html40'>
    <head><meta charset='utf-8'><title>${filename}</title>
    <!--[if gte mso 9]><xml><w:WordDocument><w:View>Print</w:View>
    <w:Zoom>90</w:Zoom></w:WordDocument></xml><![endif]--></head>
    <body>${html}</body></html>`;
  const blob = new Blob([wordHtml], { type: "application/msword" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename + ".doc"; a.click();
  URL.revokeObjectURL(url);
}

function downloadTxt(r: ResumeData, j: JobData, rewritten: string, filename: string) {
  const lines: string[] = [
    r.name, r.email, r.phone, j.title ? `Applying for: ${j.title}` : "",
    "", "─".repeat(60), "REWRITTEN RESUME", "─".repeat(60), "",
    rewritten,
  ];
  const blob = new Blob([lines.filter(Boolean).join("\n")], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename + ".txt"; a.click();
  URL.revokeObjectURL(url);
}

// ─── Component ───────────────────────────────────────────────────────────

export default function ResumeDownload({ resumeData, jobData, rewrittenText }: Props) {
  const [selected, setSelected] = useState("modern");
  const [downloaded, setDownloaded] = useState<string | null>(null);

  const filename = `${(resumeData.name || "resume").replace(/\s+/g, "_")}_resume`;

  const triggerDownload = (type: "pdf" | "word" | "txt") => {
    const html = buildHtml(selected, resumeData, jobData, rewrittenText);
    if (type === "pdf") downloadPdf(html, filename);
    else if (type === "word") downloadWord(html, filename);
    else downloadTxt(resumeData, jobData, rewrittenText, filename);
    setDownloaded(type);
    setTimeout(() => setDownloaded(null), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Template grid */}
      <div>
        <p className="text-sm text-slate-400 mb-4">
          Choose a template — then download as PDF, editable Word, or plain text.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {TEMPLATES.map((t) => (
            <motion.button
              key={t.id}
              onClick={() => setSelected(t.id)}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className={`
                relative text-left rounded-2xl border p-4 transition-all duration-200
                ${selected === t.id
                  ? "border-brand-500 bg-brand-500/10 shadow-lg shadow-brand-500/20"
                  : "border-white/10 glass hover:border-brand-500/40"
                }
              `}
            >
              {selected === t.id && (
                <CheckCircle2 className="absolute top-3 right-3 w-4 h-4 text-brand-400" />
              )}
              {/* Color swatch */}
              <div
                className="w-full h-1.5 rounded-full mb-3"
                style={{ background: t.accent }}
              />
              {/* ASCII preview */}
              <pre className="text-[9px] text-slate-500 font-mono leading-relaxed mb-3 whitespace-pre">
                {t.preview}
              </pre>
              <p className="text-white text-sm font-semibold">{t.name}</p>
              <p className="text-slate-500 text-xs mt-0.5">{t.description}</p>
              <span className={`pill ${t.tagColor} text-[10px] mt-2 inline-block`}>
                {t.tag}
              </span>
            </motion.button>
          ))}
        </div>
      </div>

      {/* Selected template info + download buttons */}
      <AnimatePresence mode="wait">
        <motion.div
          key={selected}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="glass rounded-2xl border border-white/10 p-6"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
            <div>
              <h3 className="text-white font-semibold text-lg">
                {TEMPLATES.find((t) => t.id === selected)?.name}
              </h3>
              <p className="text-slate-400 text-sm mt-0.5">
                {TEMPLATES.find((t) => t.id === selected)?.description}
              </p>
            </div>
            <span
              className={`pill ${TEMPLATES.find((t) => t.id === selected)?.tagColor} self-start sm:self-auto`}
            >
              {TEMPLATES.find((t) => t.id === selected)?.tag}
            </span>
          </div>

          <div className="grid sm:grid-cols-3 gap-3">
            {/* PDF */}
            <motion.button
              onClick={() => triggerDownload("pdf")}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="flex flex-col items-center gap-2 rounded-xl border border-brand-500/30 bg-brand-500/10 hover:bg-brand-500/20 p-4 transition-all group"
            >
              <FileText className="w-6 h-6 text-brand-400 group-hover:scale-110 transition-transform" />
              <span className="text-white font-medium text-sm">Download PDF</span>
              <span className="text-slate-500 text-xs text-center">
                Opens print dialog — Save as PDF
              </span>
              {downloaded === "pdf" && (
                <CheckCircle2 className="w-4 h-4 text-green-400" />
              )}
            </motion.button>

            {/* Word */}
            <motion.button
              onClick={() => triggerDownload("word")}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="flex flex-col items-center gap-2 rounded-xl border border-cyan-500/30 bg-cyan-500/10 hover:bg-cyan-500/20 p-4 transition-all group"
            >
              <FileType2 className="w-6 h-6 text-cyan-400 group-hover:scale-110 transition-transform" />
              <span className="text-white font-medium text-sm">Download Word</span>
              <span className="text-slate-500 text-xs text-center">
                Editable .doc — open in Word or Docs
              </span>
              {downloaded === "word" && (
                <CheckCircle2 className="w-4 h-4 text-green-400" />
              )}
            </motion.button>

            {/* TXT */}
            <motion.button
              onClick={() => triggerDownload("txt")}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
              className="flex flex-col items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20 p-4 transition-all group"
            >
              <Download className="w-6 h-6 text-emerald-400 group-hover:scale-110 transition-transform" />
              <span className="text-white font-medium text-sm">Plain Text</span>
              <span className="text-slate-500 text-xs text-center">
                ATS-safe .txt — paste anywhere
              </span>
              {downloaded === "txt" && (
                <CheckCircle2 className="w-4 h-4 text-green-400" />
              )}
            </motion.button>
          </div>

          <p className="text-slate-600 text-xs mt-4 text-center">
            <Eye className="w-3 h-3 inline mr-1" />
            PDF preview opens in a new tab — use <strong>Ctrl+P → Save as PDF</strong> to download
          </p>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
