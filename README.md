# Resume Analyzer - Production-Ready LLM Application

A sophisticated Resume Analysis platform combining **FastAPI**, **Streamlit**, **spaCy**, **FAISS**, and **LLMs** for intelligent resume processing and job matching.

## 🎯 Features

### Core Capabilities
- **Multi-format Resume Parsing**: PDF, DOCX, TXT support
- **NLP Processing**: Named entity extraction, skill detection, section identification
- **Semantic Search**: FAISS-powered vector search across resume corpus
- **AI Analysis**: GPT-powered resume insights and job matching
- **Job Matching**: Similarity scoring and gap analysis
- **🆕 LinkedIn/Indeed/Glassdoor Job Search**: Real-time job fetching via JSearch API
- **Job Recommendations**: AI-powered job matching based on resume
- **RESTful API**: FastAPI backend with full OpenAPI documentation
- **Web UI**: Modern dark-themed web interface

### Technical Highlights
- **Production Architecture**: Modular, scalable design
- **Vector Database**: FAISS for O(1) semantic search
- **LLM Integration**: OpenAI API with temperature control
- **Error Handling**: Comprehensive exception management
- **CORS Support**: Multi-origin API access
- **State Management**: Persistent vector store and resume cache

## 📁 Project Structure

```
ats/
├── backend/
│   ├── main.py              # FastAPI application
│   └── __init__.py
├── frontend/
│   ├── app.py               # Streamlit UI
│   └── __init__.py
├── core/
│   ├── nlp_pipeline.py      # Resume processing
│   ├── vector_store.py      # FAISS semantic search
│   ├── llm_analyzer.py      # LLM-powered analysis
│   └── __init__.py
├── utils/
│   ├── file_processor.py    # Multi-format parsing
│   ├── schemas.py           # Pydantic models
│   └── __init__.py
├── data/                    # Vector store and cached data
├── config.py                # Configuration management
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
└── README.md                # This file
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- OpenAI API Key (for AI analysis)
- RapidAPI Key (optional - for LinkedIn/Indeed/Glassdoor jobs)

### Installation

1. **Clone and setup**
```bash
cd ats
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys:
# - OPENAI_API_KEY (required for AI analysis)
# - RAPIDAPI_KEY (optional - for LinkedIn/Indeed/Glassdoor jobs)
```

**Get RapidAPI Key for Job Search** (optional but recommended):
- See [SETUP_JSEARCH.md](SETUP_JSEARCH.md) for detailed instructions
- Free tier: 500 requests/month
- Enables LinkedIn, Indeed, and Glassdoor job searches

### Running the Application

**Terminal 1 - Start FastAPI Backend**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Streamlit Frontend**
```bash
streamlit run frontend/app.py
```

Visit `http://localhost:8501` for the UI and `http://localhost:8000/docs` for API documentation.

## 📊 API Endpoints

### Resume Management
- `POST /api/upload` - Upload and process resume
- `GET /api/resume/{resume_id}` - Get extracted information
- `GET /api/resumes` - List all resumes
- `DELETE /api/resume/{resume_id}` - Delete resume

### Analysis
- `POST /api/analyze/{resume_id}` - AI-powered analysis
- `POST /api/match` - Resume-to-job matching
- `POST /api/search` - Semantic search

### Job Search & Recommendations
- `POST /api/jobs/fetch` - Fetch jobs from LinkedIn/Indeed/Glassdoor/RemoteOK
- `GET /api/jobs/sources` - Get available job sources
- `POST /api/jobs/recommend` - Get AI-powered job recommendations
- `GET /api/jobs/filters` - Get available filters (roles, locations, etc.)

### System
- `GET /api/health` - Health check

## 🔑 Key Components

### `nlp_pipeline.py`
**Purpose**: Resume text extraction and processing

**Key Methods**:
- `extract_contact_info()` - Extract emails, phones, URLs
- `extract_entities()` - Named entity recognition
- `extract_skills()` - Identify technical skills
- `chunk_text()` - Split for embeddings
- `get_key_sections()` - Identify resume sections

```python
pipeline = ResumePipeline()
result = pipeline.process_resume(resume_text)
# Returns: contact_info, entities, skills, sections, chunks
```

### `vector_store.py`
**Purpose**: Semantic search using FAISS

**Key Methods**:
- `add_vectors()` - Index embeddings with metadata
- `search()` - Find k-nearest neighbors
- `save()/load()` - Persist index

```python
store = VectorStore(dimension=384)
embeddings = embedding_service.embed_batch(chunks)
store.add_vectors(embeddings, metadata)
results = store.search(query_embedding, k=5)
```

### `llm_analyzer.py`
**Purpose**: LLM-powered resume analysis

**Key Methods**:
- `analyze_resume()` - Comprehensive analysis
- `match_resume_to_job()` - Job matching with scoring

```python
analyzer = ResumeLLMAnalyzer()
analysis = analyzer.analyze_resume(resume_text)
match = analyzer.match_resume_to_job(resume_text, job_description)
```

### `main.py`
**Purpose**: FastAPI backend orchestration

**Architecture**:
- Lifespan management for initialization
- CORS middleware for frontend communication
- In-memory resume storage with optional persistence
- Async request handling

## 🔧 Configuration

Edit `config.py` or `.env` for:
- **LLM Model**: Change from `gpt-3.5-turbo` to other models
- **Temperature**: Adjust LLM creativity (0.0-1.0)
- **Chunk Size**: Control embedding granularity
- **FAISS Dimension**: Match embedding model output

## 💾 Data Management

### Resume Storage
- Stored in-memory during session
- Persists between API requests
- Clear with DELETE endpoint

### Vector Index
- Automatically saved on shutdown
- Loaded on startup
- Location: `./data/resume_index.faiss`

## 🧪 Example Usage

### Upload Resume
```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@resume.pdf"
```

### Get Analysis
```bash
curl http://localhost:8000/api/analyze/{resume_id}
```

### Job Matching
```bash
curl -X POST http://localhost:8000/api/match \
  -H "Content-Type: application/json" \
  -d '{
    "resume_id": "uuid",
    "job_description": "We are looking for..."
  }'
```

## 📈 Performance Optimizations

- **FAISS**: O(1) search across thousands of resumes
- **Batch Embeddings**: Vectorize multiple chunks simultaneously
- **Async Processing**: Non-blocking API operations
- **In-Memory Cache**: Fast resume retrieval
- **Index Persistence**: Load pre-computed vectors instantly

## 🔐 Production Considerations

1. **API Key Management**: Use secure secrets management (AWS Secrets, Azure Key Vault)
2. **Rate Limiting**: Add to FastAPI with `slowapi`
3. **Authentication**: Implement JWT or OAuth
4. **Database**: Replace in-memory storage with PostgreSQL/MongoDB
5. **Logging**: Add structured logging with `loguru` or `structlog`
6. **Monitoring**: Use Prometheus/Grafana for metrics
7. **Deployment**: Docker containerization and Kubernetes orchestration

## 🛠️ Development

### Adding New Skills Detection
Edit `nlp_pipeline.py` in `extract_skills()`:
```python
common_skills = {
    # Add your custom skills here
    'your_skill', 'another_skill',
}
```

### Customizing Analysis Prompt
Modify `llm_analyzer.py` in `_build_analysis_prompt()` for different analysis styles.

### Extending Search
Implement filters in `vector_store.py` search for metadata-based filtering.

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| streamlit | UI framework |
| spacy | NLP processing |
| faiss-cpu | Vector search |
| openai | LLM integration |
| pydantic | Data validation |
| PyPDF2 | PDF parsing |
| python-docx | DOCX parsing |

## 🤝 Contributing

1. Follow PEP 8 style guide
2. Add docstrings to all functions
3. Include error handling
4. Update tests and documentation

## 📝 License

MIT License - See LICENSE file

## ⚡ Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| "Backend not running" | Start FastAPI: `python -m uvicorn backend.main:app --reload` |
| spaCy model missing | Run: `python -m spacy download en_core_web_sm` |
| FAISS dimension mismatch | Ensure embedding model matches FAISS dimension |
| API key errors | Verify OPENAI_API_KEY in .env |
| PDF parsing fails | Try with DOCX or TXT format |

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Streamlit API Reference](https://docs.streamlit.io/)
- [spaCy NLP Guide](https://spacy.io/usage)
- [FAISS Tutorial](https://github.com/facebookresearch/faiss/wiki)
- [LangChain Integration](https://python.langchain.com/)

---

**Built with ❤️ for production-grade AI applications**
