/* ============================================
   MAIN APPLICATION LOGIC
   ============================================ */

let currentResumeId = null;
let currentJobDescription = '';
let currentAnalysisData = null;
let currentGapsData = null;
let currentImprovementsData = null;
let jobFiltersData = { roles: [], locations: [], experience_levels: [] };
let jobFilterSelections = { role: '', location: '', experience: '' };
let currentJobRecommendations = [];
let jobsSectionInitialized = false;
let jobFiltersLoading = false;
let jobTopK = 20;
let jobFiltersPromise = null;

/**
 * Enable or disable chat based on resume upload status
 */
function updateChatAvailability(hasResume) {
    const chatInput = document.getElementById('chatInput');
    const sendChatBtn = document.getElementById('sendChatBtn');
    
    if (chatInput && sendChatBtn) {
        chatInput.disabled = !hasResume;
        sendChatBtn.disabled = !hasResume;
        
        if (!hasResume) {
            chatInput.placeholder = 'Upload a resume first to enable chat...';
        } else {
            chatInput.placeholder = 'Ask about your experience, skills, or projects... Press Ctrl+Enter to send';
        }
    }
}

/**
 * Initialize application
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Resume Analyzer App Initializing...');
    
    initializeEventListeners();
    setupNavigation();
    setupDragDrop();
    initializeJobControls();
    loadJobFilters().catch(() => {});
    checkHealth();
    restoreSessionState();
    
    // Disable chat initially (will be re-enabled if session restored)
    updateChatAvailability(!!currentResumeId);
    updateJobSectionState();
});

/**
 * Setup navigation event listeners
 */
function setupNavigation() {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionId = link.getAttribute('data-section');
            switchSection(sectionId);
        });
    });

    // Mobile menu toggle
    const navToggle = document.querySelector('.nav-toggle');
    if (navToggle) {
        navToggle.addEventListener('click', () => {
            const navMenu = document.querySelector('.nav-menu');
            navMenu.style.display = navMenu.style.display === 'flex' ? 'none' : 'flex';
        });
    }
}

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // Upload events
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
    }

    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileSelect);
    }

    // Analyze button
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', handleAnalyze);
    }

    // Rewrite bullets button
    const rewriteBulletsBtn = document.getElementById('rewriteBulletsBtn');
    if (rewriteBulletsBtn) {
        rewriteBulletsBtn.addEventListener('click', handleRewriteBullets);
    }

    // Download resume button
    const downloadResumeBtn = document.getElementById('downloadResumeBtn');
    if (downloadResumeBtn) {
        downloadResumeBtn.addEventListener('click', handleDownloadResume);
    }

    // Copy bullets button
    const copyBulletsBtn = document.getElementById('copyBulletsBtn');
    if (copyBulletsBtn) {
        copyBulletsBtn.addEventListener('click', handleCopyBullets);
    }

    // Chat events
    const sendChatBtn = document.getElementById('sendChatBtn');
    if (sendChatBtn) {
        sendChatBtn.addEventListener('click', handleSendMessage);
    }

    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                handleSendMessage();
            }
        });
    }

    // Job description input
    const jobDescInput = document.getElementById('jobDescription');
    if (jobDescInput) {
        jobDescInput.addEventListener('input', (e) => {
            currentJobDescription = e.target.value;
        });
    }

    // Job recommendation filters
    const jobRoleFilter = document.getElementById('jobRoleFilter');
    if (jobRoleFilter) {
        jobRoleFilter.addEventListener('change', (e) => handleJobFilterChange('role', e.target.value));
    }

    const jobLocationFilter = document.getElementById('jobLocationFilter');
    if (jobLocationFilter) {
        jobLocationFilter.addEventListener('change', (e) => handleJobFilterChange('location', e.target.value));
    }

    const jobExperienceFilter = document.getElementById('jobExperienceFilter');
    if (jobExperienceFilter) {
        jobExperienceFilter.addEventListener('change', (e) => handleJobFilterChange('experience', e.target.value));
    }

    // Top K filter removed - shows all matching jobs

    const jobRefreshBtn = document.getElementById('jobRefreshBtn');
    if (jobRefreshBtn) {
        jobRefreshBtn.addEventListener('click', () => fetchJobRecommendations(true));
    }
}

/**
 * Setup drag and drop
 */
function setupDragDrop() {
    const dropZone = document.getElementById('dropZone');
    if (!dropZone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', handleDrop, false);
}

/**
 * Prevent default drag behavior
 */
function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

/**
 * Handle file drop
 */
function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        handleFileSelect({ target: { files } });
    }
}

/**
 * Handle file selection
 */
async function handleFileSelect(event) {
    const files = event.target.files;
    if (files.length === 0) return;

    const file = files[0];

    try {
        validateFile(file);
        console.log('[Upload] Starting file upload:', file.name);
        showLoading(true);

        const result = await uploadResume(file);
        console.log('[Upload] Upload successful, resumeId:', result.resume_id);
        currentResumeId = result.resume_id;

        // Store resume data
        storeResumeData('resumeId', currentResumeId);
        storeResumeData('fileName', file.name);
        
        // Enable chat now that resume is uploaded
        updateChatAvailability(true);
        updateJobSectionState();
        fetchJobRecommendations(true);

        showToast(`Resume uploaded successfully: ${file.name}`, 'success');
        
        // Update UI
        const dropZone = document.getElementById('dropZone');
        const progressDiv = document.getElementById('uploadProgress');
        
        dropZone.innerHTML = `
            <div style="text-align: center; padding: 20px;">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">✓</div>
                <p style="font-size: 1.1rem; margin-bottom: 5px;">File uploaded successfully</p>
                <p style="color: var(--text-secondary);">${file.name}</p>
                <p style="color: var(--text-tertiary); font-size: 0.9rem; margin-top: 10px;">
                    ${formatFileSize(file.size)} • Ready for analysis
                </p>
            </div>
        `;

        progressDiv.style.display = 'none';
        console.log('[Upload] UI updated - hiding spinner');

    } catch (error) {
        console.error('[Upload] Error:', error);
        showToast(parseError(error), 'error');
    } finally {
        console.log('[Upload] Finally block - hiding spinner');
        showLoading(false);
    }
}

function initializeJobControls() {
    // Top K filter removed - now shows all matching jobs
    jobTopK = 20;
}

async function loadJobFilters() {
    if (jobFiltersPromise) {
        return jobFiltersPromise;
    }

    jobFiltersLoading = true;

    jobFiltersPromise = (async () => {
        try {
            const filters = await getJobFilters();
            jobFiltersData = {
                roles: (filters && Array.isArray(filters.roles)) ? filters.roles : [],
                locations: (filters && Array.isArray(filters.locations)) ? filters.locations : [],
                experience_levels: (filters && Array.isArray(filters.experience_levels)) ? filters.experience_levels : []
            };

            populateJobFilterSelect('jobRoleFilter', jobFiltersData.roles, 'All roles', 'role');
            populateJobFilterSelect('jobLocationFilter', jobFiltersData.locations, 'All locations', 'location');
            populateJobFilterSelect('jobExperienceFilter', jobFiltersData.experience_levels, 'All levels', 'experience');
            jobsSectionInitialized = true;
            return jobFiltersData;
        } catch (error) {
            console.warn('Failed to load job filters', error);
            showToast('Unable to load job filters. Please try again later.', 'error');
            throw error;
        } finally {
            jobFiltersLoading = false;
        }
    })();

    try {
        return await jobFiltersPromise;
    } catch (error) {
        jobFiltersPromise = null;
        throw error;
    }
}

function populateJobFilterSelect(elementId, options, placeholder, key) {
    const select = document.getElementById(elementId);
    if (!select) return;

    select.innerHTML = '';

    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = placeholder;
    select.appendChild(defaultOption);

    (options || []).forEach(option => {
        const opt = document.createElement('option');
        opt.value = option;
        opt.textContent = option;
        select.appendChild(opt);
    });

    if (key && jobFilterSelections[key]) {
        select.value = jobFilterSelections[key];
    }
}

function handleJobFilterChange(key, value) {
    jobFilterSelections[key] = value;
    fetchJobRecommendations();
}

function updateJobSectionState() {
    const emptyState = document.getElementById('jobEmptyState');
    const recommendations = document.getElementById('jobRecommendations');

    if (!emptyState || !recommendations) return;

    if (!currentResumeId) {
        emptyState.style.display = 'block';
        recommendations.innerHTML = '';
    } else {
        emptyState.style.display = 'none';
    }
}

function setJobSectionMessage(message, variant = 'info') {
    const recommendations = document.getElementById('jobRecommendations');
    if (!recommendations) return;

    recommendations.innerHTML = '';

    const card = document.createElement('div');
    card.className = 'glass-card job-empty';

    const heading = document.createElement('h3');
    const icon = document.createElement('i');
    icon.className = `fas ${variant === 'error' ? 'fa-triangle-exclamation' : 'fa-lightbulb'}`;
    heading.appendChild(icon);
    heading.appendChild(document.createTextNode(` ${message}`));
    card.appendChild(heading);

    recommendations.appendChild(card);
}

function setJobLoading(isLoading) {
    const refreshBtn = document.getElementById('jobRefreshBtn');
    if (refreshBtn) {
        refreshBtn.disabled = isLoading;
        refreshBtn.innerHTML = isLoading
            ? '<i class="fas fa-spinner fa-spin"></i> Fetching...'
            : '<i class="fas fa-sync"></i> Refresh Recommendations';
    }

    if (isLoading) {
        const recommendations = document.getElementById('jobRecommendations');
        if (recommendations) {
            recommendations.innerHTML = '<div class="glass-card job-loading">Generating personalized job matches...</div>';
        }
    }
}

function mapApplyBadge(status) {
    switch ((status || '').toLowerCase()) {
        case 'ready':
            return 'apply-ready';
        case 'partial':
            return 'apply-partial';
        default:
            return 'apply-upskill';
    }
}

function createProgressItem(label, value, type) {
    const clampedValue = Math.max(0, Math.min(value, 1));
    const percent = Math.round(clampedValue * 100);

    const item = document.createElement('div');
    item.className = 'job-progress-item';

    const labelRow = document.createElement('div');
    labelRow.className = 'job-progress-label';

    const labelText = document.createElement('span');
    labelText.textContent = label;

    const valueText = document.createElement('span');
    valueText.textContent = `${percent}%`;

    labelRow.appendChild(labelText);
    labelRow.appendChild(valueText);

    const bar = document.createElement('div');
    bar.className = 'job-progress-bar';

    const fill = document.createElement('div');
    fill.className = `job-progress-fill ${type}`;
    fill.style.width = `${percent}%`;

    bar.appendChild(fill);

    item.appendChild(labelRow);
    item.appendChild(bar);

    return item;
}

function renderJobRecommendations(jobs) {
    const recommendations = document.getElementById('jobRecommendations');
    if (!recommendations) return;

    recommendations.innerHTML = '';

    if (!jobs || jobs.length === 0) {
        const card = document.createElement('div');
        card.className = 'glass-card job-empty';

        const heading = document.createElement('h3');
        const icon = document.createElement('i');
        icon.className = 'fas fa-briefcase';
        heading.appendChild(icon);
        heading.appendChild(document.createTextNode(' No matching roles found'));

        const body = document.createElement('p');
        body.textContent = 'Adjust filters or update your resume to see new matches.';

        card.appendChild(heading);
        card.appendChild(body);
        recommendations.appendChild(card);
        return;
    }

    const fragment = document.createDocumentFragment();

    jobs.forEach(job => {
        const card = document.createElement('div');
        card.className = 'glass-card job-card';

        const header = document.createElement('div');
        header.className = 'job-card-header';

        const info = document.createElement('div');

        const titleEl = document.createElement('h3');
        titleEl.className = 'job-title';
        titleEl.textContent = job.title || 'Untitled Role';

        const companyEl = document.createElement('div');
        companyEl.className = 'job-company';
        const companyName = job.company || 'Unknown company';
        const locationLabel = job.location || 'Remote';
        companyEl.textContent = `${companyName} • ${locationLabel}`;

        info.appendChild(titleEl);
        info.appendChild(companyEl);

        const badge = document.createElement('div');
        badge.className = `apply-badge ${mapApplyBadge(job.apply_readiness)}`;
        badge.textContent = job.apply_readiness || 'Needs Review';

        header.appendChild(info);
        header.appendChild(badge);
        card.appendChild(header);

        const summary = document.createElement('div');
        summary.className = 'job-match-summary';

        const score = document.createElement('div');
        score.className = 'match-score';
        const matchValue = Math.round(job.match_percentage || 0);
        score.innerHTML = `${matchValue}<span>% match</span>`;

        summary.appendChild(score);

        const progressList = document.createElement('div');
        progressList.className = 'job-progress-list';
        progressList.appendChild(createProgressItem('Semantic fit', job.similarity || 0, 'semantic'));
        progressList.appendChild(createProgressItem('Skill overlap', job.skill_overlap || 0, 'skills'));
        progressList.appendChild(createProgressItem('Experience alignment', job.experience_alignment || 0, 'experience'));

        summary.appendChild(progressList);
        card.appendChild(summary);

        const skillsRow = document.createElement('div');
        skillsRow.className = 'job-skills';

        (job.matched_skills || []).slice(0, 6).forEach(skill => {
            const chip = document.createElement('span');
            chip.className = 'job-skill-chip';
            chip.textContent = skill;
            skillsRow.appendChild(chip);
        });

        (job.missing_skills || []).slice(0, 4).forEach(skill => {
            const chip = document.createElement('span');
            chip.className = 'job-skill-chip job-missing-chip';
            chip.textContent = skill;
            skillsRow.appendChild(chip);
        });

        if (skillsRow.childNodes.length > 0) {
            card.appendChild(skillsRow);
        }

        const highlights = Array.isArray(job.highlights) ? job.highlights : [];
        if (highlights.length > 0) {
            const highlightsList = document.createElement('ul');
            highlightsList.className = 'job-highlights';

            highlights.forEach(item => {
                const li = document.createElement('li');
                const icon = document.createElement('i');
                icon.className = 'fas fa-star';
                const text = document.createElement('span');
                text.textContent = item;
                li.appendChild(icon);
                li.appendChild(text);
                highlightsList.appendChild(li);
            });

            card.appendChild(highlightsList);
        }

        if (job.explanation) {
            const explanation = document.createElement('p');
            explanation.className = 'job-explanation';
            explanation.textContent = job.explanation;
            card.appendChild(explanation);
        }

        const footer = document.createElement('div');
        footer.className = 'job-card-footer';

        const meta = document.createElement('div');
        const details = [];
        if (job.role) details.push(job.role);
        if (job.employment_type) details.push(job.employment_type);
        if (job.experience_level) details.push(`${job.experience_level} level`);
        meta.textContent = details.join(' • ') || 'Role details not provided';

        footer.appendChild(meta);

        if (job.apply_url) {
            const link = document.createElement('a');
            link.href = job.apply_url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            link.innerHTML = 'View job posting <i class="fas fa-arrow-up-right-from-square"></i>';
            footer.appendChild(link);
        }

        card.appendChild(footer);

        fragment.appendChild(card);
    });

    recommendations.appendChild(fragment);
}

async function fetchJobRecommendations(showUploadToast = false) {
    if (!currentResumeId) {
        if (showUploadToast) {
            showToast('Upload a resume to unlock job recommendations.', 'warning');
        }
        updateJobSectionState();
        return;
    }

    try {
        await loadJobFilters();
    } catch (error) {
        console.warn('Continuing without job filters', error);
    }

    updateJobSectionState();
    setJobLoading(true);

    try {
        const filters = {
            roles: jobFilterSelections.role ? [jobFilterSelections.role] : [],
            locations: jobFilterSelections.location ? [jobFilterSelections.location] : [],
            experience_levels: jobFilterSelections.experience ? [jobFilterSelections.experience] : []
        };

        const response = await getJobRecommendations(currentResumeId, filters, jobTopK);
        currentJobRecommendations = response.jobs || [];

        updateJobSectionState();
        renderJobRecommendations(currentJobRecommendations);

        if (currentJobRecommendations.length === 0 && showUploadToast) {
            showToast('No matching jobs found. Try adjusting filters.', 'info');
        }
    } catch (error) {
        const message = parseError(error);
        console.error('Job recommendation error:', error);

        // If the server was restarted, in-memory resumes are cleared.
        // The UI may still have an old resume_id in sessionStorage.
        if (typeof message === 'string' && message.toLowerCase().includes('resume not found')) {
            clearResumeData();
            currentResumeId = null;
            currentAnalysisData = null;
            currentGapsData = null;
            currentImprovementsData = null;
            currentJobRecommendations = [];

            updateChatAvailability(false);
            updateJobSectionState();
            setJobSectionMessage('Session expired. Please upload your resume again.', 'warning');
            showToast('Session expired. Please upload your resume again.', 'warning');
            return;
        }

        showToast(message, 'error');
        setJobSectionMessage('We could not generate recommendations right now. Try again shortly.', 'error');
    } finally {
        setJobLoading(false);
    }
}

function restoreSessionState() {
    const storedResumeId = getResumeData('resumeId');
    if (!storedResumeId) {
        return;
    }

    currentResumeId = storedResumeId;
    updateChatAvailability(true);
    updateJobSectionState();

    const storedAnalysis = getResumeData('analysisData');
    if (storedAnalysis) {
        currentAnalysisData = storedAnalysis;
        updateAnalysisDisplay();
    }

    const storedGaps = getResumeData('gapsData');
    if (storedGaps) {
        currentGapsData = storedGaps;
    }

    const storedImprovements = getResumeData('improvementsData');
    if (storedImprovements) {
        currentImprovementsData = storedImprovements;
    }

    fetchJobRecommendations();
}

/**
 * Handle resume analysis
 */
async function handleAnalyze() {
    if (!currentResumeId) {
        showToast('Please upload a resume first', 'warning');
        switchSection('upload');
        return;
    }

    const jobDesc = document.getElementById('jobDescription').value;

    try {
        validateJobDescription(jobDesc);
        showLoading(true);
        console.log('[Analyze] Starting parallel API calls...');

        const [atsData, gapsData, improvementsData] = await Promise.all([
            getATSScore(currentResumeId, jobDesc),
            getSkillGaps(currentResumeId, jobDesc),
            getImprovements(currentResumeId, jobDesc)
        ]);

        console.log('[Analyze] All API calls completed');
        currentAnalysisData = atsData;
        currentGapsData = gapsData;
        currentImprovementsData = improvementsData;

        // Store data
        storeResumeData('analysisData', currentAnalysisData);
        storeResumeData('gapsData', currentGapsData);
        storeResumeData('improvementsData', currentImprovementsData);

        // Update UI
        updateAnalysisDisplay();

        // Switch to analysis section
        switchSection('analysis');
        showToast('Analysis complete!', 'success');
        console.log('[Analyze] Success - hiding spinner');

    } catch (error) {
        console.error('[Analyze] Error:', error);
        showToast(parseError(error), 'error');
    } finally {
        console.log('[Analyze] Finally block - hiding spinner');
        showLoading(false);
    }
}

/**
 * Update analysis display
 */
function updateAnalysisDisplay() {
    if (!currentAnalysisData) return;

    const formattedData = formatAnalysisResults(currentAnalysisData);
    updateAnalysisUI(formattedData);

    // Update skill gaps
    const gapsContainer = document.getElementById('skillGaps');
    gapsContainer.innerHTML = '';

    if (currentGapsData && currentGapsData.critical_gaps) {
        currentGapsData.critical_gaps.forEach(gap => {
            gapsContainer.appendChild(createGapItem(gap));
        });
    }

    if (!gapsContainer.hasChildNodes()) {
        gapsContainer.innerHTML = '<p class="empty-state">No critical skill gaps identified!</p>';
    }

    // Show rewrite button
    const rewriteBtn = document.getElementById('rewriteBulletsBtn');
    if (rewriteBtn) {
        rewriteBtn.style.display = 'block';
    }
}

/**
 * Handle rewrite bullets
 */
async function handleRewriteBullets() {
    if (!currentResumeId) return;

    const jobDesc = document.getElementById('jobDescription').value;

    try {
        showLoading(true);

        const rewriteData = await rewriteBullets(currentResumeId, jobDesc);

        // Display rewritten bullets
        const bulletsContainer = document.getElementById('rewrittenBullets');
        bulletsContainer.innerHTML = '';

        if (rewriteData.rewritten_bullets && rewriteData.rewritten_bullets.length > 0) {
            rewriteData.rewritten_bullets.forEach((bullet, index) => {
                const original = currentAnalysisData?.matched_skills?.[index] || 'Original bullet point';
                bulletsContainer.appendChild(createBulletItem(original, bullet));
            });
        }

        // Show action buttons
        const actionDiv = document.getElementById('bulletActions');
        if (actionDiv) {
            actionDiv.style.display = 'flex';
        }

        switchSection('optimize');
        showToast('Bullets rewritten successfully!', 'success');

    } catch (error) {
        showToast(parseError(error), 'error');
    } finally {
        showLoading(false);
    }
}

/**
 * Handle download optimized resume
 */
async function handleDownloadResume() {
    try {
        const fileName = getResumeData('fileName') || 'resume-optimized.txt';
        const baseFileName = fileName.split('.')[0];
        
        // Collect all improvements and optimized content
        const content = generateResumeContent();
        
        downloadFile(content, `${baseFileName}-optimized.txt`, 'text/plain');
        showToast('Resume downloaded!', 'success');

    } catch (error) {
        showToast(parseError(error), 'error');
    }
}

/**
 * Generate optimized resume content
 */
function generateResumeContent() {
    let content = '=== OPTIMIZED RESUME ===\n\n';

    if (currentAnalysisData) {
        content += `ATS SCORE: ${currentAnalysisData.total_score}/100\n`;
        content += `Job Match: ${currentAnalysisData.match_percentage}%\n\n`;

        content += 'SCORE BREAKDOWN:\n';
        content += `- Skills Match: ${currentAnalysisData.breakdown?.skills || 0}%\n`;
        content += `- Experience: ${currentAnalysisData.breakdown?.experience || 0}%\n`;
        content += `- Keywords: ${currentAnalysisData.breakdown?.keywords || 0}%\n`;
        content += `- Formatting: ${currentAnalysisData.breakdown?.formatting || 0}%\n\n`;
    }

    if (currentAnalysisData?.matched_skills) {
        content += 'MATCHED SKILLS:\n';
        currentAnalysisData.matched_skills.forEach(skill => {
            content += `• ${skill}\n`;
        });
        content += '\n';
    }

    if (currentImprovementsData) {
        content += 'IMPROVEMENT SUGGESTIONS:\n';
        content += `${currentImprovementsData.ats_optimization}\n\n`;
    }

    const rewrittenBullets = document.querySelectorAll('.bullet-improved');
    if (rewrittenBullets.length > 0) {
        content += 'OPTIMIZED BULLET POINTS:\n';
        rewrittenBullets.forEach(bullet => {
            content += `• ${bullet.textContent}\n`;
        });
        content += '\n';
    }

    return content;
}

/**
 * Handle copy bullets to clipboard
 */
async function handleCopyBullets() {
    try {
        const bullets = [];
        document.querySelectorAll('.bullet-improved').forEach(bullet => {
            bullets.push(bullet.textContent);
        });

        if (bullets.length === 0) {
            showToast('No bullets to copy', 'warning');
            return;
        }

        const text = bullets.join('\n');
        await copyToClipboard(text);

    } catch (error) {
        showToast(parseError(error), 'error');
    }
}

/**
 * Handle send chat message
 */
async function handleSendMessage() {
    const chatInput = document.getElementById('chatInput');
    const question = chatInput.value.trim();

    if (!question) return;

    if (!currentResumeId) {
        showToast('Please upload a resume first', 'warning');
        return;
    }

    try {
        // Add user message
        addChatMessage(question, true);
        chatInput.value = '';

        // Show typing indicator
        showTypingIndicator(true);

        // Get answer
        const response = await chatWithResume(currentResumeId, question);

        showTypingIndicator(false);

        // Add assistant response
        addChatMessage(response.answer, false);

        if (response.confidence < 0.7) {
            showToast(
                `Confidence: ${(response.confidence * 100).toFixed(0)}% - Answer may have limited context`,
                'warning'
            );
        }

    } catch (error) {
        showTypingIndicator(false);
        showToast(parseError(error), 'error');
        addChatMessage('Sorry, I encountered an error. Please try again.', false);
    }
}

/**
 * Check API health
 */
async function checkHealth() {
    try {
        const health = await healthCheck();
        if (!health) {
            showToast('Backend server is not running. Please start the FastAPI server.', 'error');
        } else {
            console.log('✓ Backend connected');
        }
    } catch (error) {
        console.warn('Health check failed:', error);
    }
}

/**
 * Initialize improvements display
 */
function displayImprovements() {
    const improvementsContainer = document.getElementById('improvements');
    improvementsContainer.innerHTML = '';

    if (!currentImprovementsData) return;

    if (currentImprovementsData.ats_optimization) {
        improvementsContainer.appendChild(
            createImprovementItem(
                'ATS Optimization',
                currentImprovementsData.ats_optimization
            )
        );
    }

    if (currentImprovementsData.content_improvements) {
        improvementsContainer.appendChild(
            createImprovementItem(
                'Content Improvements',
                currentImprovementsData.content_improvements
            )
        );
    }

    if (currentImprovementsData.formatting_tips) {
        improvementsContainer.appendChild(
            createImprovementItem(
                'Formatting Tips',
                currentImprovementsData.formatting_tips
            )
        );
    }

    if (currentImprovementsData.action_items) {
        const actionList = currentImprovementsData.action_items
            .map(item => `• ${item}`)
            .join('\n');
        improvementsContainer.appendChild(
            createImprovementItem(
                'Action Items',
                actionList
            )
        );
    }
}

// Update improvements display when switching to optimize section
document.addEventListener('DOMContentLoaded', () => {
    const originalSwitchSection = window.switchSection;
    window.switchSection = function(sectionId) {
        originalSwitchSection(sectionId);
        if (sectionId === 'optimize' && currentImprovementsData) {
            displayImprovements();
        }
    };
});

console.log('Resume Analyzer App Loaded');
