from utils.llm_client import LLMClient
from models.schemas import ResumeData, Skill, Experience, Education, SkillCategory

_SYSTEM = """You are an expert resume parser. Extract all structured information from the resume.
Return ONLY valid JSON — no markdown, no explanation."""

_USER_TEMPLATE = """Parse this resume into the following JSON structure:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "+1234567890",
  "summary": "Professional summary text",
  "skills": [
    {{"name": "Python", "category": "technical", "level": "expert"}},
    {{"name": "Communication", "category": "soft", "level": "intermediate"}}
  ],
  "experiences": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "duration": "Jan 2022 - Present",
      "responsibilities": ["Built X", "Led Y team"],
      "skills_used": ["Python", "SQL"]
    }}
  ],
  "education": [
    {{
      "degree": "B.Sc. Computer Science",
      "institution": "University Name",
      "year": "2020",
      "gpa": "3.8"
    }}
  ],
  "certifications": ["AWS Certified", "Google Cloud"]
}}

Skill categories: technical, soft, tool, language, framework, domain
Skill levels: beginner, intermediate, expert

RESUME:
{text}"""


def parse_resume(text: str, llm: LLMClient) -> ResumeData:
    data = llm.complete_json(_SYSTEM, _USER_TEMPLATE.format(text=text[:8000]))

    skills = []
    for s in data.get("skills", []):
        try:
            cat = SkillCategory(s.get("category", "technical"))
        except ValueError:
            cat = SkillCategory.TECHNICAL
        skills.append(Skill(name=s.get("name", ""), category=cat, level=s.get("level")))

    experiences = []
    for e in data.get("experiences", []):
        experiences.append(Experience(
            company=e.get("company", ""),
            role=e.get("role", ""),
            duration=e.get("duration", ""),
            responsibilities=e.get("responsibilities", []),
            skills_used=e.get("skills_used", []),
        ))

    education = []
    for ed in data.get("education", []):
        education.append(Education(
            degree=ed.get("degree", ""),
            institution=ed.get("institution", ""),
            year=ed.get("year"),
            gpa=ed.get("gpa"),
        ))

    return ResumeData(
        name=data.get("name", ""),
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        summary=data.get("summary", ""),
        skills=skills,
        experiences=experiences,
        education=education,
        certifications=data.get("certifications", []),
        raw_text=text,
    )
