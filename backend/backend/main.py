import os
import sys
from pathlib import Path

# Ensure local packages are importable
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Always load .env from the backend folder regardless of where python is run from
load_dotenv(BASE_DIR / ".env")

from agents.pipeline import run_pipeline
from models.schemas import AnalysisResponse

app = FastAPI(
    title="ResumeRadar API",
    description="AI-powered resume analysis, semantic skill matching, and auto-tailored application engine.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "ResumeRadar API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/providers")
def available_providers():
    """Return which AI providers have API keys configured."""
    providers = []
    if os.getenv("GROQ_API_KEY"):
        providers.append("groq")
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        providers.append("gemini")
    return {
        "available": providers,
        "default": providers[0] if providers else None,
        "configured": len(providers) > 0,
    }


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    resume: UploadFile = File(..., description="Resume file — PDF, DOCX, or TXT"),
    job_description: str = Form(..., description="Full job description text"),
    provider: str = Form(None, description="AI provider: groq or gemini (auto-detected if omitted)"),
    cover_letter_tone: str = Form("professional", description="professional | enthusiastic | concise"),
    groq_api_key: str = Form(None, description="User Groq API key (overrides server .env)"),
    gemini_api_key: str = Form(None, description="User Gemini API key (overrides server .env)"),
):
    """
    Full analysis pipeline:
    1. Parse resume → structured data
    2. Analyze job description → requirements
    3. Semantic match → fit score + skill breakdown
    4. Gap detection → missing & unstated skills
    5. Resume rewrite → ATS-optimized with STAR bullets
    6. Cover letter → tailored to role
    """
    allowed = {".pdf", ".docx", ".doc", ".txt"}
    ext = Path(resume.filename or "").suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Please upload a PDF, DOCX, or TXT file.",
        )

    file_bytes = await resume.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum allowed size is 10 MB.")

    if not job_description or len(job_description.strip()) < 20:
        raise HTTPException(status_code=400, detail="Job description is too short. Paste the full job posting.")

    valid_tones = {"professional", "enthusiastic", "concise"}
    tone = cover_letter_tone if cover_letter_tone in valid_tones else "professional"

    try:
        result = run_pipeline(
            resume_bytes=file_bytes,
            resume_filename=resume.filename or "resume.pdf",
            job_description=job_description,
            provider=provider or None,
            cover_letter_tone=tone,
            groq_api_key=groq_api_key or None,
            gemini_api_key=gemini_api_key or None,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}. Check your API key and try again.",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,
    )
