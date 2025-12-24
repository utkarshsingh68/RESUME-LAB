/* ============================================
   UI UTILITIES & COMPONENTS
   ============================================ */

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, duration);
}

/**
 * Show loading spinner
 */
function showLoading(show = true) {
    console.log(`[UI] showLoading(${show})`);
    const spinner = document.getElementById('loadingSpinner');
    if (spinner) {
        if (show) {
            spinner.style.display = 'flex';
        } else {
            spinner.style.display = 'none';
        }
    } else {
        console.error('[UI] loadingSpinner element not found!');
    }
}

/**
 * Update section visibility
 */
function switchSection(sectionId) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });

    // Show selected section
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.add('active');
    }

    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-section') === sectionId) {
            link.classList.add('active');
        }
    });

    // Scroll to top
    window.scrollTo(0, 0);
}

/**
 * Draw circular progress chart
 */
function drawCircularProgress(canvasId, score) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = 80;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 12;
    ctx.stroke();

    // Progress circle
    const percentage = Math.min(score / 100, 1);
    const endAngle = (Math.PI * 2 * percentage) - Math.PI / 2;

    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#6366f1');
    gradient.addColorStop(1, '#ec4899');

    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, -Math.PI / 2, endAngle);
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 12;
    ctx.lineCap = 'round';
    ctx.stroke();
}

/**
 * Animate number counter
 */
function animateCounter(element, target, duration = 1000) {
    if (!element) return;

    let current = 0;
    const increment = target / (duration / 16);
    const update = () => {
        current += increment;
        if (current < target) {
            element.textContent = Math.floor(current);
            requestAnimationFrame(update);
        } else {
            element.textContent = target;
        }
    };

    update();
}

/**
 * Update progress bar width
 */
function updateProgressBar(barId, percentage) {
    const bar = document.getElementById(barId);
    if (bar) {
        bar.style.width = Math.min(percentage, 100) + '%';
    }
}

/**
 * Create skill tag element
 */
function createSkillTag(skill, type = 'matched') {
    const tag = document.createElement('span');
    tag.className = `skill-tag ${type}`;
    tag.textContent = skill;
    return tag;
}

/**
 * Create gap item element
 */
function createGapItem(gap) {
    const item = document.createElement('div');
    item.className = `gap-item ${gap.category === 'CRITICAL' ? 'critical' : ''}`;

    const header = document.createElement('div');
    header.className = 'gap-header';

    const skillName = document.createElement('span');
    skillName.className = 'gap-skill';
    skillName.textContent = gap.skill;

    const priority = document.createElement('span');
    priority.className = 'gap-priority';
    priority.textContent = `Priority: ${gap.priority.toFixed(1)}x`;

    header.appendChild(skillName);
    header.appendChild(priority);

    const meta = document.createElement('div');
    meta.className = 'gap-meta';

    const category = document.createElement('span');
    category.innerHTML = `<strong>Category:</strong> ${gap.category}`;

    const frequency = document.createElement('span');
    frequency.innerHTML = `<strong>In Job:</strong> ${gap.frequency_in_job} times`;

    meta.appendChild(category);
    meta.appendChild(frequency);

    item.appendChild(header);
    item.appendChild(meta);

    if (gap.alternative_skills && gap.alternative_skills.length > 0) {
        const alternatives = document.createElement('div');
        alternatives.className = 'gap-alternatives';
        alternatives.innerHTML = `<strong>Alternatives:</strong> ${gap.alternative_skills.join(', ')}`;
        item.appendChild(alternatives);
    }

    return item;
}

/**
 * Create improvement item element
 */
function createImprovementItem(title, description) {
    const item = document.createElement('div');
    item.className = 'improvement-item';

    const heading = document.createElement('h4');
    heading.innerHTML = `<i class="fas fa-lightbulb"></i> ${title}`;

    const text = document.createElement('p');
    text.textContent = description;

    item.appendChild(heading);
    item.appendChild(text);

    return item;
}

/**
 * Create bullet comparison item
 */
function createBulletItem(original, improved) {
    const item = document.createElement('div');
    item.className = 'bullet-item';

    const originalEl = document.createElement('div');
    originalEl.className = 'bullet-original';
    originalEl.textContent = original || 'Original bullet point';

    const improvedEl = document.createElement('div');
    improvedEl.className = 'bullet-improved';
    improvedEl.textContent = improved || 'Improved version';

    item.appendChild(originalEl);
    item.appendChild(improvedEl);

    return item;
}

/**
 * Format analysis results for display
 */
function formatAnalysisResults(data) {
    return {
        atsScore: data.total_score || data.ats_score || 0,
        matchPercentage: data.match_percentage || 0,
        skillScore: data.breakdown?.skills || data.skill_breakdown?.skills || 0,
        experienceScore: data.breakdown?.experience || data.skill_breakdown?.experience || 0,
        keywordsScore: data.breakdown?.keywords || data.skill_breakdown?.keywords || 0,
        formattingScore: data.breakdown?.formatting || data.skill_breakdown?.formatting || 0,
        matchedSkills: data.matched_skills || [],
        missingSkills: (data.missing_skills || data.critical_gaps || []).map(skill => 
            typeof skill === 'string' ? skill : skill.skill
        )
    };
}

/**
 * Copy text to clipboard
 */
function copyToClipboard(text) {
    return navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

/**
 * Download file
 */
function downloadFile(content, filename, type = 'text/plain') {
    const blob = new Blob([content], { type });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
}

/**
 * Debounce function
 */
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func(...args), delay);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Format analysis percentage with color
 */
function getScoreColor(score) {
    if (score >= 80) return '#22c55e';
    if (score >= 60) return '#f59e0b';
    if (score >= 40) return '#f97316';
    return '#ef4444';
}

/**
 * Disable button
 */
function disableButton(buttonId, disable = true) {
    const btn = document.getElementById(buttonId);
    if (btn) {
        btn.disabled = disable;
        if (disable) {
            btn.style.opacity = '0.5';
        } else {
            btn.style.opacity = '1';
        }
    }
}

/**
 * Update chat message
 */
function addChatMessage(text, isUser = false) {
    const messagesContainer = document.getElementById('chatMessages');
    const message = document.createElement('div');
    message.className = `message ${isUser ? 'user-message' : 'assistant-message'}`;

    const content = document.createElement('div');
    content.className = 'message-content';
    content.innerHTML = `<p>${escapeHtml(text)}</p>`;

    message.appendChild(content);
    messagesContainer.appendChild(message);

    // Scroll to bottom
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

/**
 * Show typing indicator
 */
function showTypingIndicator(show = true) {
    const indicator = document.getElementById('chatIndicator');
    if (indicator) {
        indicator.style.display = show ? 'flex' : 'none';
    }
}

/**
 * Clear chat messages
 */
function clearChat() {
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.innerHTML = `
        <div class="message assistant-message">
            <div class="message-content">
                <p>Hi! 👋 I'm your AI resume assistant. Ask me anything about your resume.</p>
            </div>
        </div>
    `;
}

/**
 * Validate job description
 */
function validateJobDescription(jobDesc) {
    if (!jobDesc || jobDesc.trim().length < 50) {
        throw new Error('Please provide a detailed job description (at least 50 characters)');
    }
    return true;
}

/**
 * Update UI with analysis data
 */
function updateAnalysisUI(data) {
    // ATS Score
    document.getElementById('scoreNumber').textContent = Math.round(data.atsScore);
    animateCounter(document.getElementById('scoreNumber'), Math.round(data.atsScore), 800);
    drawCircularProgress('scoreCanvas', data.atsScore);

    // Component scores
    updateProgressBar('skillsScore', data.skillScore);
    document.getElementById('skillsPercent').textContent = Math.round(data.skillScore) + '%';

    updateProgressBar('experienceScore', data.experienceScore);
    document.getElementById('experiencePercent').textContent = Math.round(data.experienceScore) + '%';

    updateProgressBar('keywordsScore', data.keywordsScore);
    document.getElementById('keywordsPercent').textContent = Math.round(data.keywordsScore) + '%';

    updateProgressBar('formattingScore', data.formattingScore);
    document.getElementById('formattingPercent').textContent = Math.round(data.formattingScore) + '%';

    // Match percentage
    const matchPercent = Math.round(data.matchPercentage);
    document.getElementById('matchPercent').textContent = matchPercent + '%';

    // Update match circle
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (matchPercent / 100) * circumference;
    const matchCircle = document.getElementById('matchCircle');
    if (matchCircle) {
        matchCircle.style.strokeDashoffset = offset;
    }

    // Skills
    const matchedContainer = document.getElementById('matchedSkills');
    matchedContainer.innerHTML = '';
    if (data.matchedSkills && data.matchedSkills.length > 0) {
        data.matchedSkills.forEach(skill => {
            matchedContainer.appendChild(createSkillTag(skill, 'matched'));
        });
    } else {
        matchedContainer.innerHTML = '<p class="empty-state">No matched skills</p>';
    }

    const missingContainer = document.getElementById('missingSkills');
    missingContainer.innerHTML = '';
    if (data.missingSkills && data.missingSkills.length > 0) {
        data.missingSkills.forEach(skill => {
            // Handle both string and object formats
            const skillName = typeof skill === 'string' ? skill : skill.skill;
            missingContainer.appendChild(createSkillTag(skillName, 'missing'));
        });
    } else {
        missingContainer.innerHTML = '<p class="empty-state">All skills matched!</p>';
    }
}
