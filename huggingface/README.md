---
title: ResumeRadar
emoji: 🎯
colorFrom: indigo
colorTo: blue
sdk: gradio
sdk_version: "5.9.1"
app_file: app.py
pinned: false
license: mit
short_description: AI resume analyzer with fit score & interview prep
---

# ResumeRadar 🎯

**AI/ML Job Match Engine — Full Analysis in ~30 Seconds**

Upload your resume, paste a job description — get fit score, skill gaps, AI-rewritten resume,
tailored cover letter, interview prep questions, and a downloadable styled template.

## How to Use

1. Enter your **Groq** or **Gemini** API key *(free tier — see below)*
2. Upload your resume (PDF, DOCX, or TXT — up to 10 MB)
3. Paste the full job description
4. Choose a cover letter tone and resume template
5. Click **Analyze My Resume** and wait ~30 seconds

## Free API Keys

| Provider | Link | Free Tier |
|----------|------|-----------|
| **Groq** (Llama 3.3 70B) | https://console.groq.com/keys | 14,400 req/day |
| **Gemini** (2.0 Flash) | https://aistudio.google.com/app/apikey | 1,500 req/day |

> **Space owners**: set `GROQ_API_KEY` and/or `GEMINI_API_KEY` in HF Secrets — users can then
> run analysis without entering a key at all.

## What You Get (8 Output Tabs)

| Tab | What it shows |
|-----|---------------|
| 📊 **Score** | Fit score (0–100), ATS keyword score, strengths summary |
| 🎯 **Skill Breakdown** | Every job skill — matched ✅ or missing ❌ with semantic similarity % |
| ⚠️ **Gap Analysis** | Critical missing skills + easy wins (skills you have but didn't write) |
| ✍️ **Rewritten Resume** | Full STAR-method rewrite optimised for ATS and the specific role |
| 📝 **Cover Letter** | 280–340 word tailored letter (professional / enthusiastic / concise) |
| 🔍 **Changes Made** | Before/after diff with reasoning for each improvement |
| 🎤 **Interview Prep** | Behavioral, technical & situational questions + coaching tips |
| 📥 **Download Template** | Styled HTML resume (4 templates) → open in browser → Save as PDF |

## Scoring (v2.1)

- Scores are **never zero** for partial matches — graduated partial credit at every similarity level
- Exact keyword match → 100%
- Strong semantic match (≥0.65) → uses raw similarity
- Partial match (0.45–0.65) → interpolated partial credit
- Weak match (0.25–0.45) → 70% of similarity
- Minimal match (<0.25) → minimum floor of 6%
- Fit score floored at **12%** — no resume ever shows 0

## Resume Templates

Four professional HTML templates available for download:

- **Modern Pro** — Two-column indigo sidebar
- **Executive Classic** — Centered serif with double-rule dividers
- **Minimal ATS-Safe** — Clean, ATS-first, keyword-dense layout
- **Tech Stack** — Dark header, monospace accents, badge skills

Download the `.html` file → open in browser → **Ctrl+P → Save as PDF** for a professional PDF.
Or open in Microsoft Word / Google Docs for full editing.

## Privacy

Your API keys and resume content are processed **only during your session** and never stored,
logged, or shared. Files are deleted after processing.

## Tech Stack

- **LLM**: Groq (Llama 3.3 70B) · Google Gemini 2.0 Flash
- **NLP**: sentence-transformers `all-MiniLM-L6-v2` for semantic skill matching
- **UI**: Gradio 5.9.1 (HF Spaces) · Next.js 15 + FastAPI (local/production)
- **Matching**: Cosine similarity with graduated partial-credit scoring
