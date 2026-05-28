"""
ResumeRadar — HuggingFace Spaces (Gradio)
Self-contained: includes all pipeline logic.
v2.2 — Gradio 5.x / Python 3.13 compatible, graduated scoring,
        interview prep with humanized answers, template downloads.
"""

import io
import os
import re
import json
import time
import tempfile
from pathlib import Path
from functools import lru_cache
from typing import Optional

# ─── Patch gradio_client 5.9.x bool-schema crash ─────────────────────────────
# Gradio 5.9.x calls `if "const" in schema` without checking isinstance(schema, dict).
# JSON Schema allows boolean schemas (True/False) — Python can't use `in` on a bool.
# This crashes every page load via routes.py:main → api_info → get_api_info.
# We patch the internal helper to guard against non-dict schemas.
try:
    import gradio_client.utils as _gcu  # import before gr so patch is in place

    _orig_j2p = _gcu._json_schema_to_python_type

    def _safe_j2p(schema, defs=None):
        if not isinstance(schema, dict):
            return "Any"          # boolean schema → treat as Any
        return _orig_j2p(schema, defs)

    _gcu._json_schema_to_python_type = _safe_j2p
    print("[ResumeRadar] gradio_client bool-schema patch applied ✓")
except Exception as _patch_err:
    print(f"[ResumeRadar] gradio_client patch skipped (may already be fixed): {_patch_err}")
# ─────────────────────────────────────────────────────────────────────────────

import gradio as gr

# ─── Text Extraction ──────────────────────────────────────────────────────────

def extract_text(file_path: str) -> str:
    path = Path(file_path)
    ext = path.suffix.lower()
    data = path.read_bytes()

    if ext == ".pdf":
        return _pdf(data)
    elif ext in (".docx", ".doc"):
        return _docx(data)
    elif ext == ".txt":
        return data.decode("utf-8", errors="ignore").strip()
    raise ValueError(f"Unsupported file type '{ext}'. Upload PDF, DOCX, or TXT.")


def _pdf(data: bytes) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages).strip()
        if text:
            return text
    except Exception:
        pass
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(data))
        text = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
        if text:
            return text
    except Exception:
        pass
    raise ValueError("Could not extract text from PDF. Use a PDF with selectable text.")


def _docx(data: bytes) -> str:
    import docx
    doc = docx.Document(io.BytesIO(data))
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text.strip())
    return "\n".join(parts)


# ─── Startup: detect server-side API keys (set in HF Space Secrets) ──────────
# Read ONCE at module load time — Gradio worker threads on HF Spaces can see a
# different os.environ than the main process, so we cache here and reuse below.
_SERVER_GROQ = (
    os.getenv("GROQ_API_KEY", "")
    or os.getenv("GROQ_KEY", "")
    or ""
).strip()

_SERVER_GEMINI = (
    os.getenv("GEMINI_API_KEY", "")
    or os.getenv("GOOGLE_API_KEY", "")
    or os.getenv("GOOGLE_GEMINI_KEY", "")
    or ""
).strip()

# Startup log (visible in HF Space logs) — helps diagnose secret issues
_groq_status   = f"SET ({_SERVER_GROQ[:4]}...)"   if _SERVER_GROQ   else "NOT SET"
_gemini_status = f"SET ({_SERVER_GEMINI[:4]}...)" if _SERVER_GEMINI else "NOT SET"
print(f"[ResumeRadar] GROQ_API_KEY   : {_groq_status}")
print(f"[ResumeRadar] GEMINI_API_KEY : {_gemini_status}")

# ─── LLM Client ───────────────────────────────────────────────────────────────

# Preferred model order for each provider — first one found on the account wins.
_GROQ_PREFERRED = [
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]
_GEMINI_PREFERRED = [
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
]


def _pick_groq_model(client) -> str:
    """Ask Groq which models this key can actually use, then return the best one."""
    try:
        available = {m.id for m in client.models.list().data}
        # Skip non-chat models (whisper, embeddings, guard)
        chat_models = {m for m in available
                       if not any(x in m for x in ("whisper", "embed", "guard", "tool"))}
        for pref in _GROQ_PREFERRED:
            if pref in chat_models:
                return pref
        # Fall back to whatever chat model exists
        if chat_models:
            return sorted(chat_models)[0]
    except Exception:
        pass
    return _GROQ_PREFERRED[0]   # last resort if models.list() itself fails


def _pick_gemini_model(genai) -> str:
    """Ask Gemini which models this key can generate content with, return the best one."""
    try:
        available = {
            m.name.split("/")[-1]
            for m in genai.list_models()
            if "generateContent" in (m.supported_generation_methods or [])
        }
        for pref in _GEMINI_PREFERRED:
            if pref in available:
                return pref
    except Exception:
        pass
    return _GEMINI_PREFERRED[0]  # last resort


class LLMClient:
    def __init__(self, provider: str, groq_key: str = "", gemini_key: str = ""):
        self.provider = provider

        if provider == "groq":
            from groq import Groq
            if not groq_key:
                raise ValueError(
                    "❌ No Groq API key found.\n\n"
                    "• Enter your key in the 'Groq API Key' field above, OR\n"
                    "• Set GROQ_API_KEY in HF Space Settings → Secrets\n"
                    "• Get a free key at: https://console.groq.com/keys"
                )
            self.client = Groq(api_key=groq_key)
            self.model  = _pick_groq_model(self.client)
            print(f"[ResumeRadar] LLMClient Groq → selected model: {self.model}")

        elif provider == "gemini":
            import google.generativeai as genai
            if not gemini_key:
                raise ValueError(
                    "❌ No Gemini API key found.\n\n"
                    "• Enter your key in the 'Gemini API Key' field above, OR\n"
                    "• Set GEMINI_API_KEY in HF Space Settings → Secrets\n"
                    "• Get a free key at: https://aistudio.google.com/app/apikey"
                )
            genai.configure(api_key=gemini_key)
            self._genai = genai
            self.model  = _pick_gemini_model(genai)
            print(f"[ResumeRadar] LLMClient Gemini → selected model: {self.model}")

        else:
            raise ValueError(f"Unknown provider: {provider}")

    def complete(self, system: str, user: str) -> str:
        if self.provider == "groq":
            # Try the pre-selected model first, then every fallback in order.
            # This survives model deprecations, quota changes, and list() failures.
            models_to_try = [self.model] + [m for m in _GROQ_PREFERRED if m != self.model]
            last_err: Exception = RuntimeError("No models tried")
            for model in models_to_try:
                try:
                    resp = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        temperature=0.1,
                        max_tokens=4096,
                    )
                    self.model = model  # remember which model worked
                    return resp.choices[0].message.content
                except Exception as e:
                    msg = str(e).lower()
                    # Model doesn't exist on this account → try the next one
                    if any(k in msg for k in (
                        "model_not_found", "not_found", "does not exist",
                        "404", "no such model", "invalid model",
                        "model not found", "decommissioned", "deprecated",
                        "not supported", "no longer available",
                    )):
                        last_err = e
                        continue
                    # Auth failure → no point trying other models
                    if any(k in msg for k in (
                        "401", "403", "invalid api key", "unauthorized",
                        "authentication", "invalid_api_key",
                    )):
                        raise ValueError(
                            "❌ Groq API key was rejected.\n\n"
                            "• Double-check the key at https://console.groq.com/keys\n"
                            "• If using HF Secrets, make sure the secret is named "
                            "GROQ_API_KEY (exact spelling, no spaces).\n"
                            f"Raw error: {e}"
                        ) from e
                    # Rate limit / quota
                    if any(k in msg for k in ("429", "rate_limit", "rate limit", "quota")):
                        raise ValueError(
                            "❌ Groq rate limit hit. Wait ~60 seconds and try again, "
                            "or switch to Gemini.\n"
                            f"Raw error: {e}"
                        ) from e
                    # Anything else (network, timeout, …) — fail fast
                    raise
            raise ValueError(
                "❌ All Groq models are currently unavailable.\n\n"
                f"Tried: {', '.join(models_to_try)}\n"
                f"Last error: {last_err}\n\n"
                "• Check https://status.groq.com for outages.\n"
                "• Switch to Gemini as a workaround."
            )

        else:  # gemini
            models_to_try = [self.model] + [m for m in _GEMINI_PREFERRED if m != self.model]
            last_err = RuntimeError("No models tried")
            for model in models_to_try:
                try:
                    client = self._genai.GenerativeModel(model)
                    resp = client.generate_content(
                        f"{system}\n\n{user}",
                        generation_config={"temperature": 0.1, "max_output_tokens": 4096},
                    )
                    self.model = model  # remember which model worked
                    return resp.text
                except Exception as e:
                    msg = str(e).lower()
                    # Model not available → try next
                    if any(k in msg for k in (
                        "not found", "404", "model not found", "invalid model",
                        "does not exist", "deprecated", "not supported",
                        "no longer available",
                    )):
                        last_err = e
                        continue
                    # Auth failure
                    if any(k in msg for k in (
                        "api key not valid", "invalid api key", "permission denied",
                        "401", "403", "unauthenticated",
                    )):
                        raise ValueError(
                            "❌ Gemini API key was rejected.\n\n"
                            "• Double-check the key at https://aistudio.google.com/app/apikey\n"
                            "• If using HF Secrets, make sure the secret is named "
                            "GEMINI_API_KEY (exact spelling, no spaces).\n"
                            f"Raw error: {e}"
                        ) from e
                    # Quota
                    if any(k in msg for k in ("429", "quota", "resource_exhausted", "resource exhausted")):
                        raise ValueError(
                            "❌ Gemini quota exceeded. Wait and try again, "
                            "or switch to Groq.\n"
                            f"Raw error: {e}"
                        ) from e
                    raise
            raise ValueError(
                "❌ All Gemini models are currently unavailable.\n\n"
                f"Tried: {', '.join(models_to_try)}\n"
                f"Last error: {last_err}\n\n"
                "• Check https://status.google.com for outages.\n"
                "• Switch to Groq as a workaround."
            )

    def json(self, system: str, user: str) -> dict:
        raw = self.complete(
            system + "\n\nReturn ONLY valid JSON — no markdown fences, no explanation.",
            user,
        ).strip()

        # Strip markdown code fences
        if raw.startswith("```"):
            m = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
            if m:
                raw = m.group(1).strip()

        # Remove control characters that break JSON parsing
        raw = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", raw)

        try:
            return json.loads(raw, strict=False)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", raw)
            if m:
                try:
                    return json.loads(m.group(), strict=False)
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"LLM returned invalid JSON:\n{raw[:300]}")


# ─── Sentence Transformer (cached) ────────────────────────────────────────────

@lru_cache(maxsize=1)
def get_embedder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")


# ─── Pipeline Steps ───────────────────────────────────────────────────────────

def parse_resume(text: str, llm: LLMClient) -> dict:
    return llm.json(
        "You are an expert resume parser. Extract all information accurately.",
        f"""Parse this resume and return JSON exactly in this format:
{{
  "name": "",
  "email": "",
  "phone": "",
  "summary": "",
  "skills": [{{"name": "Python", "category": "technical", "level": "expert"}}],
  "experiences": [{{"company": "", "role": "", "duration": "", "responsibilities": [], "skills_used": []}}],
  "education": [{{"degree": "", "institution": "", "year": "", "gpa": ""}}],
  "certifications": []
}}

RESUME:
{text[:7000]}""",
    )


def analyze_job(text: str, llm: LLMClient) -> dict:
    return llm.json(
        "You are an expert job description analyst.",
        f"""Analyze this job description and return JSON exactly in this format:
{{
  "title": "",
  "company": "",
  "seniority": "mid",
  "domain": "",
  "required_skills": [],
  "preferred_skills": [],
  "responsibilities": []
}}

JOB DESCRIPTION:
{text[:5000]}""",
    )


def compute_match(resume: dict, job: dict, resume_text: str) -> dict:
    """Semantic skill match with graduated partial-credit scoring."""
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    model = get_embedder()
    text_lower = resume_text.lower()

    # Collect resume skill names
    resume_skills = list({s["name"].lower() for s in resume.get("skills", [])})
    for exp in resume.get("experiences", []):
        resume_skills.extend([s.lower() for s in exp.get("skills_used", [])])
    resume_skills = list(set(resume_skills))

    all_job_skills = job.get("required_skills", []) + job.get("preferred_skills", [])
    if not all_job_skills:
        return {
            "fit_score": 50.0, "ats_score": 50.0,
            "skill_breakdown": [], "gaps": [], "strengths": [],
        }

    job_embs = model.encode(all_job_skills, convert_to_numpy=True)
    res_embs = model.encode(resume_skills, convert_to_numpy=True) if resume_skills else None

    breakdown, gaps = [], []
    total, max_possible = 0.0, 0.0

    for i, skill in enumerate(all_job_skills):
        imp = "required" if skill in job.get("required_skills", []) else "preferred"
        w = 1.5 if imp == "required" else 1.0
        max_possible += w

        exact = skill.lower() in text_lower
        best_sim, best_phrase = 0.0, None

        if res_embs is not None and len(res_embs) > 0:
            sims = cosine_similarity(job_embs[i : i + 1], res_embs)[0]
            idx = int(np.argmax(sims))
            best_sim = float(sims[idx])
            if best_sim >= 0.55:
                best_phrase = resume_skills[idx]

        # Only genuine semantic overlap counts
        semantic_match = best_sim >= 0.55
        in_resume = exact or semantic_match

        # Honest scoring — zero credit below 0.35 (truly unrelated)
        if exact:
            effective_score = 1.0
        elif best_sim >= 0.65:
            effective_score = best_sim                          # strong semantic
        elif best_sim >= 0.50:
            effective_score = 0.35 + (best_sim - 0.50) * 2.0  # clear partial
        elif best_sim >= 0.35:
            effective_score = best_sim * 0.40                  # tangential only
        else:
            effective_score = 0.0                              # no match

        total += effective_score * w

        breakdown.append({
            "skill": skill,
            "in_resume": in_resume,
            "score": round(best_sim, 3),
            "matched_phrase": best_phrase,
            "importance": imp,
        })

        if not in_resume:
            gaps.append({
                "skill": skill, "gap_type": "missing",
                "importance": imp, "suggestion": "",
            })
        elif semantic_match and not exact:
            gaps.append({
                "skill": skill, "gap_type": "present_but_unstated", "importance": imp,
                "suggestion": f"You have '{best_phrase}' — explicitly write '{skill}' to pass ATS filters.",
            })

    raw_score = (total / max_possible) * 100 if max_possible > 0 else 0.0
    # No artificial floor — honest 0 if nothing matches
    fit_score = round(max(0.0, min(100.0, raw_score)), 1)
    ats_hits = sum(1 for s in all_job_skills if s.lower() in text_lower)
    ats_score = (ats_hits / len(all_job_skills)) * 100

    strengths = [b["skill"] for b in breakdown if b["in_resume"] and b["score"] > 0.60][:6]

    return {
        "fit_score": round(fit_score, 1),
        "ats_score": round(ats_score, 1),
        "skill_breakdown": breakdown,
        "gaps": gaps,
        "strengths": strengths,
    }


def rewrite_resume(resume: dict, job: dict, match: dict, llm: LLMClient) -> dict:
    gaps_text = "; ".join(
        f"{g['skill']} ({g['gap_type']})" + (f": {g['suggestion']}" if g.get("suggestion") else "")
        for g in match["gaps"][:8]
    ) or "None identified"

    return llm.json(
        "You are an expert resume writer using the STAR method. Never fabricate skills or experience.",
        f"""Rewrite this resume to maximise match with the job description. Return JSON:
{{"rewritten_text": "full rewritten resume text", "changes": [{{"original": "old text", "improved": "new text", "reason": "why"}}]}}

JOB: {job.get('title','')} | Required: {', '.join(job.get('required_skills',[])[:8])}
GAPS: {gaps_text}
STRENGTHS: {', '.join(match.get('strengths',[]))}

ORIGINAL RESUME:
{resume.get('raw_text','')[:5000]}""",
    )


def write_cover_letter(resume: dict, job: dict, match: dict, tone: str, llm: LLMClient) -> dict:
    exps = resume.get("experiences", [])
    last_role = f"{exps[0]['role']} at {exps[0]['company']}" if exps else "See resume"

    return llm.json(
        "You are an expert cover letter writer. Write specific, memorable letters — not generic ones.",
        f"""Write a tailored cover letter. Return JSON:
{{"cover_letter": "full 280–340 word cover letter", "key_points_addressed": ["point1", "point2", "point3"]}}

CANDIDATE: {resume.get('name','Applicant')} | Last Role: {last_role}
Top Skills: {', '.join(s['name'] for s in resume.get('skills', [])[:7])}
JOB: {job.get('title','')} at {job.get('company','')}
Required: {', '.join(job.get('required_skills',[])[:8])}
Tone: {tone} | Fit Score: {match.get('fit_score', 0)}/100""",
    )


def generate_interview_questions(resume: dict, job: dict, match: dict, llm: LLMClient) -> dict:
    gaps      = [g["skill"] for g in match.get("gaps", []) if g["gap_type"] == "missing"][:4]
    strengths = match.get("strengths", [])[:5]
    exps      = resume.get("experiences", [])
    last_exp  = exps[0] if exps else {}
    last_company = last_exp.get("company", "my previous company")
    last_role    = f"{last_exp.get('role','')} at {last_company}" if last_exp else "previous role"
    top_skills   = ", ".join(s["name"] for s in resume.get("skills", [])[:7])

    return llm.json(
        """You are an expert interview coach. Generate Q&A pairs where answers are:
- Written in FIRST PERSON from the candidate's perspective ("I did...", "I used...")
- Natural and conversational — NOT robotic or generic
- Specific to the candidate's actual skills and experience
- Behavioral answers use STAR format (Situation, Task, Action, Result)
- Technical answers reference the candidate's real tech stack
- Each answer: 60-90 words
Return ONLY valid JSON.""",
        f"""Generate 12 interview Q&A pairs for this candidate.

CANDIDATE:
- Name: {resume.get('name','the candidate')}
- Last Role: {last_role}
- Skills: {top_skills}

JOB: {job.get('title','')} at {job.get('company','')}
Domain: {job.get('domain','')}
Required Skills: {', '.join(job.get('required_skills',[])[:8])}
Fit Score: {match.get('fit_score',0)}/100
Strengths: {', '.join(strengths)}
Gaps to probe: {', '.join(gaps) or 'none critical'}

Return JSON:
{{
  "qa_pairs": [
    {{"question": "...", "answer": "...", "category": "behavioral"}},
    {{"question": "...", "answer": "...", "category": "behavioral"}},
    {{"question": "...", "answer": "...", "category": "behavioral"}},
    {{"question": "...", "answer": "...", "category": "behavioral"}},
    {{"question": "...", "answer": "...", "category": "behavioral"}},
    {{"question": "...", "answer": "...", "category": "technical"}},
    {{"question": "...", "answer": "...", "category": "technical"}},
    {{"question": "...", "answer": "...", "category": "technical"}},
    {{"question": "...", "answer": "...", "category": "technical"}},
    {{"question": "...", "answer": "...", "category": "situational"}},
    {{"question": "...", "answer": "...", "category": "situational"}},
    {{"question": "...", "answer": "...", "category": "situational"}}
  ],
  "tips": ["tip1","tip2","tip3","tip4","tip5"]
}}

CRITICAL: Make answers reference {top_skills} and experience at {last_company}. First-person only.""",
    )


# ─── Resume Template Builder ──────────────────────────────────────────────────

TEMPLATE_STYLES = {
    "Modern Pro": "modern",
    "Executive Classic": "executive",
    "Minimal ATS-Safe": "minimal",
    "Tech Stack": "tech",
}


def build_resume_html(template_id: str, resume: dict, job: dict, rewritten_text: str) -> str:
    name = resume.get("name", "Your Name")
    email = resume.get("email", "")
    phone = resume.get("phone", "")
    summary = resume.get("summary", "")
    skills = [s["name"] for s in resume.get("skills", [])]
    exps = resume.get("experiences", [])
    edus = resume.get("education", [])
    certs = resume.get("certifications", [])
    role = job.get("title", "")
    contact = " · ".join(filter(None, [email, phone]))

    exp_html = "".join(
        f"""<div style="margin-bottom:12px">
          <div style="display:flex;justify-content:space-between">
            <strong>{e.get('role','')}</strong>
            <span style="font-size:11px;color:#94a3b8">{e.get('duration','')}</span>
          </div>
          <div style="color:#6366f1;font-size:12px">{e.get('company','')}</div>
          <ul style="padding-left:16px;color:#475569;line-height:1.7">
            {"".join(f'<li>{r}</li>' for r in e.get('responsibilities', []))}
          </ul>
        </div>"""
        for e in exps
    )

    edu_html = "".join(
        f"""<div style="margin-bottom:8px">
          <strong>{e.get('degree','')}</strong> — {e.get('institution','')}
          {f"<span style='font-size:11px;color:#94a3b8'> {e.get('year','')}</span>" if e.get('year') else ""}
        </div>"""
        for e in edus
    )

    skill_badges = "".join(
        f'<span style="display:inline-block;background:#6366f120;border:1px solid #6366f140;'
        f'border-radius:4px;padding:2px 9px;margin:2px;font-size:11px;color:#818cf8">{s}</span>'
        for s in skills
    )

    cert_html = (
        f'<section><h2>Certifications</h2><ul>{"".join(f"<li>{c}</li>" for c in certs)}</ul></section>'
        if certs else ""
    )

    templates = {
        "modern": f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0 }}
  body {{ font-family:'Segoe UI',Arial,sans-serif; font-size:13px; color:#1e293b }}
  .wrap {{ display:flex; min-height:100vh }}
  .sidebar {{ width:220px; background:#6366f1; color:white; padding:28px 18px; flex-shrink:0 }}
  .sidebar h1 {{ font-size:20px; font-weight:700; margin-bottom:4px }}
  .sidebar .role {{ font-size:11px; opacity:.8; margin-bottom:20px }}
  .sidebar .contact {{ font-size:11px; opacity:.85; line-height:1.8; margin-bottom:20px }}
  .sidebar h3 {{ font-size:9px; letter-spacing:1.5px; text-transform:uppercase; opacity:.6;
    margin:18px 0 8px; border-top:1px solid rgba(255,255,255,.2); padding-top:10px }}
  .main {{ flex:1; padding:28px }}
  .main h2 {{ font-size:10px; letter-spacing:2px; text-transform:uppercase; color:#6366f1;
    border-bottom:2px solid #6366f1; padding-bottom:4px; margin:22px 0 12px }}
  .main h2:first-child {{ margin-top:0 }}
  ul {{ padding-left:16px; color:#475569; line-height:1.7 }}
</style></head><body>
<div class="wrap">
  <div class="sidebar">
    <h1>{name}</h1>
    <div class="role">{role}</div>
    <div class="contact">{email}<br/>{phone}</div>
    <h3>Skills</h3>
    <div>{"".join(f'<span style="display:inline-block;background:rgba(255,255,255,.15);border-radius:3px;padding:2px 7px;margin:2px;font-size:10px">{s}</span>' for s in skills)}</div>
    {f'<h3>Certifications</h3><ul style="font-size:11px;opacity:.85">{"".join(f"<li>{c}</li>" for c in certs)}</ul>' if certs else ""}
  </div>
  <div class="main">
    {f'<h2>Profile</h2><p style="color:#475569;line-height:1.65">{summary}</p>' if summary else ""}
    {f'<h2>Experience</h2>{exp_html}' if exps else ""}
    {f'<h2>Education</h2>{edu_html}' if edus else ""}
  </div>
</div></body></html>""",

        "executive": f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0 }}
  body {{ font-family:Georgia,'Times New Roman',serif; font-size:13px; color:#111827;
    max-width:800px; margin:0 auto; padding:48px 52px }}
  .header {{ text-align:center; margin-bottom:28px; padding-bottom:20px;
    border-bottom:2.5px double #1e293b }}
  .header h1 {{ font-size:28px; letter-spacing:4px; text-transform:uppercase; font-weight:700 }}
  .header .role {{ font-size:12px; letter-spacing:2px; color:#6b7280; margin:4px 0 8px }}
  .header .contact {{ font-size:11px; color:#6b7280 }}
  h2 {{ font-size:11px; letter-spacing:3px; text-transform:uppercase;
    border-bottom:1px solid #1e293b; padding-bottom:4px; margin:24px 0 12px }}
  .exp-header {{ display:flex; justify-content:space-between }}
  ul {{ padding-left:18px; color:#4b5563; line-height:1.75 }}
  .skill-badge {{ display:inline-block; border:1px solid #d1d5db; border-radius:3px;
    padding:1px 8px; margin:2px; font-size:11px; font-family:'Segoe UI',sans-serif }}
</style></head><body>
<div class="header">
  <h1>{name}</h1>
  <div class="role">{role}</div>
  <div class="contact">{contact}</div>
</div>
{f'<h2>Executive Profile</h2><p style="font-style:italic;color:#374151;line-height:1.7">{summary}</p>' if summary else ""}
{f'<h2>Professional Experience</h2>{exp_html}' if exps else ""}
{f'<h2>Education</h2>{edu_html}' if edus else ""}
{f'<h2>Core Competencies</h2><div style="margin-top:8px">{skill_badges}</div>' if skills else ""}
{cert_html}
</body></html>""",

        "minimal": f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0 }}
  body {{ font-family:Arial,Helvetica,sans-serif; font-size:12px; color:#111;
    max-width:760px; margin:0 auto; padding:42px 48px }}
  h1 {{ font-size:22px; font-weight:700; margin-bottom:2px }}
  .contact {{ font-size:11px; color:#555; margin-bottom:28px }}
  h2 {{ font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px;
    border-bottom:1px solid #999; padding-bottom:3px; margin:22px 0 10px }}
  .exp-item {{ margin-bottom:12px }}
  .exp-header {{ display:flex; justify-content:space-between }}
  ul {{ padding-left:16px; color:#333; line-height:1.75 }}
  .skills {{ display:flex; flex-wrap:wrap; gap:4px }}
  .skills span {{ border:1px solid #ccc; border-radius:3px; padding:1px 7px; font-size:11px }}
</style></head><body>
<h1>{name}</h1>
<div class="contact">{contact}{(" · " + role) if role else ""}</div>
{f'<h2>Summary</h2><p style="color:#333;line-height:1.65">{summary}</p>' if summary else ""}
{f'<h2>Experience</h2>{exp_html}' if exps else ""}
{f'<h2>Education</h2>{edu_html}' if edus else ""}
{f'<h2>Skills</h2><div class="skills">{"".join(f"<span>{s}</span>" for s in skills)}</div>' if skills else ""}
{cert_html}
</body></html>""",

        "tech": f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0 }}
  body {{ font-family:'Consolas','Courier New',monospace; font-size:12px; color:#1e293b }}
  .header {{ background:#0f172a; color:#e2e8f0; padding:24px 32px }}
  .header h1 {{ font-size:24px; font-weight:700; color:#38bdf8; letter-spacing:2px }}
  .header .meta {{ font-size:11px; color:#94a3b8; margin-top:4px }}
  .body {{ padding:28px 32px }}
  h2 {{ font-size:11px; color:#0f172a; background:#e2e8f0; padding:4px 10px;
    margin:20px 0 10px; border-left:4px solid #38bdf8;
    font-family:'Segoe UI',sans-serif; letter-spacing:1px; text-transform:uppercase }}
  ul {{ padding-left:16px; color:#475569; line-height:1.75; font-family:'Segoe UI',sans-serif }}
  .skill-badge {{ display:inline-block; background:#0f172a; color:#38bdf8;
    border-radius:4px; padding:2px 9px; margin:2px; font-size:11px }}
</style></head><body>
<div class="header">
  <h1>{name}</h1>
  <div class="meta">{("// " + role + " · ") if role else ""}{contact}</div>
</div>
<div class="body">
  {f'<h2>// Profile</h2><p style="font-family:Segoe UI,sans-serif;color:#475569;line-height:1.65">{summary}</p>' if summary else ""}
  {f'<h2>// Tech Stack</h2><div style="margin-top:6px">{skill_badges}</div>' if skills else ""}
  {f'<h2>// Experience</h2>{exp_html}' if exps else ""}
  {f'<h2>// Education</h2>{edu_html}' if edus else ""}
  {cert_html}
</div></body></html>""",
    }

    return templates.get(template_id, templates["modern"])


def save_html_template(html: str, candidate_name: str) -> str:
    fname = f"{(candidate_name or 'resume').replace(' ', '_')}_resume.html"
    out_path = Path(tempfile.gettempdir()) / fname
    out_path.write_text(html, encoding="utf-8")
    return str(out_path)


# ─── Multi-format Resume Export ───────────────────────────────────────────────

def build_resume_docx(resume: dict, job: dict, rewritten_text: str) -> bytes:
    """Build a professionally formatted DOCX and return raw bytes."""
    import io
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    for sec in doc.sections:
        sec.top_margin    = Inches(0.75)
        sec.bottom_margin = Inches(0.75)
        sec.left_margin   = Inches(1.0)
        sec.right_margin  = Inches(1.0)

    name    = resume.get("name", "Your Name")
    email   = resume.get("email", "")
    phone   = resume.get("phone", "")
    role    = job.get("title", "")
    summary = resume.get("summary", "")
    skills  = [s["name"] if isinstance(s, dict) else str(s) for s in resume.get("skills", [])]
    exps    = resume.get("experiences", [])
    edus    = resume.get("education", [])
    certs   = resume.get("certifications", [])

    # Name
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(name)
    r.bold = True
    r.font.size = Pt(22)
    r.font.color.rgb = RGBColor(0x1e, 0x29, 0x3b)

    # Role + Contact line
    contact_parts = [x for x in [role, email, phone] if x]
    if contact_parts:
        p2 = doc.add_paragraph(" · ".join(contact_parts))
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if p2.runs:
            p2.runs[0].font.size = Pt(10)
            p2.runs[0].font.color.rgb = RGBColor(0x6b, 0x72, 0x80)

    def add_section(title: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after  = Pt(4)
        r = p.add_run(title.upper())
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0x63, 0x66, 0xf1)

    if summary:
        add_section("Summary")
        doc.add_paragraph(summary)

    if exps:
        add_section("Experience")
        for e in exps:
            p = doc.add_paragraph()
            r = p.add_run(e.get("role", ""))
            r.bold = True
            r.font.size = Pt(11)
            if e.get("company"):
                p.add_run(f"  —  {e['company']}")
            if e.get("duration"):
                dr = p.add_run(f"  ({e['duration']})")
                dr.font.size = Pt(10)
                dr.font.color.rgb = RGBColor(0x6b, 0x72, 0x80)
            for resp in e.get("responsibilities", []):
                bp = doc.add_paragraph(resp, style="List Bullet")
                bp.paragraph_format.left_indent = Inches(0.2)
                bp.paragraph_format.space_after  = Pt(2)

    if edus:
        add_section("Education")
        for e in edus:
            p = doc.add_paragraph()
            r = p.add_run(e.get("degree", ""))
            r.bold = True
            if e.get("institution"):
                p.add_run(f"  —  {e['institution']}")
            if e.get("year"):
                yr = p.add_run(f"  ({e['year']})")
                yr.font.size = Pt(10)
                yr.font.color.rgb = RGBColor(0x6b, 0x72, 0x80)

    if skills:
        add_section("Skills")
        doc.add_paragraph(", ".join(skills))

    if certs:
        add_section("Certifications")
        for c in certs:
            doc.add_paragraph(f"• {c}")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def build_resume_txt(resume: dict, job: dict, rewritten_text: str) -> str:
    """Return a clean plain-text resume — uses AI-rewritten text when available."""
    if rewritten_text and len(rewritten_text) > 100:
        return rewritten_text   # AI version is already polished plain text

    # Fallback: build from structured dict
    name    = resume.get("name", "")
    email   = resume.get("email", "")
    phone   = resume.get("phone", "")
    role    = job.get("title", "")
    summary = resume.get("summary", "")
    skills  = [s["name"] if isinstance(s, dict) else str(s) for s in resume.get("skills", [])]
    exps    = resume.get("experiences", [])
    edus    = resume.get("education", [])
    certs   = resume.get("certifications", [])

    lines = [name]
    contact = " · ".join(filter(None, [role, email, phone]))
    if contact:
        lines.append(contact)
    lines.append("=" * 60)

    if summary:
        lines += ["", "SUMMARY", "-" * 30, summary]
    if exps:
        lines += ["", "EXPERIENCE", "-" * 30]
        for e in exps:
            lines.append(f"\n{e.get('role','')} — {e.get('company','')} ({e.get('duration','')})")
            for r in e.get("responsibilities", []):
                lines.append(f"  • {r}")
    if edus:
        lines += ["", "EDUCATION", "-" * 30]
        for e in edus:
            lines.append(f"  {e.get('degree','')} — {e.get('institution','')} {e.get('year','')}")
    if skills:
        lines += ["", "SKILLS", "-" * 30, ", ".join(skills)]
    if certs:
        lines += ["", "CERTIFICATIONS", "-" * 30]
        for c in certs:
            lines.append(f"  • {c}")

    return "\n".join(lines)


def save_resume_file(
    resume: dict,
    job: dict,
    rewritten_text: str,
    template_choice: str,
    dl_format: str,
) -> str:
    """Build & save the resume in the requested format; return the file path."""
    safe_name = (resume.get("name") or "resume").replace(" ", "_")
    tmp = Path(tempfile.gettempdir())

    if dl_format == "DOCX":
        data = build_resume_docx(resume, job, rewritten_text)
        path = tmp / f"{safe_name}_resume.docx"
        path.write_bytes(data)
    elif dl_format == "TXT":
        data = build_resume_txt(resume, job, rewritten_text)
        path = tmp / f"{safe_name}_resume.txt"
        path.write_text(data, encoding="utf-8")
    else:  # HTML (default)
        template_id = TEMPLATE_STYLES.get(template_choice, "modern")
        data = build_resume_html(template_id, resume, job, rewritten_text)
        path = tmp / f"{safe_name}_resume.html"
        path.write_text(data, encoding="utf-8")

    return str(path)


# ─── Main Gradio Handler ───────────────────────────────────────────────────────

def run_analysis(
    resume_file,
    job_description: str,
    provider: str,
    groq_key: str,
    gemini_key: str,
    tone: str,
    template_choice: str,
    dl_format: str = "HTML",
):
    try:
        t0 = time.time()

        # ── Key resolution ────────────────────────────────────────────────────
        # Gradio 5.x returns None for hidden components — guard with (x or "").
        # _SERVER_GROQ / _SERVER_GEMINI are read ONCE at module load time and
        # stored as module-level strings.  We reuse them here instead of calling
        # os.getenv() again, because Gradio worker threads on HF Spaces can see
        # a different environment than the main process.
        groq_key_clean   = (groq_key   or "").strip()
        gemini_key_clean = (gemini_key or "").strip()

        # User key overrides server key; server key (module-level cached) is fallback
        resolved_groq   = groq_key_clean   or _SERVER_GROQ
        resolved_gemini = gemini_key_clean or _SERVER_GEMINI

        # Log key resolution result (visible in HF Space logs → helps diagnose issues)
        print(f"[ResumeRadar] run_analysis provider={provider!r} "
              f"groq={'user' if groq_key_clean else ('server' if _SERVER_GROQ else 'NONE')} "
              f"gemini={'user' if gemini_key_clean else ('server' if _SERVER_GEMINI else 'NONE')}")

        # ── Input validation ──────────────────────────────────────────────────
        if not resume_file:
            return "❌ Please upload a resume file.", "", "", "", "", "", "", None
        if not job_description or len(job_description.strip()) < 20:
            return "❌ Please paste the full job description (at least 20 chars).", "", "", "", "", "", "", None
        if provider == "Groq" and not resolved_groq:
            return (
                "❌ No Groq API key found.\n\n"
                "**Option A** — Enter your key in the 'Groq API Key' field above.\n"
                "**Option B** — Get a free key at https://console.groq.com/keys\n"
                "(Space owners: set GROQ_API_KEY in HF Space Secrets.)",
                "", "", "", "", "", "", None,
            )
        if provider == "Gemini" and not resolved_gemini:
            return (
                "❌ No Gemini API key found.\n\n"
                "**Option A** — Enter your key in the 'Gemini API Key' field above.\n"
                "**Option B** — Get a free key at https://aistudio.google.com/app/apikey\n"
                "(Space owners: set GEMINI_API_KEY in HF Space Secrets.)",
                "", "", "", "", "", "", None,
            )

        prov = "groq" if provider == "Groq" else "gemini"
        llm  = LLMClient(prov, resolved_groq, resolved_gemini)

        # ── Step 1: Extract ──
        # Normalise file reference across all Gradio versions:
        #   Gradio 5.x  → str path  (most common)
        #   Gradio 5.x  → FileData object with .path attribute
        #   Gradio 4.x  → object with .name attribute (legacy)
        #   Gradio 4.x  → dict with "path" or "name" key
        if resume_file is None:
            return "❌ Please upload a resume file.", "", "", "", "", "", "", None
        if isinstance(resume_file, str):
            file_path = resume_file
        elif hasattr(resume_file, "path"):          # Gradio 5.x FileData
            file_path = resume_file.path
        elif hasattr(resume_file, "name"):          # Gradio 4.x TempFile
            file_path = resume_file.name
        elif isinstance(resume_file, dict):
            file_path = resume_file.get("path") or resume_file.get("name") or ""
        else:
            file_path = str(resume_file)

        if not file_path:
            return "❌ Could not read the uploaded file path. Try uploading again.", "", "", "", "", "", "", None

        resume_text = extract_text(file_path)

        # ── Step 2: Parse & analyse ──
        resume_data = parse_resume(resume_text, llm)
        resume_data["raw_text"] = resume_text
        job_data = analyze_job(job_description, llm)

        # ── Step 3: Semantic match ──
        match = compute_match(resume_data, job_data, resume_text)

        # ── Step 4: Rewrite ──
        rewrite = rewrite_resume(resume_data, job_data, match, llm)

        # ── Step 4b: Cover letter (isolated try-except so a failure here doesn't
        #             wipe out all the other outputs) ──
        cover_text = ""
        try:
            cover = write_cover_letter(resume_data, job_data, match, tone.lower(), llm)
            # LLMs sometimes use different key names — try them all
            cover_text = (
                cover.get("cover_letter")
                or cover.get("letter")
                or cover.get("cover letter")
                or cover.get("Cover Letter")
                or cover.get("content")
                or cover.get("text")
                or ""
            )
            # Last resort: pick the longest string value in the dict
            if not cover_text:
                long_vals = sorted(
                    [v for v in cover.values() if isinstance(v, str) and len(v) > 80],
                    key=len, reverse=True,
                )
                cover_text = long_vals[0] if long_vals else ""
            print(f"[ResumeRadar] Cover letter length: {len(cover_text)} chars")
        except Exception as cl_err:
            print(f"[ResumeRadar] Cover letter generation error: {cl_err}")
            cover_text = (
                "⚠️ Cover letter generation encountered an error. "
                "The rest of your analysis is complete above.\n\n"
                f"Error detail: {cl_err}"
            )

        # ── Step 5: Interview prep ──
        _IV_FALLBACK = {
            "qa_pairs": [
                {"question": "Tell me about yourself and why you're interested in this role.",
                 "answer": "I have a strong background in the required skills and I'm excited about this opportunity because it aligns with my career goals. I bring hands-on experience, a problem-solving mindset, and a track record of delivering results.",
                 "category": "behavioral"},
                {"question": "Walk me through a challenging project you've worked on.",
                 "answer": "In my previous role, I was assigned a high-priority project with a tight deadline. I broke it into milestones, coordinated with the team daily, and used my technical skills to automate bottlenecks. We delivered on time and the solution was adopted company-wide.",
                 "category": "behavioral"},
                {"question": "Describe a time you had to learn a new technology quickly.",
                 "answer": "When our team adopted a new framework mid-project, I spent a weekend doing deep-dive tutorials and built a small prototype. Within a week I was contributing features and later ran a knowledge-sharing session for my teammates.",
                 "category": "behavioral"},
                {"question": "How do you handle tight deadlines and competing priorities?",
                 "answer": "I prioritise ruthlessly using impact vs. effort. I communicate early when timelines are at risk, break work into the smallest deliverable units, and use time-boxed sprints to stay on track without sacrificing quality.",
                 "category": "situational"},
                {"question": "Describe a situation where you disagreed with your manager.",
                 "answer": "I respectfully raised my concern with data to back it up, listened to understand their perspective, and we reached a compromise that incorporated the best of both ideas. The outcome was better than either original plan.",
                 "category": "situational"},
                {"question": "Walk me through your technical approach to a recent project.",
                 "answer": "I start by clarifying requirements and constraints, then design the architecture on paper before writing a line of code. I favour modular, testable components, do code reviews, and document decisions so the team can maintain the system long-term.",
                 "category": "technical"},
                {"question": "How do you ensure the quality of your code?",
                 "answer": "I write unit and integration tests alongside the code, not after. I use linting and static analysis tools, review PRs thoroughly, and regularly refactor to keep the codebase clean and readable.",
                 "category": "technical"},
            ],
            "tips": [
                "Use the STAR method (Situation, Task, Action, Result) for every behavioural answer.",
                "Research the company before the interview — mention one specific product or initiative.",
                "Mirror keywords from the job description in your answers.",
                "Prepare 3 smart questions to ask the interviewer at the end.",
                "Practice your answers out loud — fluency matters as much as content.",
            ],
        }
        try:
            interview = generate_interview_questions(resume_data, job_data, match, llm)
            # Validate the response has usable content; fall back if not
            _test_qa = interview.get("qa_pairs", [])
            if not _test_qa:
                # Try alternate key names the LLM sometimes uses
                for _alt in ("questions", "interview_questions", "q_and_a", "qa"):
                    _test_qa = interview.get(_alt, [])
                    if _test_qa:
                        interview["qa_pairs"] = _test_qa
                        break
            if not _test_qa:
                print("[ResumeRadar] Interview: no qa_pairs found — using fallback")
                interview = _IV_FALLBACK
            else:
                # Normalise category field — some LLMs use capital letters or synonyms
                _cat_map = {
                    "behaviour": "behavioral", "behaviour al": "behavioral",
                    "behavioral": "behavioral", "behavioural": "behavioral",
                    "technical": "technical", "tech": "technical",
                    "situational": "situational", "scenario": "situational",
                    "situation": "situational",
                }
                for _qa in interview.get("qa_pairs", []):
                    raw_cat = str(_qa.get("category", "behavioral")).lower().strip()
                    _qa["category"] = _cat_map.get(raw_cat, raw_cat)
            print(f"[ResumeRadar] Interview: {len(interview.get('qa_pairs',[]))} Q&As")
        except Exception as iv_err:
            print(f"[ResumeRadar] Interview generation error: {iv_err}")
            interview = _IV_FALLBACK

        # ── Step 6: Template download ──
        rewritten_text = rewrite.get("rewritten_text", resume_text)
        dl_path = save_resume_file(resume_data, job_data, rewritten_text, template_choice, dl_format)

        elapsed = round(time.time() - t0, 1)
        score_icon = "🟢" if match["fit_score"] >= 75 else ("🟡" if match["fit_score"] >= 50 else "🔴")

        # ── Format outputs ──

        # Score
        matched  = [s for s in match["skill_breakdown"] if s["in_resume"]]
        missing  = [g for g in match["gaps"] if g["gap_type"] == "missing" and g["importance"] == "required"]
        unstated = [g for g in match["gaps"] if g["gap_type"] == "present_but_unstated"]

        score_md = f"""## {score_icon} Fit Score: **{match['fit_score']}/100**

| Metric | Value |
|--------|-------|
| ATS Keyword Score | {match['ats_score']:.0f}% |
| Skills Matched | {len(matched)} / {len(match['skill_breakdown'])} |
| Critical Gaps | {len(missing)} |
| Easy Wins (unstated) | {len(unstated)} |
| Provider | {prov.title()} |
| Analysis Time | {elapsed}s |

### ✨ Strengths
{', '.join(match.get('strengths', [])) or 'See skill breakdown below'}
"""

        # Skills
        lines = ["| Skill | Status | Importance | Semantic Score |",
                 "|-------|--------|------------|----------------|"]
        for s in match["skill_breakdown"]:
            icon = "✅" if s["in_resume"] else "❌"
            lines.append(f"| {s['skill']} | {icon} | {s['importance']} | {s['score']:.0%} |")
        skills_md = "\n".join(lines)

        # Gaps
        gap_lines = ["## Gap Analysis\n"]
        if missing:
            gap_lines.append("### 🔴 Critical Missing Skills (Required)")
            for g in missing:
                gap_lines.append(f"- **{g['skill']}**")
        if unstated:
            gap_lines.append("\n### 🟡 Easy Wins — You Have These, Just Not Written")
            for g in unstated:
                gap_lines.append(f"- **{g['skill']}**: {g.get('suggestion', '')}")
        if not missing and not unstated:
            gap_lines.append("✅ No critical gaps detected! Great match.")
        gaps_md = "\n".join(gap_lines)

        # Changes
        changes = rewrite.get("changes", [])
        change_lines = [f"## {len(changes)} Improvements Made\n"]
        for idx, ch in enumerate(changes[:10], 1):
            change_lines.append(f"**{idx}. Before:** {ch.get('original', '')}")
            change_lines.append(f"**After:** {ch.get('improved', '')}")
            change_lines.append(f"_Reason: {ch.get('reason', '')}_\n")
        changes_md = "\n".join(change_lines)

        # Interview prep — Q&A format with answers
        # Handle both new {qa_pairs:[...]} and old {behavioral:[...]} LLM formats
        raw_qa = interview.get("qa_pairs", [])
        if not raw_qa:
            # Convert old format → new format if LLM returned it
            for cat in ["behavioral", "technical", "situational"]:
                for q in interview.get(cat, []):
                    if isinstance(q, str):
                        raw_qa.append({"question": q, "answer": "", "category": cat})
                    elif isinstance(q, dict):
                        q.setdefault("category", cat)
                        raw_qa.append(q)

        iv_tips = interview.get("tips", [])

        CATEGORY_ORDER = ["behavioral", "technical", "situational"]
        CATEGORY_ICONS = {"behavioral": "🗣", "technical": "⚙️", "situational": "🎯"}

        iv_lines = []
        global_q = 1
        for cat in CATEGORY_ORDER:
            cat_qs = [qa for qa in raw_qa if qa.get("category") == cat]
            if not cat_qs:
                continue
            iv_lines.append(f"\n## {CATEGORY_ICONS.get(cat, '')} {cat.title()} Questions\n")
            for qa in cat_qs:
                iv_lines.append(f"**Q{global_q}: {qa.get('question', '')}**\n")
                ans = qa.get("answer", "").strip()
                if ans:
                    iv_lines.append(f"> 💬 *Sample Answer:* {ans}\n")
                global_q += 1

        if iv_tips:
            iv_lines.append("\n---\n## 💡 Interview Tips\n")
            for tip in iv_tips:
                iv_lines.append(f"- {tip}")

        interview_md = "\n".join(iv_lines) if iv_lines else "No interview questions generated."

        # cover_text was already extracted in the isolated try-except above (Step 4b)
        # Do NOT re-assign here — the multi-key extraction there is the source of truth.

        return (
            score_md,
            skills_md,
            gaps_md,
            rewritten_text,
            cover_text,
            changes_md,
            interview_md,
            dl_path,
            # ── Cached state for reactive template/format switching ──
            resume_data,
            job_data,
            rewritten_text,
        )

    except Exception as e:
        import traceback
        err = str(e)
        # Full traceback goes to HF Space logs — visible in Settings → Logs tab
        print(f"[ResumeRadar] ERROR in run_analysis:\n{traceback.format_exc()}")
        return f"❌ Error: {err}", "", "", "", "", "", "", None, None, None, ""


# ─── Reactive download regeneration (no LLM call) ────────────────────────────

def regenerate_download(
    cached_resume, cached_job, cached_rewrite,
    template_choice: str, dl_format: str
):
    """Rebuild the download file instantly when template or format changes.
    Requires a prior analysis run to have populated the cached state values."""
    if not cached_resume:
        return None   # no analysis run yet — nothing to regenerate
    try:
        path = save_resume_file(
            cached_resume,
            cached_job or {},
            cached_rewrite or "",
            template_choice,
            dl_format,
        )
        print(f"[ResumeRadar] Regenerated download: {dl_format} / {template_choice} → {path}")
        return path
    except Exception as e:
        print(f"[ResumeRadar] regenerate_download error: {e}")
        return None


# ─── Gradio UI ────────────────────────────────────────────────────────────────

HEADER_HTML = """
<div id="rr-header" style="padding:44px 8px 22px;text-align:center;font-family:'Inter',system-ui,sans-serif;position:relative;z-index:2">

  <!-- Live badge -->
  <div style="display:inline-flex;align-items:center;gap:9px;padding:6px 18px;
    border-radius:999px;border:1px solid rgba(99,102,241,0.35);
    background:rgba(99,102,241,0.10);color:#818cf8;
    font-size:0.72rem;font-weight:600;letter-spacing:0.07em;text-transform:uppercase;
    margin-bottom:22px">
    <span style="width:7px;height:7px;border-radius:50%;background:#06b6d4;display:inline-block;
      box-shadow:0 0 8px rgba(6,182,212,0.8);animation:rrPulse 2.5s ease-in-out infinite"></span>
    AI-Powered &nbsp;·&nbsp; Semantic Matching &nbsp;·&nbsp; ATS Optimization
  </div>

  <!-- Title -->
  <h1 style="font-size:clamp(2.4rem,5vw,3.6rem);font-weight:900;line-height:1.05;
    margin:0 0 14px;letter-spacing:-0.03em;font-family:'Inter',system-ui,sans-serif">
    <span style="color:#f1f5f9">Resume</span><span style="
      background:linear-gradient(135deg,#818cf8 0%,#06b6d4 52%,#a78bfa 100%);
      -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text">Radar</span>
  </h1>

  <!-- Subtitle -->
  <div style="color:#64748b;font-size:0.975rem;line-height:1.7;
    font-family:'Inter',system-ui,sans-serif;
    text-align:center;display:block;width:100%;
    padding:0 12%;margin-bottom:22px;box-sizing:border-box">
    Upload your resume &amp; paste a job description —
    <span style="color:#cbd5e1;font-weight:500">get fit score, skill gaps, ATS-optimized rewrite,
    tailored cover letter &amp; interview prep</span> in ~30 seconds.
  </div>

  <!-- Feature pills -->
  <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:8px;margin-bottom:16px">
    <span style="padding:5px 13px;border-radius:999px;background:rgba(99,102,241,0.14);border:1px solid rgba(99,102,241,0.30);color:#818cf8;font-size:0.73rem;font-weight:500">📊 Fit Score</span>
    <span style="padding:5px 13px;border-radius:999px;background:rgba(6,182,212,0.12);border:1px solid rgba(6,182,212,0.30);color:#67e8f9;font-size:0.73rem;font-weight:500">🎯 Skill Gaps</span>
    <span style="padding:5px 13px;border-radius:999px;background:rgba(167,139,250,0.12);border:1px solid rgba(167,139,250,0.30);color:#c4b5fd;font-size:0.73rem;font-weight:500">✍️ Resume Rewrite</span>
    <span style="padding:5px 13px;border-radius:999px;background:rgba(34,197,94,0.12);border:1px solid rgba(34,197,94,0.30);color:#4ade80;font-size:0.73rem;font-weight:500">📝 Cover Letter</span>
    <span style="padding:5px 13px;border-radius:999px;background:rgba(245,158,11,0.12);border:1px solid rgba(245,158,11,0.30);color:#fbbf24;font-size:0.73rem;font-weight:500">🎤 Interview Prep</span>
    <span style="padding:5px 13px;border-radius:999px;background:rgba(239,68,68,0.10);border:1px solid rgba(239,68,68,0.25);color:#f87171;font-size:0.73rem;font-weight:500">📥 Templates</span>
  </div>

  <!-- Free-key hint -->
  <div style="color:#1e293b;font-size:0.73rem;margin:0;
    font-family:'Inter',system-ui,sans-serif;
    text-align:center;display:block;width:100%;box-sizing:border-box">
    Free tier:
    <a href="https://console.groq.com/keys" target="_blank" style="color:#4f46e5;text-decoration:none;font-weight:500">Groq</a> 14,400 req/day &nbsp;·&nbsp;
    <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#4f46e5;text-decoration:none;font-weight:500">Gemini</a> 1,500 req/day &nbsp;·&nbsp;
    Keys used only during your session, never stored.
  </div>
</div>
"""

FOOTER_HTML = """
<div style="text-align:center;padding:20px 16px 12px;border-top:1px solid rgba(255,255,255,0.06);
  font-family:'Inter',system-ui,sans-serif;color:#1e293b;font-size:0.73rem;margin-top:8px">
  <span style="color:#334155;font-weight:600">ResumeRadar</span>
  &nbsp;·&nbsp; Sentence-Transformers + Gradio &nbsp;·&nbsp; MIT License
</div>
"""

CUSTOM_CSS = """
/* ═══════════════════════════════════════════════════════════════════════════
   ResumeRadar — Premium Dark UI  (Gradio 5.x)
   Matches the local Next.js design: fog, glass cards, neon button, Inter font
   ═══════════════════════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Theme CSS vars (override Gradio Soft) ── */
:root {
  --body-background-fill:   #04040f;
  --block-background-fill:  rgba(10,10,30,0.55);
  --block-border-color:     rgba(255,255,255,0.07);
  --input-background-fill:  rgba(255,255,255,0.04);
  --input-border-color:     rgba(255,255,255,0.10);
  --color-accent:           #6366f1;
  --button-primary-background-fill:       linear-gradient(135deg,#6366f1,#4f46e5);
  --button-primary-background-fill-hover: linear-gradient(135deg,#818cf8,#6366f1);
  --button-primary-text-color:            #ffffff;
  --button-secondary-background-fill:     rgba(255,255,255,0.04);
  --button-secondary-border-color:        rgba(255,255,255,0.10);
}

/* ── Base ── */
html, body {
  background: #04040f !important;
  font-family: 'Inter', system-ui, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  color: #e2e8f0;
  overflow-x: hidden;
}

/* ── Animated fog background (4 radial blobs, slow drift + hue cycle) ── */
body::before {
  content: "";
  position: fixed; inset: 0;
  pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 65% 50% at 8%  5%,  rgba(99,102,241,0.18) 0%, transparent 60%),
    radial-gradient(ellipse 55% 45% at 88% 85%, rgba(6,182,212,0.14)  0%, transparent 55%),
    radial-gradient(ellipse 45% 55% at 50% 52%, rgba(167,139,250,0.09) 0%, transparent 70%),
    radial-gradient(ellipse 35% 30% at 18% 82%, rgba(56,189,248,0.07)  0%, transparent 60%);
  animation: fogDrift 14s ease-in-out infinite alternate;
}
@keyframes fogDrift {
  0%   { opacity:.75; transform:scale(1.00) translate(0px,  0px);  filter:hue-rotate(0deg)   }
  25%  { opacity:1.00; transform:scale(1.04) translate(14px,-9px); filter:hue-rotate(18deg)  }
  50%  { opacity:.85; transform:scale(0.97) translate(-9px, 7px);  filter:hue-rotate(-12deg) }
  75%  { opacity:.95; transform:scale(1.02) translate(8px, 11px);  filter:hue-rotate(10deg)  }
  100% { opacity:.80; transform:scale(1.01) translate(-5px,-5px);  filter:hue-rotate(-6deg)  }
}

/* ── Dot-grid texture ── */
body::after {
  content: "";
  position: fixed; inset: 0;
  pointer-events: none; z-index: 0;
  background-image: radial-gradient(circle, rgba(255,255,255,0.025) 1px, transparent 1px);
  background-size: 30px 30px;
}

/* ── Container ── */
.gradio-container {
  background: transparent !important;
  max-width: 1200px !important;
  margin: 0 auto !important;
  position: relative; z-index: 1;
  padding: 0 12px 36px !important;
}
.contain, .gap, .form { background: transparent !important; }

/* Hide "Built with Gradio" footer */
footer { display: none !important; }

/* ── Glass card blocks ── */
.block {
  background: rgba(10,10,30,0.55) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 18px !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.05) !important;
  transition: border-color 0.3s, box-shadow 0.3s !important;
}
.block:hover {
  border-color: rgba(99,102,241,0.18) !important;
  box-shadow: 0 4px 32px rgba(0,0,0,0.40), 0 0 0 1px rgba(99,102,241,0.10),
              inset 0 1px 0 rgba(255,255,255,0.05) !important;
}

/* ── Component labels ── */
.label-wrap span, label > span:first-child {
  color: #64748b !important;
  font-size: 0.68rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  font-family: 'Inter', sans-serif !important;
}

/* ── Text inputs / textarea ── */
textarea, input[type="text"], input[type="password"], input[type="number"] {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 12px !important;
  color: #e2e8f0 !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.875rem !important;
  line-height: 1.65 !important;
  transition: border-color 0.25s, box-shadow 0.25s !important;
}
textarea:focus, input[type="text"]:focus, input[type="password"]:focus {
  border-color: rgba(99,102,241,0.55) !important;
  box-shadow: 0 0 0 3px rgba(99,102,241,0.15), 0 0 20px rgba(99,102,241,0.08) !important;
  outline: none !important;
}
textarea::placeholder, input::placeholder { color: #1e293b !important; }

/* ── File upload drop zone ── */
.file-preview-holder, .upload-container, [data-testid="file"] {
  border: 2px dashed rgba(255,255,255,0.10) !important;
  border-radius: 14px !important;
  background: rgba(255,255,255,0.02) !important;
  transition: all 0.3s !important;
}
.file-preview-holder:hover, .upload-container:hover {
  border-color: rgba(99,102,241,0.40) !important;
  background: rgba(99,102,241,0.04) !important;
  box-shadow: 0 0 24px rgba(99,102,241,0.08) !important;
}

/* ── PRIMARY button — neon indigo glow ── */
button.primary, button.lg.primary {
  background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
  box-shadow: 0 0 30px rgba(99,102,241,0.55), 0 4px 16px rgba(99,102,241,0.30) !important;
  border: none !important;
  border-radius: 14px !important;
  color: #ffffff !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 700 !important;
  font-size: 1rem !important;
  letter-spacing: 0.01em !important;
  padding: 14px 32px !important;
  transition: box-shadow 0.3s, transform 0.2s !important;
}
button.primary:hover, button.lg.primary:hover {
  box-shadow: 0 0 54px rgba(99,102,241,0.85), 0 8px 28px rgba(99,102,241,0.40) !important;
  transform: translateY(-2px) !important;
}
button.primary:active, button.lg.primary:active { transform: translateY(0) !important; }

/* ── Secondary buttons ── */
button.secondary {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 10px !important;
  color: #94a3b8 !important;
  font-family: 'Inter', sans-serif !important;
  transition: all 0.2s !important;
}
button.secondary:hover {
  background: rgba(99,102,241,0.10) !important;
  border-color: rgba(99,102,241,0.35) !important;
  color: #c7d2fe !important;
}

/* ── Tab navigation — glass pill style ── */
.tab-nav {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 14px !important;
  padding: 5px !important;
  gap: 2px !important;
  flex-wrap: wrap !important;
}
.tab-nav > button {
  background: transparent !important;
  border: none !important;
  border-radius: 10px !important;
  color: #475569 !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 500 !important;
  font-size: 0.8rem !important;
  padding: 7px 12px !important;
  transition: all 0.2s !important;
  white-space: nowrap !important;
}
.tab-nav > button:hover {
  color: #cbd5e1 !important;
  background: rgba(255,255,255,0.06) !important;
}
.tab-nav > button.selected {
  background: linear-gradient(135deg,rgba(99,102,241,0.25),rgba(99,102,241,0.14)) !important;
  border: 1px solid rgba(99,102,241,0.30) !important;
  color: #a5b4fc !important;
  font-weight: 600 !important;
  box-shadow: 0 0 14px rgba(99,102,241,0.20), inset 0 1px 0 rgba(255,255,255,0.08) !important;
}

/* ── Markdown / prose output ── */
.prose {
  color: #cbd5e1 !important;
  font-family: 'Inter', sans-serif !important;
  line-height: 1.75 !important;
  max-width: none !important;
}
.prose h1 {
  font-size: 1.75rem !important; font-weight: 900 !important;
  background: linear-gradient(135deg, #818cf8 0%, #06b6d4 55%, #a78bfa 100%);
  -webkit-background-clip: text !important; -webkit-text-fill-color: transparent !important;
  background-clip: text !important; margin-bottom: 0.75rem !important;
}
.prose h2 {
  font-size: 1.05rem !important; font-weight: 700 !important; color: #818cf8 !important;
  margin: 1.25rem 0 0.5rem !important; padding-bottom: 0.35rem !important;
  border-bottom: 1px solid rgba(99,102,241,0.20) !important;
}
.prose h3 {
  font-size: 0.9rem !important; font-weight: 600 !important; color: #67e8f9 !important;
  margin: 1rem 0 0.4rem !important;
}
.prose p    { color: #94a3b8 !important; font-size: 0.875rem !important; margin: 0.5rem 0 !important; }
.prose a    { color: #818cf8 !important; }
.prose a:hover { color: #a5b4fc !important; }
.prose strong  { color: #e2e8f0 !important; font-weight: 600 !important; }
.prose em      { color: #94a3b8 !important; }
.prose code {
  background: rgba(99,102,241,0.14) !important; color: #a5b4fc !important;
  border-radius: 5px !important; padding: 1px 6px !important; font-size: 0.82em !important;
}
.prose blockquote {
  border-left: 3px solid rgba(99,102,241,0.50) !important;
  background: rgba(99,102,241,0.07) !important;
  padding: 10px 16px !important; border-radius: 0 10px 10px 0 !important;
  color: #94a3b8 !important; font-style: italic !important; margin: 10px 0 !important;
}
.prose table { width: 100% !important; border-collapse: collapse !important; overflow: hidden !important; }
.prose thead th {
  background: rgba(99,102,241,0.18) !important; color: #818cf8 !important;
  font-size: 0.7rem !important; font-weight: 700 !important;
  text-transform: uppercase !important; letter-spacing: 0.07em !important;
  padding: 9px 12px !important; border: 1px solid rgba(99,102,241,0.20) !important;
}
.prose tbody td {
  padding: 8px 12px !important; border: 1px solid rgba(255,255,255,0.05) !important;
  color: #cbd5e1 !important; font-size: 0.85rem !important;
}
.prose tbody tr:nth-child(even) { background: rgba(255,255,255,0.02) !important; }
.prose ul, .prose ol { padding-left: 1.4rem !important; }
.prose li   { color: #94a3b8 !important; margin: 4px 0 !important; font-size: 0.875rem !important; }
.prose hr   { border-color: rgba(255,255,255,0.08) !important; margin: 1.5rem 0 !important; }

/* ── Radio group (provider selector) ── */
input[type="radio"] { accent-color: #6366f1 !important; }
.radio-group label, .wrap > label {
  color: #64748b !important; cursor: pointer !important;
  border-radius: 10px !important; border: 1px solid rgba(255,255,255,0.08) !important;
  background: rgba(255,255,255,0.03) !important;
  padding: 8px 14px !important; transition: all 0.2s !important;
}
.radio-group label:has(input:checked), .wrap > label:has(input:checked) {
  color: #818cf8 !important; border-color: rgba(99,102,241,0.40) !important;
  background: rgba(99,102,241,0.12) !important;
}

/* ── Dropdowns / selects ── */
select {
  background: rgba(255,255,255,0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  border-radius: 10px !important; color: #e2e8f0 !important;
  font-family: 'Inter', sans-serif !important; font-size: 0.875rem !important;
  transition: border-color 0.2s !important; cursor: pointer !important;
}
select:focus { border-color: rgba(99,102,241,0.50) !important; outline: none !important; }

/* ── Copy button ── */
button[aria-label="Copy"] {
  background: rgba(99,102,241,0.12) !important;
  border: 1px solid rgba(99,102,241,0.25) !important;
  border-radius: 8px !important; color: #818cf8 !important;
  transition: all 0.2s !important;
}
button[aria-label="Copy"]:hover {
  background: rgba(99,102,241,0.22) !important;
  box-shadow: 0 0 12px rgba(99,102,241,0.30) !important;
}

/* ── Header: force all paragraphs to centre ── */
#rr-header, #rr-header p, #rr-header h1 { text-align: center !important; }

/* ── Header badge pulse animation ── */
@keyframes rrPulse {
  0%, 100% { opacity:1.0; box-shadow:0 0 8px rgba(6,182,212,0.80); }
  50%       { opacity:0.4; box-shadow:0 0 2px rgba(6,182,212,0.25); }
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.35); border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.55); }
"""

with gr.Blocks(
    theme=gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="blue",
        neutral_hue="slate",
        font=[gr.themes.GoogleFont("Inter"), "sans-serif"],
    ),
    title="ResumeRadar",
    css=CUSTOM_CSS,
) as demo:
    gr.HTML(HEADER_HTML)

    # ── Hidden state: cache analysis data for reactive template/format refresh ──
    cached_resume  = gr.State(value=None)   # resume_data dict
    cached_job     = gr.State(value=None)   # job_data dict
    cached_rewrite = gr.State(value="")     # rewritten_text str

    with gr.Row():
        # ── Left Column: Inputs ──────────────────────────────────────────────
        with gr.Column(scale=1):
            gr.Markdown("### 📄 Your Resume")
            resume_file = gr.File(
                label="Upload Resume (PDF, DOCX, TXT)",
                file_types=[".pdf", ".docx", ".doc", ".txt"],
            )

            gr.Markdown("### 📋 Job Description")
            job_desc = gr.Textbox(
                label="Paste the full job description",
                placeholder="Include requirements, responsibilities, and preferred skills for the best analysis…",
                lines=10,
            )

            gr.Markdown("### ⚙️ Settings")
            with gr.Row():
                provider = gr.Radio(
                    ["Groq", "Gemini"],
                    label="AI Provider",
                    value="Groq",
                )
                tone = gr.Dropdown(
                    ["Professional", "Enthusiastic", "Concise"],
                    label="Cover Letter Tone",
                    value="Professional",
                )

            # ── Server-key status banner (computed once at startup) ──
            if _SERVER_GROQ and _SERVER_GEMINI:
                _key_status = "✅ **Both Groq & Gemini** server keys active — just pick a provider and click Analyze. You can also paste your own key below to override."
            elif _SERVER_GROQ:
                _key_status = "✅ **Groq** server key active — no key needed for Groq. For Gemini, enter your key below."
            elif _SERVER_GEMINI:
                _key_status = "✅ **Gemini** server key active — no key needed for Gemini. For Groq, enter your key below."
            else:
                _key_status = "⚠️ No server keys set. Enter a **Groq** or **Gemini** key below (both have free tiers)."

            gr.Markdown(_key_status)

            groq_key = gr.Textbox(
                label="Groq API Key (optional if server key is active)",
                placeholder="Leave blank to use server key · or paste gsk_… to override",
                type="password",
                visible=True,
            )
            gemini_key = gr.Textbox(
                label="Gemini API Key (optional if server key is active)",
                placeholder="Leave blank to use server key · or paste AIza… to override",
                type="password",
                visible=False,
            )

            def toggle_keys(prov):
                return gr.update(visible=prov == "Groq"), gr.update(visible=prov == "Gemini")

            provider.change(toggle_keys, inputs=provider, outputs=[groq_key, gemini_key])

            gr.Markdown("### 🎨 Resume Template")
            template_choice = gr.Dropdown(
                choices=list(TEMPLATE_STYLES.keys()),
                value="Modern Pro",
                label="Choose template for download",
            )

            analyze_btn = gr.Button("🚀 Analyze My Resume", variant="primary", size="lg")

            gr.Markdown(
                "_⏱ Analysis takes ~25–40 seconds. All 6 steps run sequentially._",
                elem_classes=["output-markdown"],
            )

        # ── Right Column: Outputs ────────────────────────────────────────────
        with gr.Column(scale=2):
            with gr.Tabs():
                with gr.Tab("📊 Score"):
                    score_out = gr.Markdown(label="Fit Score & Summary")

                with gr.Tab("🎯 Skill Breakdown"):
                    skills_out = gr.Markdown(label="Skill-by-Skill Matrix")

                with gr.Tab("⚠️ Gap Analysis"):
                    gaps_out = gr.Markdown(label="Missing & Unstated Skills")

                with gr.Tab("✍️ Rewritten Resume"):
                    rewrite_out = gr.Textbox(
                        label="AI-Rewritten & ATS-Optimized Resume",
                        lines=25,
                        show_copy_button=True,
                    )

                with gr.Tab("📝 Cover Letter"):
                    cover_out = gr.Textbox(
                        label="Tailored Cover Letter",
                        lines=20,
                        show_copy_button=True,
                    )

                with gr.Tab("🔍 Changes Made"):
                    changes_out = gr.Markdown(label="What Was Improved")

                with gr.Tab("🎤 Interview Prep"):
                    interview_out = gr.Markdown(label="Interview Questions & Tips")

                with gr.Tab("📥 Download Template"):
                    gr.Markdown(
                        "**Download your AI-rewritten resume.** Choose template and format, then "
                        "change either dropdown to instantly regenerate — no re-analysis needed.\n\n"
                        "| Format | Best for |\n|--------|----------|\n"
                        "| **HTML** | Open in browser → Ctrl+P → Save as PDF |\n"
                        "| **DOCX** | Edit in Word / Google Docs |\n"
                        "| **TXT** | ATS upload, plain copy-paste |"
                    )
                    dl_format = gr.Radio(
                        choices=["HTML", "DOCX", "TXT"],
                        value="HTML",
                        label="📄 Download Format",
                        interactive=True,
                    )
                    template_dl = gr.File(label="Download Resume", interactive=False)

    # ── Wire analyse button ──
    analyze_btn.click(
        fn=run_analysis,
        inputs=[resume_file, job_desc, provider, groq_key, gemini_key, tone, template_choice, dl_format],
        outputs=[
            score_out, skills_out, gaps_out,
            rewrite_out, cover_out, changes_out,
            interview_out, template_dl,
            cached_resume, cached_job, cached_rewrite,   # populate State
        ],
    )

    # ── Reactive: changing template OR format regenerates download instantly ──
    _regen_inputs  = [cached_resume, cached_job, cached_rewrite, template_choice, dl_format]
    _regen_outputs = [template_dl]

    template_choice.change(fn=regenerate_download, inputs=_regen_inputs, outputs=_regen_outputs)
    dl_format.change(fn=regenerate_download,       inputs=_regen_inputs, outputs=_regen_outputs)

    gr.HTML(FOOTER_HTML)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_api=False,          # hide "Use via API" button
        allowed_paths=[tempfile.gettempdir()],  # Gradio 5.x: allow serving HTML from /tmp
    )
