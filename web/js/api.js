/* ============================================
   API CONFIGURATION & UTILITY
   ============================================ */

// Use the current page origin so the UI and API stay on the same host/port.
const API_BASE_URL = `${window.location.origin}/api`;
const TIMEOUT = 120000; // 120 seconds for LLM operations

/**
 * Generic API request handler with error handling
 */
async function apiRequest(endpoint, options = {}) {
    const {
        method = 'GET',
        body = null,
        headers = {},
        timeout = TIMEOUT
    } = options;

    const config = {
        method,
        headers: {
            'Content-Type': 'application/json',
            ...headers
        }
    };

    if (body) {
        config.body = typeof body === 'string' ? body : JSON.stringify(body);
    }

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...config,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('Request timeout. Please try again.');
        }
        throw error;
    }
}

/**
 * Upload file to backend
 */
async function uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s for upload

        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || 'Upload failed');
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('Upload timeout. Please try again.');
        }
        throw error;
    }
}

/**
 * Analyze resume with job description
 */
async function analyzeResume(resumeId, jobDescription) {
    return apiRequest(`/analyze/${resumeId}`, {
        method: 'POST',
        body: {
            job_description: jobDescription
        }
    });
}

/**
 * Get ATS score
 */
async function getATSScore(resumeId, jobDescription) {
    return apiRequest('/ats-score', {
        method: 'POST',
        body: {
            resume_id: resumeId,
            job_description: jobDescription
        }
    });
}

/**
 * Get skill gaps analysis
 */
async function getSkillGaps(resumeId, jobDescription) {
    return apiRequest('/skill-gaps', {
        method: 'POST',
        body: {
            resume_id: resumeId,
            job_description: jobDescription
        }
    });
}

/**
 * Get resume improvements
 */
async function getImprovements(resumeId, jobDescription) {
    return apiRequest('/resume-improvements', {
        method: 'POST',
        body: {
            resume_id: resumeId,
            job_description: jobDescription
        }
    });
}

/**
 * Rewrite bullet points
 */
async function rewriteBullets(resumeId, jobDescription) {
    const params = new URLSearchParams({
        resume_id: resumeId,
        job_description: jobDescription
    });

    return apiRequest(`/rewrite-bullets?${params}`, {
        method: 'POST'
    });
}

/**
 * Chat with resume (RAG)
 */
async function chatWithResume(resumeId, question) {
    const params = new URLSearchParams({
        resume_id: resumeId,
        question: question
    });

    return apiRequest(`/resume-chat?${params}`, {
        method: 'POST'
    });
}

/**
 * Retrieve available job filters
 */
async function getJobFilters() {
    return apiRequest('/jobs/filters');
}

/**
 * Fetch recommended jobs for a resume
 */
async function getJobRecommendations(resumeId, filters = {}, topK = 100) {
    return apiRequest('/jobs/recommendations', {
        method: 'POST',
        body: {
            resume_id: resumeId,
            top_k: topK,
            filters
        },
        timeout: 180000 // 3 minutes for job recommendations with LLM
    });
}

/**
 * Retrieve raw fetched jobs (not personalized).
 */
async function getFetchedJobs(limit = 50, offset = 0) {
    const params = new URLSearchParams({
        limit: String(limit),
        offset: String(offset)
    });

    return apiRequest(`/jobs/list?${params}`, {
        method: 'GET'
    });
}

/**
 * Fetch jobs from web sources
 */
async function fetchJobsFromWeb(source, query, limit, append = true) {
    const params = new URLSearchParams({
        source: source,
        query: query || '',
        limit: limit || 25,
        append: append
    });
    
    return apiRequest(`/jobs/fetch?${params}`, {
        method: 'POST',
        timeout: 180000 // 3 minutes for scraping
    });
}

/**
 * Get available job sources
 */
async function getJobSources() {
    return apiRequest('/jobs/sources', {
        method: 'GET'
    });
}

/**
 * Health check
 */
async function healthCheck() {
    try {
        return await apiRequest('/health');
    } catch (error) {
        return null;
    }
}

/**
 * Store resume data in session
 */
function storeResumeData(key, value) {
    sessionStorage.setItem(key, JSON.stringify(value));
}

/**
 * Retrieve resume data from session
 */
function getResumeData(key) {
    const data = sessionStorage.getItem(key);
    return data ? JSON.parse(data) : null;
}

/**
 * Clear all resume data
 */
function clearResumeData() {
    sessionStorage.clear();
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Validate file
 */
function validateFile(file, maxSize = 10 * 1024 * 1024) {
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    
    if (!allowedTypes.includes(file.type)) {
        throw new Error('Invalid file type. Please upload PDF, DOCX, or TXT.');
    }
    
    if (file.size > maxSize) {
        throw new Error(`File too large. Maximum size is ${formatFileSize(maxSize)}`);
    }
    
    return true;
}

/**
 * Generate unique ID
 */
function generateId() {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Parse error message
 */
function parseError(error) {
    if (error instanceof Error) {
        return error.message;
    }
    if (typeof error === 'string') {
        return error;
    }
    if (error && error.detail) {
        return error.detail;
    }
    return 'An unexpected error occurred. Please try again.';
}
