from utils.llm_client import LLMClient
from models.schemas import ResumeData, JobData, MatchResult, RewrittenResume, ResumeChange

_SYSTEM = """You are an expert resume writer. Rewrite resumes to maximize ATS match and recruiter impact
using the STAR method. Preserve 100% factual accuracy — never fabricate skills or results.
Return ONLY valid JSON — no markdown, no explanation."""

_USER_TEMPLATE = """Rewrite this resume to better match the job description.

TARGET JOB: {title}
REQUIRED SKILLS: {required}
PREFERRED SKILLS: {preferred}
KEY RESPONSIBILITIES: {responsibilities}
GAPS TO ADDRESS: {gaps}
STRENGTHS TO HIGHLIGHT: {strengths}

ORIGINAL RESUME:
{resume}

Return JSON:
{{
  "rewritten_text": "Full rewritten resume — all sections, no placeholders",
  "changes": [
    {{
      "original": "Worked on Python projects",
      "improved": "Engineered 3 production Python microservices that reduced API latency by 40%",
      "reason": "Added quantified impact + STAR method + aligned with Python requirement"
    }}
  ]
}}

Rules:
1. Only reframe existing experience — NEVER add fake skills or achievements
2. Weave in job keywords where they honestly apply
3. Quantify achievements wherever possible (%, time saved, scale)
4. Use strong action verbs (engineered, architected, optimized, led)
5. Mirror the job description language where truthful"""


def rewrite_resume(
    resume: ResumeData, job: JobData, match: MatchResult, llm: LLMClient
) -> RewrittenResume:
    gaps_text = "; ".join(
        f"{g.skill} ({g.gap_type})" + (f": {g.suggestion}" if g.suggestion else "")
        for g in match.gaps[:8]
    ) or "None identified"

    data = llm.complete_json(
        _SYSTEM,
        _USER_TEMPLATE.format(
            title=job.title,
            required=", ".join(job.required_skills[:10]),
            preferred=", ".join(job.preferred_skills[:6]),
            responsibilities="; ".join(job.responsibilities[:4]),
            gaps=gaps_text,
            strengths=", ".join(match.strengths),
            resume=resume.raw_text[:6000],
        ),
    )

    raw_changes = data.get("changes", [])
    changes = [
        ResumeChange(
            original=c.get("original", ""),
            improved=c.get("improved", ""),
            reason=c.get("reason", ""),
        )
        for c in raw_changes
    ]

    return RewrittenResume(
        original_text=resume.raw_text,
        rewritten_text=data.get("rewritten_text", resume.raw_text),
        changes=changes,
    )
