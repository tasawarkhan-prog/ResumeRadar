<div align="center">

<img src="https://img.shields.io/badge/Live%20Demo-HuggingFace%20Space-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="HuggingFace Space"/>
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js"/>
<img src="https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/Gradio-5.9.1-FF7C00?style=for-the-badge&logo=gradio&logoColor=white" alt="Gradio"/>
<img src="https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge" alt="MIT License"/>

<br/><br/>

# 🎯 ResumeRadar

### AI-Powered Job Match Engine — Full Resume Analysis in ~30 Seconds

**Upload your resume · Paste a job description · Get fit score, skill gaps, ATS-optimized rewrite, tailored cover letter, interview prep & downloadable templates**

<br/>

[![🚀 Try Live on HuggingFace](https://img.shields.io/badge/%F0%9F%9A%80%20Try%20Live%20on%20HuggingFace-ResumeRadar-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co/spaces/Tasawar-prog1/ResumeRadar)

<br/>

</div>

---

## ✨ What ResumeRadar Does

Most job seekers send the same resume everywhere and wonder why they get no callbacks. **ResumeRadar fixes that.** It reads both your resume and the target job description with AI, then gives you an honest, actionable match report — in under 30 seconds.

```
Your Resume  ──┐
               ├──▶  ResumeRadar AI Engine  ──▶  8 Output Tabs
Job Description┘         (Groq / Gemini)         (Score · Gaps · Rewrite · ...)
```

---

## 🖥️ Output Tabs (8 Total)

| Tab | What You Get |
|-----|-------------|
| 📊 **Fit Score** | Overall match score 0–100, ATS keyword score, strengths summary |
| 🎯 **Skill Breakdown** | Every required skill — matched ✅ or missing ❌ with semantic similarity % |
| ⚠️ **Gap Analysis** | Critical missing skills + easy wins (skills you have but didn't write) |
| ✍️ **Rewritten Resume** | Full STAR-method AI rewrite, ATS-optimized for the specific role |
| 📝 **Cover Letter** | 280–340 word tailored letter in Professional / Enthusiastic / Concise tone |
| 🔍 **Changes Made** | Before/after diff with reasoning for every improvement |
| 🎤 **Interview Prep** | Behavioral, technical & situational Q&A with sample answers + coaching tips |
| 📥 **Download Template** | Export in **HTML** (→ PDF via browser print) · **DOCX** (Word) · **TXT** (ATS-safe) |

---

## 🏗️ Project Architecture

```
ResumeRadar/
│
├── huggingface/            ← 🤗 HuggingFace Space (Gradio, zero-install)
│   ├── app.py              ← Single-file Gradio app (1 800 lines)
│   ├── requirements.txt    ← Pinned dependencies
│   └── README.md           ← HF Space card
│
├── backend/                ← 🐍 FastAPI backend (local / production)
│   ├── main.py             ← REST API entry point
│   ├── requirements.txt    ← Python dependencies
│   ├── .env.example        ← API key template
│   ├── models/
│   │   └── schemas.py      ← Pydantic request/response models
│   ├── utils/
│   │   ├── extractor.py    ← PDF / DOCX / TXT text extraction
│   │   └── llm_client.py   ← Groq + Gemini multi-provider client
│   └── agents/
│       ├── resume_parser.py    ← Structured resume parsing
│       ├── job_analyzer.py     ← Job description analysis
│       ├── semantic_matcher.py ← Cosine similarity skill matching
│       ├── rewriter.py         ← STAR-method resume rewriter
│       ├── cover_letter.py     ← Tone-aware cover letter generator
│       ├── interview_agent.py  ← Q&A + coaching tips generator
│       └── pipeline.py         ← Orchestrates all agents
│
└── frontend/               ← ⚛️ Next.js 15 frontend (local / production)
    ├── app/
    │   └── layout.tsx
    ├── components/
    │   ├── Hero.tsx
    │   ├── Navbar.tsx
    │   ├── ScoreGauge.tsx
    │   ├── SkillMatrix.tsx
    │   ├── GapAnalysis.tsx
    │   ├── ResumeRewrite.tsx
    │   ├── CoverLetter.tsx
    │   └── ParticleBackground.tsx
    ├── package.json
    └── next.config.mjs
```

---

## 🤗 HuggingFace Space (Zero-Install — Try Now)

> **No installation needed.** Just open the link, paste your API key (free), upload your resume, and go.

**👉 [https://huggingface.co/spaces/Tasawar-prog1/ResumeRadar](https://huggingface.co/spaces/Tasawar-prog1/ResumeRadar)**

### Free API Keys

| Provider | Sign-up Link | Free Tier |
|----------|-------------|-----------|
| **Groq** (Llama 3.3 70B) | [console.groq.com/keys](https://console.groq.com/keys) | 14,400 req/day |
| **Gemini** (2.0 Flash) | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) | 1,500 req/day |

### HF Space Quick Start

1. Click the link above
2. Enter your Groq **or** Gemini API key (only one needed)
3. Upload your resume — PDF, DOCX, or TXT up to 10 MB
4. Paste the full job description
5. Choose a cover letter tone and resume template
6. Click **🚀 Analyze My Resume** — results in ~30 seconds

---

## 💻 Local Setup (Full Stack)

### Prerequisites

- Python 3.10+
- Node.js 18+
- A free Groq or Gemini API key (links above)

---

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ResumeRadar.git
cd ResumeRadar
```

---

### 2️⃣ Backend Setup (FastAPI)

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Configure your API keys:**

```bash
# Copy the example env file
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**Start the backend server:**

```bash
uvicorn main:app --reload --port 8000
```

Backend API runs at → `http://localhost:8000`
Auto-generated docs → `http://localhost:8000/docs`

---

### 3️⃣ Frontend Setup (Next.js)

```bash
cd ../frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local
```

Open `.env.local` and set the API base URL:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Start the frontend:**

```bash
npm run dev
```

Frontend runs at → `http://localhost:3000`

---

### 4️⃣ HuggingFace Gradio App (Local)

To run just the Gradio app locally (no Next.js or FastAPI needed):

```bash
cd huggingface

pip install -r requirements.txt

python app.py
```

App runs at → `http://localhost:7860`

---

## 🧠 How the AI Matching Works

ResumeRadar uses **semantic similarity** — not just keyword matching — so partial skill matches are rewarded fairly.

```
Skill in Job Description
        │
        ▼
sentence-transformers (all-MiniLM-L6-v2)
        │
        ▼
Cosine Similarity vs. every skill in your resume
        │
        ▼
Graduated Partial-Credit Scoring:
  Exact keyword match      → 100%
  Strong match  (≥ 0.65)  → raw similarity score
  Partial match (0.45–0.65)→ interpolated partial credit
  Weak match   (0.25–0.45) → 70% of similarity
  Minimal match (< 0.25)  → floor of 6%

Fit Score floored at 12% — no resume ever shows 0
```

---

## 📋 Resume Templates (4 Styles)

All templates are export-ready. Change template and format **without re-running analysis**.

| Template | Style |
|----------|-------|
| **Modern Pro** | Two-column layout with indigo sidebar |
| **Executive Classic** | Centered serif with double-rule dividers |
| **Minimal ATS-Safe** | Clean single-column, ATS-first layout |
| **Tech Stack** | Dark header, monospace accents, skill badges |

**Export formats:** HTML → open in browser → Ctrl+P → Save as PDF · DOCX (Word/Google Docs) · TXT (ATS upload)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | Groq (Llama 3.3 70B) · Google Gemini 2.0 Flash |
| **NLP** | sentence-transformers `all-MiniLM-L6-v2` |
| **HF Space UI** | Gradio 5.9.1 |
| **Backend API** | FastAPI · Python 3.10+ |
| **Frontend** | Next.js 15 · TypeScript · Tailwind CSS |
| **File Parsing** | pdfplumber · PyPDF2 · python-docx |
| **Matching** | scikit-learn cosine similarity |
| **Export** | python-docx (DOCX) · plain text (TXT) · HTML |

---

## 🔐 Privacy

- API keys are used **only during your session** and never stored, logged, or shared
- Uploaded resume files are processed in memory and deleted after analysis
- No data is persisted between sessions

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with ❤️ by [Tasawar](https://github.com/YOUR_USERNAME)**

[![HuggingFace Space](https://img.shields.io/badge/🤗%20Live%20Demo-ResumeRadar-FFD21E?style=flat-square)](https://huggingface.co/spaces/Tasawar-prog1/ResumeRadar)

*If this project helped you land an interview, give it a ⭐ — it means a lot!*

</div>
