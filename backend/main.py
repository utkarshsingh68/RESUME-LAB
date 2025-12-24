"""FastAPI backend for Resume Analyzer."""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import uuid
from typing import Dict
from pathlib import Path
import json

import numpy as np

from config import settings
from core.nlp_pipeline import ResumePipeline
from core.vector_store import VectorStore, EmbeddingService
from core.llm_analyzer import ResumeLLMAnalyzer
from core.ats_scoring import ATSScoringEngine, SkillGapAnalyzer
from core.resume_rag import ResumeRAG, ResumeOptimizer
from core.job_recommender import JobRecommender
from core.job_fetcher import JobFetcher
from utils.file_processor import FileProcessor
from utils.schemas import (
    ResumeUploadRequest, AnalysisResponse, JobMatchRequest, JobMatchResponse,
    JobRecommendationRequest, JobRecommendationsResponse, JobFiltersResponse,
    SearchRequest, SearchResult, ContactInfo
)

# Initialize logger
logger = logging.getLogger(__name__)


# Global state management
resume_storage: Dict[str, Dict] = {}
embedding_service: EmbeddingService = None
vector_store: VectorStore = None
ats_engine: ATSScoringEngine = None
skill_analyzer: SkillGapAnalyzer = None
resume_rag: ResumeRAG = None
resume_optimizer: ResumeOptimizer = None
nlp_pipeline: ResumePipeline = None
llm_analyzer: ResumeLLMAnalyzer = None
job_recommender: JobRecommender = None
job_fetcher: JobFetcher = None


resumes_dir = Path(__file__).parent.parent / "data" / "resumes"


def _serialize_resume_record(record: Dict) -> Dict:
    """Convert in-memory resume record into JSON-safe payload."""
    payload = {**record}
    embedding = payload.get("profile_embedding")
    if embedding is not None:
        if isinstance(embedding, np.ndarray):
            payload["profile_embedding"] = embedding.astype("float32").tolist()
        else:
            payload["profile_embedding"] = embedding
    return payload


def _deserialize_resume_record(payload: Dict) -> Dict:
    """Convert JSON payload back into in-memory resume record."""
    record = {**payload}
    embedding = record.get("profile_embedding")
    if embedding is not None and not isinstance(embedding, np.ndarray):
        record["profile_embedding"] = np.array(embedding, dtype="float32")
    return record


def save_resume_to_disk(resume_id: str, record: Dict) -> None:
    """Persist a processed resume record so sessions survive reloads."""
    resumes_dir.mkdir(parents=True, exist_ok=True)
    path = resumes_dir / f"{resume_id}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(_serialize_resume_record(record), f, ensure_ascii=False)


def delete_resume_from_disk(resume_id: str) -> None:
    path = resumes_dir / f"{resume_id}.json"
    try:
        path.unlink(missing_ok=True)
    except Exception:
        logger.exception("Failed to delete persisted resume %s", resume_id)


def load_resumes_from_disk() -> None:
    """Load persisted resumes into memory (for job recs + analysis continuity)."""
    if not resumes_dir.exists():
        return

    loaded = 0
    for path in resumes_dir.glob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            resume_id = payload.get("resume_id") or path.stem
            record = _deserialize_resume_record(payload)
            resume_storage[resume_id] = record
            loaded += 1
        except Exception:
            logger.exception("Failed to load persisted resume %s", path.name)

    if loaded:
        logger.info("Loaded %d persisted resumes", loaded)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    global embedding_service, vector_store, nlp_pipeline, llm_analyzer, ats_engine, skill_analyzer, resume_rag, resume_optimizer, job_recommender, job_fetcher
    
    # Startup
    print("🚀 Initializing Resume Analyzer...")
    embedding_service = EmbeddingService()
    vector_store = VectorStore()

    nlp_pipeline = ResumePipeline()
    llm_analyzer = ResumeLLMAnalyzer()
    ats_engine = ATSScoringEngine()
    skill_analyzer = SkillGapAnalyzer()
    resume_rag = ResumeRAG(vector_store, embedding_service, llm_analyzer)
    resume_optimizer = ResumeOptimizer(llm_analyzer)
    job_recommender = JobRecommender(embedding_service, llm_analyzer)
    job_fetcher = JobFetcher()
    
    try:
        vector_store.load()
        print("✅ Vector store loaded from disk")
    except:
        print("📝 Starting with fresh vector store")

    # Restore resumes so clients keep working after reloads.
    load_resumes_from_disk()
    
    yield
    
    # Shutdown
    print("💾 Persisting vector store...")
    vector_store.save()


# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware for web app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Resume Analyzer API",
        "version": settings.API_VERSION
    }


@app.post("/api/upload", response_model=Dict)
async def upload_resume(file: UploadFile = File(...)) -> Dict:
    """Upload and process resume file."""
    
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in settings.ALLOWED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Allowed: {settings.ALLOWED_FORMATS}"
        )
    
    # Read file content
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")
    
    # Process resume
    resume_id = str(uuid.uuid4())
    
    try:
        # Extract text
        resume_text = FileProcessor.process_file(content, file_ext)
        
        # Full NLP pipeline
        processed_data = nlp_pipeline.process_resume(resume_text)
        
        # Generate embeddings for chunks
        embeddings = embedding_service.embed_batch(processed_data["chunks"])
        
        # Store in vector database
        metadata = [
            {"resume_id": resume_id, "chunk_idx": i, "text": chunk}
            for i, chunk in enumerate(processed_data["chunks"])
        ]
        vector_store.add_vectors(embeddings, metadata)
        
        profile_text = JobRecommender._build_resume_profile_text(processed_data)
        profile_embedding = embedding_service.embed_text(profile_text).astype("float32")
        experience_years = JobRecommender._estimate_experience_years(resume_text)

        resume_record = {
            "resume_id": resume_id,
            "filename": file.filename,
            "raw_text": resume_text,
            "processed": processed_data,
            "profile_embedding": profile_embedding,
            "experience_years": experience_years,
        }

        resume_storage[resume_id] = resume_record

        # Persist resume so job recommendations remain personalized after server reload.
        try:
            save_resume_to_disk(resume_id, resume_record)
        except Exception:
            logger.exception("Failed to persist resume %s", resume_id)
        
        return {
            "resume_id": resume_id,
            "filename": file.filename,
            "status": "processed",
            "token_count": processed_data["token_count"],
            "sections": list(processed_data["sections"].keys()),
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/resume/{resume_id}", response_model=Dict)
async def get_resume_info(resume_id: str) -> Dict:
    """Get extracted resume information."""
    
    if resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    data = resume_storage[resume_id]
    processed = data["processed"]
    
    return {
        "resume_id": resume_id,
        "contact_info": processed["contact_info"],
        "skills": processed["skills"],
        "entities": processed["entities"],
        "token_count": processed["token_count"],
    }


@app.post("/api/analyze/{resume_id}", response_model=Dict)
async def analyze_resume(resume_id: str) -> Dict:
    """Perform comprehensive LLM-based analysis."""
    
    if resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_text = resume_storage[resume_id]["raw_text"]
    
    try:
        analysis = llm_analyzer.analyze_resume(resume_text)
        return {
            "resume_id": resume_id,
            "analysis": analysis["raw_analysis"],
            "status": "completed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.post("/api/match")
async def match_resume_to_job(request: JobMatchRequest) -> JobMatchResponse:
    """Match resume against job description."""
    
    if request.resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_text = resume_storage[request.resume_id]["raw_text"]
    
    try:
        result = llm_analyzer.match_resume_to_job(resume_text, request.job_description)
        
        return JobMatchResponse(
            match_score=result.get("match_score", 0),
            strengths_for_role=result.get("strengths", []),
            missing_skills=result.get("missing_skills", []),
            recommendations=result.get("recommendations", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching error: {str(e)}")


@app.post("/api/search", response_model=Dict)
async def search_resumes(request: SearchRequest) -> Dict:
    """Semantic search across resume chunks."""
    
    try:
        # Generate query embedding
        query_embedding = embedding_service.embed_text(request.query)
        
        # Search vector store
        results = vector_store.search(query_embedding, k=request.top_k)
        
        search_results = [
            {
                "similarity_score": float(score),
                "content": metadata["text"],
                "resume_id": metadata.get("resume_id"),
            }
            for score, metadata in results
        ]
        
        return {
            "query": request.query,
            "results_count": len(search_results),
            "results": search_results,
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.get("/api/jobs/filters", response_model=JobFiltersResponse)
async def get_job_filters() -> JobFiltersResponse:
    """Return available job recommendation filters."""
    options = job_recommender.get_filter_options()
    return JobFiltersResponse(**options)


@app.post("/api/jobs/recommendations", response_model=JobRecommendationsResponse)
async def recommend_jobs(request: JobRecommendationRequest) -> JobRecommendationsResponse:
    """Recommend jobs for a given resume using semantic and skill signals."""

    if request.resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")

    resume_record = resume_storage[request.resume_id]
    recommendations = job_recommender.recommend_jobs(
        request.resume_id,
        resume_record,
        request.filters.model_dump(),
        request.top_k,
    )

    return JobRecommendationsResponse(
        resume_id=request.resume_id,
        count=len(recommendations),
        jobs=recommendations,
    )


@app.get("/api/resumes")
async def list_resumes() -> Dict:
    """List all processed resumes."""
    return {
        "total_resumes": len(resume_storage),
        "resumes": [
            {
                "resume_id": rid,
                "filename": data["filename"],
                "token_count": data["processed"]["token_count"],
            }
            for rid, data in resume_storage.items()
        ]
    }


@app.post("/api/ats-score")
async def calculate_ats_score(request: JobMatchRequest) -> Dict:
    """Calculate detailed ATS score with skill gaps."""
    
    if request.resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_data = resume_storage[request.resume_id]["processed"]
    
    try:
        ats_score = ats_engine.calculate_ats_score(
            resume_data,
            request.job_description
        )
        
        return {
            "resume_id": request.resume_id,
            "total_score": ats_score.total_score,
            "match_percentage": ats_score.match_percentage,
            "breakdown": ats_score.breakdown,
            "matched_skills": ats_score.matched_skills,
            "missing_skills": [
                {
                    "skill": gap.skill,
                    "category": gap.category,
                    "priority": gap.priority,
                    "alternatives": gap.alternative_skills,
                }
                for gap in ats_score.missing_skills[:10]
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")


@app.post("/api/skill-gaps")
async def analyze_skill_gaps(request: JobMatchRequest) -> Dict:
    """Perform comprehensive skill gap analysis."""
    
    if request.resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_data = resume_storage[request.resume_id]["processed"]
    
    try:
        gap_analysis = skill_analyzer.analyze_gaps(
            resume_data,
            request.job_description
        )
        return gap_analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis error: {str(e)}")


@app.post("/api/resume-chat")
async def chat_with_resume(
    resume_id: str = Query(...),
    question: str = Query(...)
) -> Dict:
    """Chat with resume using RAG."""
    
    if resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        answer = resume_rag.answer_question(resume_id, question)
        return answer
    except Exception as e:
        logger.exception("Chat error for resume %s", resume_id)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.post("/api/resume-improvements")
async def get_resume_improvements(request: JobMatchRequest) -> Dict:
    """Get personalized resume improvement suggestions."""
    
    if request.resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    resume_text = resume_storage[request.resume_id]["raw_text"]
    gap_analysis = skill_analyzer.analyze_gaps(
        resume_storage[request.resume_id]["processed"],
        request.job_description
    )
    
    try:
        improvements = resume_optimizer.generate_improvements(
            resume_text,
            request.job_description,
            gap_analysis
        )
        return improvements
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Improvement error: {str(e)}")


@app.post("/api/rewrite-bullets")
async def rewrite_bullet_points(
    resume_id: str,
    job_description: str = None
) -> Dict:
    """Rewrite bullet points with strong action verbs and metrics."""
    
    if resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Extract bullet points from experience section
    resume_data = resume_storage[resume_id]["processed"]
    experience_text = resume_data.get("sections", {}).get("experience", "")
    
    # Simple bullet extraction (improved in production)
    bullets = [line.strip() for line in experience_text.split("\n") if line.strip().startswith("•")]
    
    try:
        rewritten = resume_optimizer.rewrite_bullet_points(
            bullets,
            job_description
        )
        return rewritten
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rewrite error: {str(e)}")


@app.delete("/api/resume/{resume_id}")
async def delete_resume(resume_id: str) -> Dict:
    """Delete resume from storage."""
    
    if resume_id not in resume_storage:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    del resume_storage[resume_id]
    delete_resume_from_disk(resume_id)
    return {"status": "deleted", "resume_id": resume_id}

@app.post("/api/jobs/fetch")
async def fetch_jobs(
    background_tasks: BackgroundTasks,
    source: str = Query("remoteok", description="Job source: remoteok, linkedin, jsearch, indeed, glassdoor"),
    query: str = Query(None, description="Job search query (e.g., 'python developer', 'data scientist')"),
    tags: str = Query(None, description="Comma-separated tags for RemoteOK (e.g., python,javascript)"),
    location: str = Query("United States", description="Location filter"),
    remote_only: bool = Query(False, description="Filter for remote jobs only"),
    limit: int = Query(50, ge=1, le=100, description="Max jobs to fetch"),
    append: bool = Query(True, description="Append to existing jobs or replace")
) -> Dict:
    """
    Fetch jobs from external job search APIs and save to local database.
    
    Supports:
    - LinkedIn Job Search API (direct LinkedIn jobs) - requires RAPIDAPI_KEY
    - JSearch (aggregated jobs like Indeed / Glassdoor) - requires RAPIDAPI_KEY
    - RemoteOK (free, no auth required)
    
    This runs in the background and refreshes the job recommender when complete.
    """
    tags_list = [tag.strip() for tag in tags.split(",")] if tags else None
    
    def fetch_and_refresh():
        """Background task to fetch jobs and refresh recommender."""
        result = job_fetcher.fetch_and_save(
            source=source,
            tags=tags_list,
            query=query,
            location=location,
            remote_only=remote_only,
            limit=limit,
            append=append
        )
        
        # Refresh job recommender with new data
        if result.get("success"):
            job_recommender.refresh()
    
    # Run in background
    background_tasks.add_task(fetch_and_refresh)
    
    return {
        "status": "started",
        "message": f"Fetching jobs from {source} in background...",
        "source": source,
        "query": query,
        "location": location,
        "limit": limit
    }


@app.get("/api/jobs/sources")
async def get_job_sources() -> Dict:
    """Get available job search sources."""
    rapidapi_configured = bool(settings.RAPIDAPI_KEY)
    
    return {
        "sources": [
            {
                "name": "jsearch",
                "display_name": "JSearch (LinkedIn + Indeed + Glassdoor)",
                "description": "Aggregated jobs from multiple boards (Indeed, Glassdoor, etc.)",
                "requires_auth": True,
                "free": True,
                "free_tier_limit": "500 requests/month",
                "configured": rapidapi_configured,
                "setup_url": "https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch"
            },
            {
                "name": "linkedin",
                "display_name": "LinkedIn Jobs",
                "description": "Jobs from LinkedIn (via LinkedIn Job Search API)",
                "requires_auth": True,
                "free": True,
                "configured": rapidapi_configured,
                "note": "Uses linkedin-job-search-api.p.rapidapi.com backend"
            },
            {
                "name": "indeed",
                "display_name": "Indeed Jobs",
                "description": "Jobs from Indeed (via Indeed API)",
                "requires_auth": True,
                "free": True,
                "configured": rapidapi_configured,
                "note": "Uses indeed12.p.rapidapi.com backend"
            },
            {
                "name": "glassdoor",
                "display_name": "Glassdoor Jobs",
                "description": "Jobs from Glassdoor (via Glassdoor Real-Time API)",
                "requires_auth": True,
                "free": True,
                "configured": rapidapi_configured,
                "note": "Uses glassdoor-real-time.p.rapidapi.com backend"
            },
            {
                "name": "remoteok",
                "display_name": "RemoteOK",
                "description": "Remote jobs from RemoteOK.com",
                "requires_auth": False,
                "free": True,
                "configured": True
            }
        ],
        "recommended_queries": [
            "python developer", "data scientist", "machine learning engineer",
            "frontend developer", "backend engineer", "full stack developer",
            "devops engineer", "software engineer", "data analyst"
        ],
        "recommended_tags": [
            "python", "javascript", "react", "nodejs", "java", 
            "golang", "rust", "devops", "data", "machine-learning",
            "frontend", "backend", "fullstack"
        ]
    }



# Serve static web app files (MUST be last to not catch API routes)
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")


if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Fix for Windows asyncio issues
    if sys.platform == 'win32':
        import asyncio
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level="info",
        timeout_keep_alive=300  # 5 minutes for long-running LLM operations
    )
