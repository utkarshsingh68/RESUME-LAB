"""Configuration management for Resume Analyzer."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    API_TITLE: str = "Resume Analyzer API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "localhost"
    API_PORT: int = 8080
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    LLM_BASE_URL: Optional[str] = None
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2000
    
    # RapidAPI Configuration
    # - JSearch: Aggregated jobs (multiple boards)
    # - LinkedIn Job Search API: Direct LinkedIn jobs
    # - Glassdoor Real-Time API: Direct Glassdoor jobs
    # - Indeed API: Direct Indeed jobs
    RAPIDAPI_KEY: Optional[str] = None
    RAPIDAPI_HOST: str = "jsearch.p.rapidapi.com"
    LINKEDIN_API_HOST: str = "linkedin-job-search-api.p.rapidapi.com"
    GLASSDOOR_API_HOST: str = "glassdoor-real-time.p.rapidapi.com"
    INDEED_API_HOST: str = "indeed12.p.rapidapi.com"
    
    # spaCy Configuration
    SPACY_MODEL: str = "en_core_web_sm"
    
    # FAISS Configuration
    FAISS_DIMENSION: int = 384  # Sentence-Transformers default
    FAISS_INDEX_PATH: str = "./data/resume_index.faiss"

    # Job Recommendations
    JOB_DATA_PATH: str = "data/job_listings.json"
    # Default number of job recommendations to return
    JOB_RECOMMENDATION_TOP_K: int = 20
    # Number of top jobs to generate LLM explanations for (to avoid timeout)
    JOB_EXPLANATION_LIMIT: int = 10
    
    # File Upload Configuration
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FORMATS: list = ["pdf", "docx", "txt"]
    
    # Processing Configuration
    CHUNK_SIZE: int = 500  # Characters per chunk
    CHUNK_OVERLAP: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
