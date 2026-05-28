import numpy as np
from typing import Optional
from models.schemas import ResumeData, JobData, MatchResult, SkillMatch, GapItem

_model: Optional[object] = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def compute_fit_score(resume: ResumeData, job: JobData) -> MatchResult:
    from sklearn.metrics.pairwise import cosine_similarity

    model = _get_model()
    resume_text_lower = resume.raw_text.lower()

    # Collect all resume skill mentions
    resume_skill_names = list({s.name.lower() for s in resume.skills})
    for exp in resume.experiences:
        resume_skill_names.extend([s.lower() for s in exp.skills_used])
    resume_skill_names = list(set(resume_skill_names))

    all_job_skills = job.required_skills + job.preferred_skills
    if not all_job_skills:
        return MatchResult(fit_score=50.0, ats_score=50.0)

    # Encode
    job_embeddings = model.encode(all_job_skills, convert_to_numpy=True)
    resume_embeddings = (
        model.encode(resume_skill_names, convert_to_numpy=True)
        if resume_skill_names
        else None
    )

    skill_matches: list[SkillMatch] = []
    gaps: list[GapItem] = []
    total_score = 0.0

    for i, job_skill in enumerate(all_job_skills):
        importance = "required" if job_skill in job.required_skills else "preferred"
        weight = 1.5 if importance == "required" else 1.0
        job_emb = job_embeddings[i : i + 1]

        exact_match = job_skill.lower() in resume_text_lower
        best_sim = 0.0
        best_phrase: Optional[str] = None

        if resume_embeddings is not None and len(resume_embeddings) > 0:
            sims = cosine_similarity(job_emb, resume_embeddings)[0]
            best_idx = int(np.argmax(sims))
            best_sim = float(sims[best_idx])
            if best_sim > 0.55:
                best_phrase = resume_skill_names[best_idx]

        # Only count as "in resume" for genuine semantic overlap (>= 0.55)
        semantic_match = best_sim >= 0.55
        in_resume = exact_match or semantic_match

        # Honest graduated scoring — no credit below 0.30 (truly unrelated)
        if exact_match:
            effective_score = 1.0
        elif best_sim >= 0.65:
            # Strong semantic overlap → full proportional credit
            effective_score = best_sim
        elif best_sim >= 0.50:
            # Clear partial overlap → meaningful partial credit
            effective_score = 0.35 + (best_sim - 0.50) * 2.0
        elif best_sim >= 0.35:
            # Tangential overlap → small credit only
            effective_score = best_sim * 0.40
        else:
            # Truly unrelated → zero credit (no inflation)
            effective_score = 0.0

        total_score += effective_score * weight

        skill_matches.append(SkillMatch(
            skill=job_skill,
            in_resume=in_resume,
            similarity_score=round(best_sim, 3),
            matched_phrase=best_phrase,
            importance=importance,
        ))

        if not in_resume:
            gaps.append(GapItem(
                skill=job_skill,
                gap_type="missing",
                importance=importance,
            ))
        elif semantic_match and not exact_match:
            gaps.append(GapItem(
                skill=job_skill,
                gap_type="present_but_unstated",
                suggestion=f"You have '{best_phrase}' — explicitly mention '{job_skill}' to beat ATS filters.",
                importance=importance,
            ))

    max_possible = sum(1.5 if s in job.required_skills else 1.0 for s in all_job_skills)
    raw_score = (total_score / max_possible) * 100 if max_possible > 0 else 0.0
    # No artificial floor — if nothing matches, show 0. Cap at 100.
    fit_score = round(max(0.0, min(100.0, raw_score)), 1)

    ats_hits = sum(1 for s in all_job_skills if s.lower() in resume_text_lower)
    ats_score = (ats_hits / len(all_job_skills)) * 100

    strengths = [
        m.skill for m in skill_matches
        if m.in_resume and (m.similarity_score > 0.60 or m.matched_phrase is not None)
    ][:6]

    return MatchResult(
        fit_score=fit_score,
        skill_breakdown=skill_matches,
        gaps=gaps,
        strengths=strengths,
        ats_score=round(ats_score, 1),
    )
