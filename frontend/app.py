"""Production Streamlit frontend for Resume Analyzer."""
import streamlit as st
import requests
import json
from pathlib import Path
import os

# Configure page
st.set_page_config(
    page_title="Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_ENDPOINTS = {
    "health": f"{API_BASE_URL}/api/health",
    "upload": f"{API_BASE_URL}/api/upload",
    "resume_info": f"{API_BASE_URL}/api/resume",
    "analyze": f"{API_BASE_URL}/api/analyze",
    "match": f"{API_BASE_URL}/api/match",
    "search": f"{API_BASE_URL}/api/search",
    "list": f"{API_BASE_URL}/api/resumes",
}


# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 12px;
        border-radius: 4px;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 12px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


def check_api_health():
    """Check if backend API is running."""
    try:
        response = requests.get(API_ENDPOINTS["health"], timeout=2)
        return response.status_code == 200
    except:
        return False


def upload_resume(uploaded_file):
    """Upload resume file to backend."""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
        response = requests.post(API_ENDPOINTS["upload"], files=files)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Upload error: {str(e)}")
        return None


def get_resume_info(resume_id: str):
    """Fetch extracted resume information."""
    try:
        response = requests.get(f"{API_ENDPOINTS['resume_info']}/{resume_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Failed to fetch resume info")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def analyze_resume(resume_id: str):
    """Perform resume analysis."""
    try:
        response = requests.post(f"{API_ENDPOINTS['analyze']}/{resume_id}")
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Analysis failed")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def match_resume_to_job(resume_id: str, job_description: str):
    """Match resume to job description."""
    try:
        payload = {
            "resume_id": resume_id,
            "job_description": job_description
        }
        response = requests.post(API_ENDPOINTS["match"], json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Matching failed")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def search_resumes(query: str, top_k: int = 5):
    """Search resumes by semantic query."""
    try:
        payload = {"query": query, "top_k": top_k}
        response = requests.post(API_ENDPOINTS["search"], json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Search failed")
            return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None


def list_all_resumes():
    """Fetch list of all resumes."""
    try:
        response = requests.get(API_ENDPOINTS["list"])
        if response.status_code == 200:
            return response.json()
        else:
            return {"total_resumes": 0, "resumes": []}
    except:
        return {"total_resumes": 0, "resumes": []}


# Main App
st.title("📄 Resume Analyzer AI")
st.markdown("*Powered by FastAPI, spaCy, FAISS, and LLMs*")

# Check API health
if not check_api_health():
    st.error("⚠️ Backend API is not running. Please start the FastAPI server on http://localhost:8000")
    st.stop()

st.success("✅ Backend connected")

# Sidebar Navigation
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select Page",
        ["📤 Upload & Analyze", "📊 My Resumes", "🎯 Job Matching", "🔍 Search"]
    )

# ============= PAGE: Upload & Analyze =============
if page == "📤 Upload & Analyze":
    st.header("Upload Resume")
    
    uploaded_file = st.file_uploader(
        "Choose a resume file",
        type=["pdf", "docx", "txt"],
        help="Supported formats: PDF, DOCX, TXT"
    )
    
    if uploaded_file:
        st.info(f"📋 File: {uploaded_file.name}")
        
        if st.button("🚀 Upload & Process", key="upload_btn"):
            with st.spinner("Processing resume..."):
                result = upload_resume(uploaded_file)
                
                if result:
                    st.session_state.current_resume_id = result["resume_id"]
                    st.success(f"✅ Resume processed successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Tokens", result["token_count"])
                    with col2:
                        st.metric("Sections Found", len(result["sections"]))
                    with col3:
                        st.metric("Resume ID", result["resume_id"][:8])
                    
                    st.subheader("Extracted Sections")
                    st.write(result["sections"])
                    
                    # Get detailed info
                    st.divider()
                    st.subheader("📋 Detailed Information")
                    
                    with st.spinner("Extracting information..."):
                        info = get_resume_info(result["resume_id"])
                        
                        if info:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader("Contact Info")
                                if info["contact_info"]["emails"]:
                                    st.write("**Emails:**", info["contact_info"]["emails"])
                                if info["contact_info"]["phones"]:
                                    st.write("**Phones:**", info["contact_info"]["phones"])
                                if info["contact_info"]["urls"]:
                                    st.write("**URLs:**", info["contact_info"]["urls"])
                            
                            with col2:
                                st.subheader("Skills Found")
                                st.write(info["skills"] if info["skills"] else "No skills detected")
                            
                            st.subheader("Named Entities")
                            st.json(info["entities"])
                    
                    # AI Analysis
                    st.divider()
                    if st.button("🤖 Get AI Analysis", key="analyze_btn"):
                        with st.spinner("Running AI analysis..."):
                            analysis = analyze_resume(result["resume_id"])
                            if analysis:
                                st.subheader("AI Analysis Results")
                                st.markdown(analysis["analysis"])


# ============= PAGE: My Resumes =============
elif page == "📊 My Resumes":
    st.header("My Resumes")
    
    resumes_data = list_all_resumes()
    
    if resumes_data["total_resumes"] == 0:
        st.info("No resumes uploaded yet. Upload one first!")
    else:
        st.metric("Total Resumes", resumes_data["total_resumes"])
        
        st.subheader("Uploaded Resumes")
        for resume in resumes_data["resumes"]:
            with st.expander(f"📄 {resume['filename']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**ID:** {resume['resume_id'][:12]}...")
                    st.write(f"**Tokens:** {resume['token_count']}")
                
                with col2:
                    if st.button("📊 View Details", key=f"view_{resume['resume_id'][:8]}"):
                        st.session_state.current_resume_id = resume["resume_id"]
                        st.rerun()


# ============= PAGE: Job Matching =============
elif page == "🎯 Job Matching":
    st.header("Job Matching")
    
    resumes_data = list_all_resumes()
    
    if resumes_data["total_resumes"] == 0:
        st.warning("Please upload a resume first!")
    else:
        resume_options = {r["filename"]: r["resume_id"] for r in resumes_data["resumes"]}
        selected_resume = st.selectbox("Select Resume", list(resume_options.keys()))
        resume_id = resume_options[selected_resume]
        
        job_description = st.text_area(
            "Paste Job Description",
            height=300,
            placeholder="Paste the job description here..."
        )
        
        if st.button("🎯 Calculate Match", key="match_btn"):
            if job_description:
                with st.spinner("Analyzing match..."):
                    result = match_resume_to_job(resume_id, job_description)
                    
                    if result:
                        # Display match score prominently
                        match_score = result.get("match_score", 0)
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Match Score", f"{match_score}%")
                        
                        with col2:
                            st.metric("Strengths", len(result.get("strengths_for_role", [])))
                        
                        with col3:
                            st.metric("Missing Skills", len(result.get("missing_skills", [])))
                        
                        st.divider()
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("✅ Strengths for This Role")
                            for strength in result.get("strengths_for_role", []):
                                st.write(f"• {strength}")
                        
                        with col2:
                            st.subheader("⚠️ Missing Skills")
                            for skill in result.get("missing_skills", []):
                                st.write(f"• {skill}")
                        
                        st.subheader("💡 Recommendations")
                        for rec in result.get("recommendations", []):
                            st.info(rec)


# ============= PAGE: Search =============
elif page == "🔍 Search":
    st.header("Semantic Search")
    st.write("Search across all uploaded resumes using natural language")
    
    search_query = st.text_input(
        "Enter search query",
        placeholder="e.g., 'machine learning experience' or 'project management'"
    )
    top_k = st.slider("Number of results", 1, 20, 5)
    
    if st.button("🔍 Search", key="search_btn"):
        if search_query:
            with st.spinner("Searching..."):
                results = search_resumes(search_query, top_k=top_k)
                
                if results and results["results_count"] > 0:
                    st.success(f"Found {results['results_count']} results")
                    
                    for i, result in enumerate(results["results"], 1):
                        with st.expander(
                            f"Result {i} - Similarity: {result['similarity_score']:.2%}",
                            expanded=(i == 1)
                        ):
                            st.write(result["content"])
                            st.caption(f"Resume ID: {result['resume_id'][:12]}...")
                else:
                    st.info("No results found")
