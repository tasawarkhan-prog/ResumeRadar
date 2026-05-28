from utils.llm_client import LLMClient
from models.schemas import ResumeData, JobData, MatchResult, InterviewPrepResult, InterviewQA

_SYSTEM = """You are an expert interview coach with 15 years of experience.
Generate interview questions AND sample answers for a candidate.

Answer writing rules:
- Write answers in FIRST PERSON from the candidate's perspective ("I did...", "I used...", "My approach was...")
- Use the candidate's ACTUAL skills and experience mentioned in the context
- Behavioral answers MUST follow STAR format: one sentence for Situation, one for Task, two for Action, one for Result
- Technical answers: explain the candidate's real tech experience clearly and simply
- Situational answers: give a specific step-by-step plan (3-4 numbered steps)
- Language: conversational, confident, natural — NOT robotic or corporate-sounding
- Each answer: 60-90 words exactly
Return ONLY valid JSON."""

_USER_TEMPLATE = """Generate 12 interview Q&A pairs for this candidate applying to this role.

CANDIDATE PROFILE:
- Name: {name}
- Most Recent Role: {last_role}
- Key Skills: {skills}
- Summary: {summary}

TARGET JOB:
- Title: {title} at {company}
- Domain: {domain}
- Required Skills: {required}
- Fit Score: {score}/100

MATCH CONTEXT:
- Confirmed strengths: {strengths}
- Skill gaps the interviewer may probe: {gaps}

Return JSON in exactly this format:
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
  "tips": [
    "Tip about STAR method",
    "Tip about researching the company",
    "Tip about matching keywords to the JD",
    "Tip about asking smart questions",
    "Tip about body language and confidence"
  ]
}}

IMPORTANT:
- Behavioral answers must reference candidate's real experience at {last_company}
- Technical answers must reference candidate's actual skills: {skills}
- Make answers sound like a confident, real human — not a template
- Do NOT use placeholders like [company name] or [project] — use real details from the profile"""


def generate_interview_prep(
    resume: ResumeData,
    job: JobData,
    match: MatchResult,
    llm: LLMClient,
) -> InterviewPrepResult:
    last_exp = resume.experiences[0] if resume.experiences else None
    last_role = f"{last_exp.role} at {last_exp.company}" if last_exp else "previous role"
    last_company = last_exp.company if last_exp else "my previous company"

    top_skills = ", ".join(s.name for s in resume.skills[:8])
    gaps = [g.skill for g in match.gaps if g.gap_type == "missing" and g.importance == "required"][:4]
    strengths = match.strengths[:5]

    try:
        data = llm.complete_json(
            _SYSTEM,
            _USER_TEMPLATE.format(
                name=resume.name or "the candidate",
                last_role=last_role,
                last_company=last_company,
                skills=top_skills or "relevant technical skills",
                summary=resume.summary[:250] if resume.summary else "Experienced professional",
                title=job.title or "the role",
                company=job.company or "the company",
                domain=job.domain or "the industry",
                required=", ".join(job.required_skills[:8]) or "see job description",
                score=match.fit_score,
                strengths=", ".join(strengths) or "technical skills",
                gaps=", ".join(gaps) or "none critical",
            ),
        )
    except Exception:
        # Graceful fallback — return minimal set if LLM fails
        return _fallback_prep(resume, job, match)

    qa_pairs = [
        InterviewQA(
            question=qa.get("question", "").strip(),
            answer=qa.get("answer", "").strip(),
            category=qa.get("category", "behavioral"),
        )
        for qa in data.get("qa_pairs", [])
        if qa.get("question") and qa.get("answer")
    ]

    if not qa_pairs:
        return _fallback_prep(resume, job, match)

    return InterviewPrepResult(
        qa_pairs=qa_pairs,
        tips=data.get("tips", _default_tips()),
    )


def _default_tips():
    return [
        "Use the STAR method (Situation → Task → Action → Result) for every behavioral answer.",
        "Research the company before the interview — mention one specific product, value, or initiative.",
        "Mirror exact keywords from the job description in your answers to signal alignment.",
        "Prepare 3 smart questions to ask the interviewer about team culture and success metrics.",
        "Practice answers aloud — the gap between thinking and saying smoothly is larger than you think.",
    ]


def _fallback_prep(resume: ResumeData, job: JobData, match: MatchResult) -> InterviewPrepResult:
    role = job.title or "this role"
    company = job.company or "this company"
    skill1 = resume.skills[0].name if resume.skills else "your primary skill"
    last = resume.experiences[0] if resume.experiences else None
    last_co = last.company if last else "your last company"

    qa_pairs = [
        InterviewQA(
            question=f"Tell me about yourself and why you're applying for the {role} position.",
            answer=f"I'm a {skill1} professional with experience building real-world solutions. "
                   f"I've most recently worked at {last_co} where I developed strong problem-solving skills. "
                   f"I'm drawn to {company} because the {role} role aligns perfectly with where I want to grow next.",
            category="behavioral",
        ),
        InterviewQA(
            question="Describe a challenging project and how you handled it.",
            answer=f"At {last_co}, I was tasked with delivering a project under a tight deadline. "
                   f"I broke it into smaller milestones, communicated blockers early, and used {skill1} to automate the most time-consuming parts. "
                   f"We delivered on time and the solution was adopted by the full team.",
            category="behavioral",
        ),
        InterviewQA(
            question=f"How have you used {skill1} in a production environment?",
            answer=f"I've used {skill1} extensively in professional projects. "
                   f"I'm comfortable with the core concepts and have applied it to solve real business problems. "
                   f"I stay current with new developments in this area through hands-on projects and continuous learning.",
            category="technical",
        ),
    ]

    return InterviewPrepResult(qa_pairs=qa_pairs, tips=_default_tips())
