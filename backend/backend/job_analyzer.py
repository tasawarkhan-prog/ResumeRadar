from utils.llm_client import LLMClient
from models.schemas import JobData

_SYSTEM = """You are an expert job description analyst. Extract all structured requirements.
Return ONLY valid JSON — no markdown, no explanation."""

_USER_TEMPLATE = """Analyze this job description and return JSON:
{{
  "title": "Job Title",
  "company": "Company Name",
  "seniority": "mid",
  "domain": "Machine Learning / Backend",
  "required_skills": ["Python", "Machine Learning", "SQL"],
  "preferred_skills": ["Docker", "Kubernetes", "AWS"],
  "responsibilities": ["Design ML models", "Deploy to production"]
}}

Rules:
- seniority: one of junior, mid, senior, lead, executive
- domain: the main technical/industry domain (e.g. "AI/ML Engineering", "Web Development")
- required_skills: skills listed as required, must-have, or essential
- preferred_skills: skills listed as nice-to-have, preferred, or plus

JOB DESCRIPTION:
{text}"""


def analyze_job(text: str, llm: LLMClient) -> JobData:
    data = llm.complete_json(_SYSTEM, _USER_TEMPLATE.format(text=text[:6000]))

    return JobData(
        title=data.get("title", ""),
        company=data.get("company", ""),
        seniority=data.get("seniority", "mid"),
        domain=data.get("domain", ""),
        required_skills=data.get("required_skills", []),
        preferred_skills=data.get("preferred_skills", []),
        responsibilities=data.get("responsibilities", []),
        raw_text=text,
    )
