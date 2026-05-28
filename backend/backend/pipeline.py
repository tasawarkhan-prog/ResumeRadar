import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from utils.extractor import extract_text
from utils.llm_client import LLMClient
from agents.resume_parser import parse_resume
from agents.job_analyzer import analyze_job
from agents.semantic_matcher import compute_fit_score
from agents.rewriter import rewrite_resume
from agents.cover_letter import generate_cover_letter
from agents.interview_agent import generate_interview_prep
from models.schemas import AnalysisResponse


def run_pipeline(
    resume_bytes: bytes,
    resume_filename: str,
    job_description: str,
    provider: str = None,
    cover_letter_tone: str = "professional",
    groq_api_key: str = None,
    gemini_api_key: str = None,
) -> AnalysisResponse:
    """
    Full ResumeRadar pipeline:
    extract → parse resume → analyze job → semantic match → rewrite → cover letter

    API key priority: user-provided > server .env
    """
    t0 = time.time()

    # Step 1: Extract text from uploaded file
    resume_text = extract_text(resume_bytes, resume_filename)
    if not resume_text or len(resume_text.strip()) < 50:
        raise ValueError(
            "The uploaded file appears to be empty or unreadable. "
            "Please ensure it contains selectable text (not a scanned image)."
        )

    # Step 2: Initialize LLM — user key takes priority over server .env
    llm = LLMClient(
        provider=provider,
        groq_api_key=groq_api_key,
        gemini_api_key=gemini_api_key,
    )

    # Step 3: Parse resume & analyze job with LLM (structured extraction)
    resume_data = parse_resume(resume_text, llm)
    job_data = analyze_job(job_description, llm)

    # Step 4: Semantic skill matching with sentence-transformers
    match_result = compute_fit_score(resume_data, job_data)

    # Step 5: Rewrite resume to maximize ATS + recruiter match
    rewritten = rewrite_resume(resume_data, job_data, match_result, llm)

    # Step 6: Generate tailored cover letter
    cover_letter = generate_cover_letter(
        resume_data, job_data, match_result, cover_letter_tone, llm
    )

    # Step 7: Generate interview Q&A with humanized answers
    interview_prep = generate_interview_prep(resume_data, job_data, match_result, llm)

    return AnalysisResponse(
        resume_data=resume_data,
        job_data=job_data,
        match_result=match_result,
        rewritten_resume=rewritten,
        cover_letter=cover_letter,
        interview_prep=interview_prep,
        processing_time=round(time.time() - t0, 2),
        provider_used=llm.provider,
    )
