"""Resume-based job recommendation engine."""
import json
import logging
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from config import settings


class JobRecommender:
    """Recommend jobs by matching resume signals with job listings."""

    def __init__(self, embedding_service, llm_analyzer):
        self.embedding_service = embedding_service
        self.llm_analyzer = llm_analyzer
        self.logger = logging.getLogger(__name__)
        self.data_path = Path(settings.JOB_DATA_PATH)
        self.top_k = settings.JOB_RECOMMENDATION_TOP_K
        self.jobs: List[Dict] = []
        self.job_embeddings: Optional[np.ndarray] = None
        self.normalized_job_embeddings: Optional[np.ndarray] = None
        self._load_jobs()
        self._embed_jobs()

    # ---------------------------------------------------------------------
    # Data loading and preparation
    # ---------------------------------------------------------------------
    def _load_jobs(self) -> None:
        if not self.data_path.exists():
            self.logger.warning("Job data file not found at %s", self.data_path)
            self.jobs = []
            return

        try:
            with self.data_path.open("r", encoding="utf-8") as f:
                self.jobs = json.load(f)
        except Exception as exc:
            self.logger.exception("Failed to load job listings: %s", exc)
            self.jobs = []

    def _embed_jobs(self) -> None:
        if not self.jobs:
            self.job_embeddings = None
            self.normalized_job_embeddings = None
            return

        job_texts = [self._build_job_embedding_text(job) for job in self.jobs]
        embeddings = self.embedding_service.embed_batch(job_texts)
        self.job_embeddings = embeddings.astype("float32")
        self.normalized_job_embeddings = self._normalize(self.job_embeddings)

    @staticmethod
    def _build_job_embedding_text(job: Dict) -> str:
        parts = [
            job.get("title", ""),
            job.get("company", ""),
            job.get("description", ""),
            " ".join(job.get("skills", [])),
            " ".join(job.get("highlights", [])),
        ]
        return " \n".join(part for part in parts if part)

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-8
        return vectors / norms

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def refresh(self) -> None:
        """Reload job data from disk and recompute embeddings."""
        self._load_jobs()
        self._embed_jobs()

    def get_filter_options(self) -> Dict[str, List[str]]:
        roles = sorted({job.get("role", job.get("title", "")) for job in self.jobs if job.get("role") or job.get("title")})
        locations = sorted({job.get("location", "") for job in self.jobs if job.get("location")})
        experience_levels = sorted({job.get("experience_level", "") for job in self.jobs if job.get("experience_level")})
        return {
            "roles": roles,
            "locations": locations,
            "experience_levels": experience_levels,
        }

    def recommend_jobs(
        self,
        resume_id: str,
        resume_record: Dict,
        filters: Optional[Dict] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict]:
        if not self.jobs or self.normalized_job_embeddings is None:
            return []

        filters = filters or {}
        top_k = top_k or self.top_k

        resume_profile = self._prepare_resume_profile(resume_record)
        if resume_profile is None:
            self.logger.warning("Resume %s missing processed data; skipping recommendations", resume_id)
            return []

        filtered_indices = self._apply_filters(filters)
        if not filtered_indices:
            return []

        resume_vector = resume_profile["embedding"].reshape(1, -1)
        resume_vector = self._normalize(resume_vector)[0]

        recommendations: List[Tuple[int, Dict]] = []

        for idx in filtered_indices:
            job = self.jobs[idx]
            metrics = self._score_job(job, self.normalized_job_embeddings[idx], resume_profile)
            job_data = {**job, **metrics}
            self._ensure_required_fields(job_data, fallback_id=str(idx))
            recommendations.append((job_data["match_percentage"], job_data))

        recommendations.sort(key=lambda item: item[0], reverse=True)
        
        # Only generate LLM explanations for top N to avoid timeout
        explanation_limit = min(top_k, getattr(settings, 'JOB_EXPLANATION_LIMIT', 10))
        top_results = []
        for i, (score, job_data) in enumerate(recommendations[:top_k]):
            if i < explanation_limit:
                top_results.append(self._augment_with_explanation(resume_profile, job_data))
            else:
                # Use simple explanation for remaining jobs
                job_data['explanation'] = self._simple_explanation(job_data)
                self._coerce_metric_types(job_data)
                top_results.append(job_data)
        
        return top_results

    @staticmethod
    def _ensure_required_fields(job_data: Dict, fallback_id: str) -> None:
        """Make sure response-required fields exist to satisfy API schemas."""
        job_id = job_data.get("id") or job_data.get("job_id") or fallback_id
        job_data["id"] = str(job_id)

        title = job_data.get("title") or job_data.get("job_title") or "Untitled role"
        job_data["title"] = str(title)

        company = job_data.get("company") or job_data.get("employer_name") or "Unknown"
        job_data["company"] = str(company)

        location = job_data.get("location") or job_data.get("job_city") or job_data.get("job_country") or "Unknown"
        job_data["location"] = str(location)

        # Lists required by schema
        if not isinstance(job_data.get("missing_skills"), list):
            job_data["missing_skills"] = list(job_data.get("missing_skills") or [])
        if not isinstance(job_data.get("matched_skills"), list):
            job_data["matched_skills"] = list(job_data.get("matched_skills") or [])

        # Optional list
        highlights = job_data.get("highlights")
        if highlights is None:
            job_data["highlights"] = None
        elif not isinstance(highlights, list):
            job_data["highlights"] = [str(highlights)]

        # Ensure explanation always exists (may be overwritten later)
        if not job_data.get("explanation"):
            job_data["explanation"] = ""

        # Coerce numeric fields that will be serialized
        JobRecommender._coerce_metric_types(job_data)

    @staticmethod
    def _coerce_metric_types(job_data: Dict) -> None:
        for key in ("match_percentage", "skill_overlap", "experience_alignment", "similarity"):
            if key in job_data and job_data[key] is not None:
                try:
                    job_data[key] = float(job_data[key])
                except Exception:
                    job_data[key] = 0.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _apply_filters(self, filters: Dict) -> List[int]:
        if not filters:
            return list(range(len(self.jobs)))

        roles = {role.lower() for role in filters.get("roles", []) if role}
        locations = {loc.lower() for loc in filters.get("locations", []) if loc}
        experience_levels = {lvl.lower() for lvl in filters.get("experience_levels", []) if lvl}

        indices = []
        for idx, job in enumerate(self.jobs):
            if roles:
                job_role = job.get("role") or job.get("title", "")
                if not job_role or job_role.lower() not in roles:
                    continue
            if locations:
                job_loc = job.get("location", "").lower()
                if not any(loc in job_loc for loc in locations):
                    continue
            if experience_levels:
                job_level = job.get("experience_level", "").lower()
                if job_level not in experience_levels:
                    continue
            indices.append(idx)
        return indices

    def _prepare_resume_profile(self, resume_record: Dict) -> Optional[Dict]:
        processed = resume_record.get("processed")
        if not processed:
            return None

        skills = {skill.lower() for skill in processed.get("skills", [])}
        resume_text = resume_record.get("raw_text") or processed.get("raw_text") or ""

        embedding = resume_record.get("profile_embedding")
        if embedding is None:
            profile_text = self._build_resume_profile_text(processed)
            embedding = self.embedding_service.embed_text(profile_text).astype("float32")
            resume_record["profile_embedding"] = embedding

        years_experience = resume_record.get("experience_years")
        if years_experience is None:
            years_experience = self._estimate_experience_years(resume_text)
            resume_record["experience_years"] = years_experience

        return {
            "skills": skills,
            "text": resume_text,
            "embedding": embedding,
            "years_experience": years_experience,
        }

    @staticmethod
    def _build_resume_profile_text(processed: Dict) -> str:
        sections = processed.get("sections") or {}
        summary = sections.get("summary") or ""
        experience = sections.get("experience") or ""
        skills_section = sections.get("skills") or ""
        combined = " ".join(part for part in [summary, experience, skills_section] if part)
        if not combined:
            combined = processed.get("raw_text", "")
        return combined[:3000]

    @staticmethod
    def _estimate_experience_years(resume_text: str) -> float:
        matches = re.findall(r"(\d+)(?:\+)?\s*(?:years?|yrs?)", resume_text.lower())
        values = [int(m) for m in matches if m.isdigit()]
        if values:
            return float(min(max(values), 40))
        if "senior" in resume_text.lower():
            return 7.0
        if "lead" in resume_text.lower():
            return 8.0
        if "junior" in resume_text.lower():
            return 1.5
        return 3.0

    def _score_job(self, job: Dict, job_vector: np.ndarray, resume_profile: Dict) -> Dict:
        resume_vector = resume_profile["embedding"]
        resume_norm = resume_vector / (np.linalg.norm(resume_vector) + 1e-8)
        semantic_similarity = float(np.dot(job_vector, resume_norm))
        semantic_similarity = max(min(semantic_similarity, 1.0), 0.0)

        job_skills = {skill.lower() for skill in job.get("skills", [])}
        resume_skills = resume_profile["skills"]
        matched_skills = sorted(job_skills & resume_skills)
        missing_skills = sorted(job_skills - resume_skills)
        skill_overlap = float(len(matched_skills) / max(len(job_skills), 1))

        experience_alignment = self._compute_experience_alignment(job, resume_profile["years_experience"])

        match_percentage = self._weighted_score(
            semantic_similarity,
            skill_overlap,
            experience_alignment,
        )

        readiness = self._apply_readiness(skill_overlap, experience_alignment, semantic_similarity)

        return {
            "match_percentage": match_percentage,
            "similarity": semantic_similarity,
            "skill_overlap": skill_overlap,
            "experience_alignment": experience_alignment,
            "apply_readiness": readiness,
            "missing_skills": missing_skills,
            "matched_skills": matched_skills,
        }

    @staticmethod
    def _compute_experience_alignment(job: Dict, resume_years: float) -> float:
        required_years = job.get("experience_required")
        if required_years is None:
            level = (job.get("experience_level") or "").lower()
            mapping = {
                "entry": 0,
                "junior": 1,
                "mid": 3,
                "mid-level": 3,
                "mid-senior": 5,
                "senior": 6,
                "lead": 8,
            }
            required_years = mapping.get(level, 3)

        if required_years <= 0:
            return 1.0

        ratio = resume_years / float(required_years)
        return float(max(min(ratio, 1.2), 0.0))

    @staticmethod
    def _weighted_score(semantic: float, skills: float, experience: float) -> float:
        score = (semantic * 0.5 + skills * 0.3 + experience * 0.2) * 100
        return round(score, 2)

    @staticmethod
    def _apply_readiness(skill_overlap: float, experience_alignment: float, semantic: float) -> str:
        if skill_overlap >= 0.7 and experience_alignment >= 0.8 and semantic >= 0.6:
            return "Ready"
        if skill_overlap >= 0.4 and experience_alignment >= 0.5:
            return "Partial"
        return "Needs Upskilling"

    def _augment_with_explanation(self, resume_profile: Dict, job_metrics: Dict) -> Dict:
        explanation = self._generate_explanation(resume_profile, job_metrics)
        job_metrics["explanation"] = explanation
        job_metrics["match_percentage"] = float(job_metrics["match_percentage"])
        job_metrics["skill_overlap"] = float(job_metrics["skill_overlap"])
        job_metrics["experience_alignment"] = float(job_metrics["experience_alignment"])
        job_metrics["similarity"] = float(job_metrics["similarity"])
        return job_metrics

    def _generate_explanation(self, resume_profile: Dict, job_metrics: Dict) -> str:
        job_title = job_metrics.get("title", "the role")
        missing_skills = job_metrics.get("missing_skills", [])
        matched_skills = job_metrics.get("matched_skills", [])
        resume_text = resume_profile.get("text", "")

        prompt = (
            "You are an expert career assistant. Given the resume context and job metrics, "
            "write two concise sentences. First sentence: why the candidate is a good fit for the job. "
            "Second sentence: what the candidate should improve to raise their match score."
            f"\n\nJOB TITLE: {job_title}\n"
            f"MATCH PERCENTAGE: {job_metrics.get('match_percentage')}\n"
            f"SKILL OVERLAP: {len(matched_skills)} matched / {len(matched_skills) + len(missing_skills)} total\n"
            f"MISSING SKILLS: {', '.join(missing_skills) if missing_skills else 'None'}\n"
            "RESUME SNIPPET:\n"
            f"{resume_text[:600]}\n"
        )

        try:
            response = self.llm_analyzer.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You provide crisp, encouraging career guidance."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=200
            )
            return response.choices[0].message.content.strip()
        except Exception as exc:
            self.logger.warning("Explanation generation failed: %s", exc)
            if missing_skills:
                return (
                    f"Strong alignment on {', '.join(matched_skills[:3])} but add {', '.join(missing_skills[:3])} "
                    "to boost readiness."
                )
            return (
                f"Solid match for {job_title} based on existing experience and skills. "
                "Emphasize recent accomplishments to further strengthen the profile."
            )
    
    def _simple_explanation(self, job_metrics: Dict) -> str:
        """Generate a quick explanation without LLM call."""
        job_title = job_metrics.get("title", "the role")
        missing_skills = job_metrics.get("missing_skills", [])
        matched_skills = job_metrics.get("matched_skills", [])
        match_pct = job_metrics.get("match_percentage", 0)
        
        if match_pct >= 75:
            return f"Excellent match for {job_title} with {len(matched_skills)} matching skills."
        elif match_pct >= 50:
            if missing_skills:
                return f"Good match for {job_title}. Consider adding {', '.join(missing_skills[:3])} to strengthen your profile."
            return f"Good match for {job_title} based on your experience and skills."
        else:
            if missing_skills:
                return f"Developing match for {job_title}. Focus on gaining experience with {', '.join(missing_skills[:3])}."
            return f"Potential match for {job_title}. Highlight relevant experience to improve alignment."
