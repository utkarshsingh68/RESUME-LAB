"""Pydantic models for API requests and responses."""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class ResumeUploadRequest(BaseModel):
    """Resume file upload request."""
    file_name: str = Field(..., description="Name of the resume file")
    file_type: str = Field(..., description="File type: pdf, docx, or txt")


class AnalysisResponse(BaseModel):
    """Resume analysis response."""
    resume_id: str
    strengths: List[str]
    skills: List[str]
    experience_years: Optional[int]
    quality_score: int
    recommendations: List[str]
    analysis_text: str


class JobMatchRequest(BaseModel):
    """Resume-to-job matching request."""
    resume_id: str
    job_description: str = Field(..., description="Job description to match against")


class JobMatchResponse(BaseModel):
    """Resume-to-job matching response."""
    match_score: int
    strengths_for_role: List[str]
    missing_skills: List[str]
    recommendations: List[str]


class JobRecommendationFilters(BaseModel):
    """Filter options for job recommendations."""
    roles: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)
    experience_levels: List[str] = Field(default_factory=list)


class JobRecommendationRequest(BaseModel):
    """Request payload for job recommendations."""
    resume_id: str
    # Allow larger result sets so users can browse more matches at once
    top_k: int = Field(100, ge=1, le=200)
    filters: JobRecommendationFilters = Field(default_factory=JobRecommendationFilters)


class JobRecommendation(BaseModel):
    """Single job recommendation."""
    id: str
    title: str
    company: str
    location: str
    employment_type: Optional[str]
    experience_level: Optional[str]
    role: Optional[str]
    match_percentage: float
    similarity: float
    skill_overlap: float
    experience_alignment: float
    apply_readiness: str
    missing_skills: List[str]
    matched_skills: List[str]
    explanation: str
    apply_url: Optional[str] = None
    highlights: Optional[List[str]] = None


class JobRecommendationsResponse(BaseModel):
    """Response payload for job recommendations."""
    resume_id: str
    count: int
    jobs: List[JobRecommendation]


class JobFiltersResponse(BaseModel):
    """Available job filter values."""
    roles: List[str]
    locations: List[str]
    experience_levels: List[str]


class SearchRequest(BaseModel):
    """Vector search request."""
    query: str
    top_k: int = Field(20, description="Number of results to return")


class SearchResult(BaseModel):
    """Single search result."""
    similarity_score: float
    content: str
    metadata: Dict


class ContactInfo(BaseModel):
    """Extracted contact information."""
    emails: List[str]
    phones: List[str]
    urls: List[str]
