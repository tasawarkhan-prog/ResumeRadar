from utils.llm_client import LLMClient
from models.schemas import ResumeData, JobData, MatchResult, CoverLetterResult

_SYSTEM = """You are an expert cover letter writer. Write compelling, personalized cover letters
that feel human and specific — not generic templates. Return ONLY valid JSON."""

_USER_TEMPLATE = """Write a cover letter for this candidate applying to this role.

CANDIDATE:
- Name: {name}
- Summary: {summary}
- Top Skills: {skills}
- Most Recent Role: {last_role}
- Match Strengths: {strengths}

TARGET ROLE:
- Job Title: {title} at {company}
- Required Skills: {required}
- Key Responsibilities: {responsibilities}
- Fit Score: {score}/100

TONE: {tone}

Return JSON:
{{
  "cover_letter": "Full 3-4 paragraph cover letter. No [placeholders]. Real content only.",
  "key_points_addressed": ["Specific point 1 addressed", "Specific point 2 addressed"]
}}

Cover letter structure:
1. Opening hook — specific to this company/role (not generic "I am writing to apply for...")
2. Connect 2 specific past achievements directly to job requirements
3. Show cultural/domain alignment with one specific insight about the company or role
4. Strong closing with clear call to action
Target: 280-340 words. Tone must match: professional=formal yet warm, enthusiastic=energetic, concise=punchy."""


def generate_cover_letter(
    resume: ResumeData,
    job: JobData,
    match: MatchResult,
    tone: str = "professional",
    llm: LLMClient = None,
) -> CoverLetterResult:
    last_role = (
        f"{resume.experiences[0].role} at {resume.experiences[0].company}"
        if resume.experiences
        else "See resume"
    )

    data = llm.complete_json(
        _SYSTEM,
        _USER_TEMPLATE.format(
            name=resume.name or "the candidate",
            summary=resume.summary[:400] if resume.summary else "Experienced professional",
            skills=", ".join(s.name for s in resume.skills[:8]),
            last_role=last_role,
            strengths=", ".join(match.strengths) or "relevant technical skills",
            title=job.title,
            company=job.company or "your company",
            required=", ".join(job.required_skills[:8]),
            responsibilities="; ".join(job.responsibilities[:3]),
            score=match.fit_score,
            tone=tone,
        ),
    )

    return CoverLetterResult(
        cover_letter=data.get("cover_letter", ""),
        tone=tone,
        key_points_addressed=data.get("key_points_addressed", []),
    )
