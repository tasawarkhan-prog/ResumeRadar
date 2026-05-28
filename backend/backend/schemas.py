from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    TOOL = "tool"
    LANGUAGE = "language"
    FRAMEWORK = "framework"
    DOMAIN = "domain"


class Skill(BaseModel):
    name: str
    category: SkillCategory = SkillCategory.TECHNICAL
    level: Optional[str] = None


class Experience(BaseModel):
    company: str
    role: str
    duration: str
    responsibilities: List[str] = []
    skills_used: List[str] = []


class Education(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None
    gpa: Optional[str] = None


class ResumeData(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    summary: str = ""
    skills: List[Skill] = []
    experiences: List[Experience] = []
    education: List[Education] = []
    certifications: List[str] = []
    raw_text: str = ""


class JobData(BaseModel):
    title: str = ""
    company: str = ""
    seniority: str = "mid"
    domain: str = ""
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    responsibilities: List[str] = []
    raw_text: str = ""


class SkillMatch(BaseModel):
    skill: str
    in_resume: bool
    similarity_score: float = 0.0
    matched_phrase: Optional[str] = None
    importance: str = "required"


class GapItem(BaseModel):
    skill: str
    gap_type: str  # missing | present_but_unstated
    suggestion: str = ""
    importance: str = "required"


class MatchResult(BaseModel):
    fit_score: float
    skill_breakdown: List[SkillMatch] = []
    gaps: List[GapItem] = []
    strengths: List[str] = []
    ats_score: float = 0.0


class ResumeChange(BaseModel):
    original: str
    improved: str
    reason: str


class RewrittenResume(BaseModel):
    original_text: str
    rewritten_text: str
    changes: List[ResumeChange] = []


class CoverLetterResult(BaseModel):
    cover_letter: str
    tone: str = "professional"
    key_points_addressed: List[str] = []


class InterviewQA(BaseModel):
    question: str
    answer: str
    category: str = "behavioral"   # behavioral | technical | situational


class InterviewPrepResult(BaseModel):
    qa_pairs: List[InterviewQA] = []
    tips: List[str] = []


class AnalysisResponse(BaseModel):
    resume_data: ResumeData
    job_data: JobData
    match_result: MatchResult
    rewritten_resume: RewrittenResume
    cover_letter: CoverLetterResult
    interview_prep: InterviewPrepResult = InterviewPrepResult()
    processing_time: float = 0.0
    provider_used: str = ""
