// Integrated Frontend-Backend Script for Radiological Threat Detection System
// This replaces the existing script.js with full API integration

// Global variables
let authToken = null;
let currentUser = null;
let currentSpectrumData = null;
let spectrumChart = null;
let isLiveModeActive = false;
let liveModeInterval = null;
let systemStartTime = Date.now();
let totalScans = 0;
let threatsDetected = 0;
let analysisInProgress = false;
let currentAnalysisSession = null;

// Authentication Guard - Check if user is logged in
function checkAuthentication() {
    console.log('🔐 Checking authentication...');
    
    // Don't redirect if we're already on the login page
    const currentPage = window.location.pathname;
    const isLoginPage = currentPage.includes('login.html') || currentPage.includes('debug_auth.html');
    
    console.log('Current page:', currentPage);
    console.log('Is login page:', isLoginPage);
    
    // Check localStorage first (remember me), then sessionStorage
    const localToken = localStorage.getItem('authToken');
    const sessionToken = sessionStorage.getItem('authToken');
    authToken = localToken || sessionToken;
    
    const localUserInfo = localStorage.getItem('userInfo');
    const sessionUserInfo = sessionStorage.getItem('userInfo');
    const userInfo = localUserInfo || sessionUserInfo;
    
    console.log('Local token:', localToken ? 'exists' : 'null');
    console.log('Session token:', sessionToken ? 'exists' : 'null');
    console.log('Final token:', authToken ? 'exists' : 'null');
    console.log('User info:', userInfo ? 'exists' : 'null');
    
    if (!authToken) {
        console.log('❌ No token found');
        if (!isLoginPage) {
            console.log('🔄 Redirecting to login...');
            window.location.href = 'login.html';
        }
        return false;
    }
    
    if (userInfo) {
        try {
            currentUser = JSON.parse(userInfo);
            console.log('✅ User info parsed successfully:', currentUser);
        } catch (e) {
            console.error('❌ Error parsing user info:', e);
            console.log('Raw user info:', userInfo);
            // Clear corrupted data
            localStorage.removeItem('authToken');
            localStorage.removeItem('userInfo');
            sessionStorage.removeItem('authToken');
            sessionStorage.removeItem('userInfo');
            if (!isLoginPage) {
                window.location.href = 'login.html';
            }
            return false;
        }
    }
    
    console.log('✅ Authentication check passed');
    return true;
}

// Logout function
function logout() {
    console.log('🚪 Logging out user...');
    
    // Clear all stored authentication data
    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('userInfo');
    
    // Reset global variables
    authToken = null;
    currentUser = null;
    
    console.log('✅ Authentication data cleared');
    
    // Redirect to login page
    window.location.href = 'login.html';
    console.log('🔄 Redirecting to login page...');
}

// API Configuration
const API_BASE_URL = 'http://localhost:5000/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Check authentication first - redirect to login if not authenticated
    if (!checkAuthentication()) {
        return; // Exit early if not authenticated
    }
    
    initializeApp();
    setupEventListeners();
    updateSystemStats();
    
    // Update UI for authenticated user
    if (authToken && currentUser) {
        updateUIForAuthenticatedUser();
        loadDashboardData();
    } else {
        showLoginModal();
    }
    
    // Start system uptime counter
    setInterval(updateSystemUptime, 1000);
});

// Synthetic spectrum generation function
function generateSpectrum() {
    const isotopeSelect = document.getElementById('isotopeSelect');
    const noiseLevel = document.getElementById('noiseLevel');
    
    if (!isotopeSelect || !noiseLevel) {
        showNotification('Generator controls not found', 'error');
        return;
    }
    
    const isotope = isotopeSelect.value;
    const noise = parseInt(noiseLevel.value);
    
    // Generate synthetic spectrum data
    const energyRange = Array.from({length: 1000}, (_, i) => i * 3); // 0-3000 keV
    let spectrum = new Array(1000).fill(0);
    
    // Add isotope-specific peaks
    const isotopeData = {
        'K-40': [1460.8],
        'Cs-137': [661.7],
        'Co-60': [1173.2, 1332.5],
        'U-238': [186.2, 1001.0],
        'mixed': [661.7, 1173.2, 1460.8]
    };
    
    const peaks = isotopeData[isotope] || [661.7];
    
    // Add peaks with Gaussian shape
    peaks.forEach(peakEnergy => {
        const peakIndex = Math.floor(peakEnergy / 3);
        const sigma = 20; // Peak width
        const amplitude = 1000 / noise; // Inverse noise level
        
        for (let i = 0; i < spectrum.length; i++) {
            const energy = i * 3;
            const gaussian = amplitude * Math.exp(-Math.pow(energy - peakEnergy, 2) / (2 * sigma * sigma));
            spectrum[i] += gaussian;
        }
    });
    
    // Add background noise
    const backgroundLevel = 10 * noise;
    spectrum = spectrum.map(count => count + Math.random() * backgroundLevel);
    
    // Update chart
    currentSpectrumData = {
        energies: energyRange,
        counts: spectrum,
        isotope: isotope,
        noise_level: noise
    };
    
    updateSpectrumChart(energyRange, spectrum);
    updateFileInfo(`Synthetic ${isotope}`, `${spectrum.length} points`, spectrum.reduce((a, b) => a + b, 0));
    
    // Enable analysis button
    const runBtn = document.getElementById('runAnalysisBtn');
    if (runBtn) runBtn.disabled = false;
    
    showNotification(`Generated ${isotope} spectrum with noise level ${noise}`, 'success');
    addLogEntry('INFO', `Generated synthetic spectrum: ${isotope}`);
}

function initializeApp() {
    // Initialize Chart.js
    const ctx = document.getElementById('spectrumChart').getContext('2d');
    spectrumChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Counts',
                data: [],
                borderColor: '#00ff88',
                backgroundColor: 'rgba(0, 255, 136, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { color: '#e0e0e0' }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Energy (keV)', color: '#00ccff' },
                    ticks: { color: '#888' },
                    grid: { color: '#333' }
                },
                y: {
                    title: { display: true, text: 'Counts', color: '#00ccff' },
                    ticks: { color: '#888' },
                    grid: { color: '#333' }
                }
            }
        }
    });
}

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const tabName = e.target.dataset.tab;
            if (tabName) showTab(tabName);
        });
    });

    // File upload
    const fileInput = document.getElementById('fileInput');
    const fileUploadArea = document.querySelector('.file-upload-area');
    
    if (fileUploadArea && fileInput) {
        fileUploadArea.addEventListener('click', () => fileInput.click());
        fileUploadArea.addEventListener('dragover', handleDragOver);
        fileUploadArea.addEventListener('drop', handleFileDrop);
        fileInput.addEventListener('change', handleFileUpload);
    }

    // Synthetic spectrum generation
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateSyntheticSpectrum);
    }
    
    // Analysis
    const runAnalysisBtn = document.getElementById('runAnalysisBtn');
    if (runAnalysisBtn) {
        runAnalysisBtn.addEventListener('click', runAnalysis);
    }
    
    // Live mode
    const liveModeToggle = document.getElementById('liveModeToggle');
    if (liveModeToggle) {
        liveModeToggle.addEventListener('change', toggleLiveMode);
    }
    
    // Export functions
    const exportPdfBtn = document.getElementById('exportPdfBtn');
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', exportToPDF);
    }
    
    const clearDataBtn = document.getElementById('clearDataBtn');
    if (clearDataBtn) {
        clearDataBtn.addEventListener('click', clearAllData);
    }
}

// Authentication Functions
function showLoginModal() {
    const modal = document.createElement('div');
    modal.className = 'auth-modal';
    modal.innerHTML = `
        <div class="auth-modal-content">
            <h2>🔐 Login Required</h2>
            <form id="loginForm">
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" required placeholder="admin@test.com">
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" required placeholder="admin123">
                </div>
                <div class="form-actions">
                    <button type="submit">Login</button>
                    <button type="button" onclick="showRegisterForm()">Register</button>
                </div>
            </form>
            <p style="color: #888; font-size: 0.9rem; text-align: center; margin-top: 1rem;">
                Default: admin@test.com / admin123
            </p>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await apiRequest('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });
            
            authToken = response.data.access_token;
            currentUser = response.data.user;
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            document.body.removeChild(modal);
            updateUIForAuthenticatedUser();
            loadDashboardData();
            showNotification('Login successful', 'success');
        } catch (error) {
            showNotification('Login failed: ' + error.message, 'error');
        }
    });
}

function showRegisterForm() {
    const existingModal = document.querySelector('.auth-modal');
    if (existingModal) document.body.removeChild(existingModal);
    
    const modal = document.createElement('div');
    modal.className = 'auth-modal';
    modal.innerHTML = `
        <div class="auth-modal-content">
            <h2>📝 Register</h2>
            <form id="registerForm">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" required>
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" id="email" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" required>
                </div>
                <div class="form-group">
                    <label for="role">Role:</label>
                    <select id="role" required>
                        <option value="viewer">Viewer</option>
                        <option value="operator">Operator</option>
                    </select>
                </div>
                <div class="form-actions">
                    <button type="submit">Register</button>
                    <button type="button" onclick="showLoginModal()">Back to Login</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    document.getElementById('registerForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = {
            username: document.getElementById('username').value,
            email: document.getElementById('email').value,
            password: document.getElementById('password').value,
            role: document.getElementById('role').value
        };
        
        try {
            await apiRequest('/auth/register', {
                method: 'POST',
                body: JSON.stringify(formData)
            });
            
            document.body.removeChild(modal);
            showNotification('Registration successful. Please login.', 'success');
            showLoginModal();
        } catch (error) {
            showNotification('Registration failed: ' + error.message, 'error');
        }
    });
}

function updateUIForAuthenticatedUser() {
    const userInfo = document.querySelector('.user-info') || document.createElement('div');
    userInfo.className = 'user-info';
    userInfo.innerHTML = `
        <span>👤 ${currentUser.username} (${currentUser.role})</span>
        <button onclick="logout()" class="logout-btn">Logout</button>
    `;
    
    if (!document.querySelector('.user-info')) {
        document.querySelector('.header').appendChild(userInfo);
    }
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    const userInfo = document.querySelector('.user-info');
    if (userInfo) userInfo.remove();
    
    showNotification('Logged out successfully', 'info');
    showLoginModal();
}

// API Helper Functions
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    try {
        const response = await fetch(url, { ...options, headers });
        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 401) {
                logout();
                throw new Error('Authentication required');
            }
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        if (!error.message.includes('Authentication')) {
            showNotification(error.message, 'error');
        }
        throw error;
    }
}

// File Upload Functions
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#00ff88';
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#555';
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload({ target: { files } });
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    if (!authToken) {
        showLoginModal();
        return;
    }
    
    const allowedTypes = ['text/csv', 'application/json'];
    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.csv') && !file.name.endsWith('.json')) {
        showNotification('Please upload a CSV or JSON file', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify({
        detector_type: 'NaI',
        measurement_time: 300,
        location: 'User Upload'
    }));
    
    try {
        showNotification('Uploading file...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/upload/spectrum`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${authToken}` },
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Upload failed');
        }
        
        currentSpectrumData = data.data.spectrum_data;
        updateSpectrumChart(currentSpectrumData.energy, currentSpectrumData.counts);
        showNotification('File uploaded successfully', 'success');
        
        // Update file info display
        updateFileInfo(file.name, `${(file.size / 1024).toFixed(1)} KB`, currentSpectrumData.energy.length);
        
    } catch (error) {
        showNotification('Upload failed: ' + error.message, 'error');
    }
}

async function generateSyntheticSpectrum() {
    if (!authToken) {
        showLoginModal();
        return;
    }
    
    const isotope = document.getElementById('isotopeSelect').value;
    const noiseLevel = parseInt(document.getElementById('noiseLevel').value);
    
    try {
        showNotification('Generating synthetic spectrum...', 'info');
        
        const response = await apiRequest('/upload/synthetic', {
            method: 'POST',
            body: JSON.stringify({
                isotope: isotope,
                noise_level: noiseLevel
            })
        });
        
        currentSpectrumData = response.data.spectrum_data;
        updateSpectrumChart(currentSpectrumData.energy, currentSpectrumData.counts);
        showNotification('Synthetic spectrum generated', 'success');
        
        updateFileInfo(`Synthetic ${isotope}`, 'Generated', currentSpectrumData.energy.length);
        
    } catch (error) {
        showNotification('Failed to generate spectrum: ' + error.message, 'error');
    }
}

// Analysis Functions
async function runAnalysis() {
    if (!currentSpectrumData || !authToken) {
        if (!authToken) {
            showLoginModal();
            return;
        }
        showNotification('No spectrum data available', 'error');
        return;
    }
    
    if (analysisInProgress) {
        showNotification('Analysis already in progress', 'warning');
        return;
    }
    
    analysisInProgress = true;
    const runBtn = document.getElementById('runAnalysisBtn');
    if (runBtn) {
        runBtn.disabled = true;
        runBtn.textContent = 'Analyzing...';
    }
    
    try {
        const response = await apiRequest('/analysis/run', {
            method: 'POST',
            body: JSON.stringify({
                spectrum_data: currentSpectrumData,
                analysis_type: 'quantum',
                models: ['quantum']
            })
        });
        
        currentAnalysisSession = response.data.session_id;
        showNotification('Analysis started', 'info');
        
        // Show analysis progress
        showAnalysisProgress();
        
        // Poll for results
        pollAnalysisResults(currentAnalysisSession);
        
    } catch (error) {
        resetAnalysisUI();
        showNotification('Failed to start analysis: ' + error.message, 'error');
    }
}

async function pollAnalysisResults(sessionId) {
    const maxAttempts = 60;
    let attempts = 0;
    
    const poll = async () => {
        try {
            const response = await apiRequest(`/analysis/status/${sessionId}`);
            const status = response.data.status;
            
            if (status === 'completed') {
                const resultsResponse = await apiRequest(`/analysis/results/${sessionId}`);
                displayAnalysisResults(resultsResponse.data);
                
                const threatResponse = await apiRequest(`/threats/current`);
                updateThreatAssessment(threatResponse.data);
                
                resetAnalysisUI();
                showNotification('Analysis completed', 'success');
                
            } else if (status === 'failed') {
                throw new Error('Analysis failed');
                
            } else if (attempts < maxAttempts) {
                attempts++;
                setTimeout(poll, 5000);
                
            } else {
                throw new Error('Analysis timeout');
            }
            
        } catch (error) {
            resetAnalysisUI();
            showNotification('Analysis error: ' + error.message, 'error');
        }
    };
    
    poll();
}

function resetAnalysisUI() {
    analysisInProgress = false;
    const runBtn = document.getElementById('runAnalysisBtn');
    if (runBtn) {
        runBtn.disabled = false;
        runBtn.textContent = 'Run Analysis';
    }
    hideAnalysisProgress();
}

function showAnalysisProgress() {
    const progressDiv = document.getElementById('analysisProgress');
    if (progressDiv) {
        progressDiv.style.display = 'block';
        
        // Animate progress bar
        let progress = 0;
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        const progressSteps = [
            { progress: 20, text: 'Initializing quantum circuits...' },
            { progress: 40, text: 'Encoding spectrum data...' },
            { progress: 60, text: 'Running VQC analysis...' },
            { progress: 80, text: 'Running QSVC analysis...' },
            { progress: 95, text: 'Finalizing results...' }
        ];
        
        let stepIndex = 0;
        const updateProgress = () => {
            if (stepIndex < progressSteps.length && analysisInProgress) {
                const step = progressSteps[stepIndex];
                if (progressFill) progressFill.style.width = `${step.progress}%`;
                if (progressText) progressText.textContent = step.text;
                stepIndex++;
                setTimeout(updateProgress, 2000);
            }
        };
        
        updateProgress();
    }
}

function hideAnalysisProgress() {
    const progressDiv = document.getElementById('analysisProgress');
    if (progressDiv) {
        progressDiv.style.display = 'none';
    }
}

function displayAnalysisResults(results) {
    // Hide analysis progress
    hideAnalysisProgress();
    
    // Update quantum ML results
    if (results.quantum_result) {
        const quantum = results.quantum_result;
        
        // Update threat assessment
        const threatLevel = document.getElementById('quantumThreatLevel');
        const threatProb = document.getElementById('quantumThreat');
        if (threatLevel) {
            threatLevel.textContent = quantum.threat_level || 'UNKNOWN';
            threatLevel.className = `value threat-level ${(quantum.threat_level || 'unknown').toLowerCase()}`;
        }
        if (threatProb) threatProb.textContent = `${((quantum.threat_probability || 0) * 100).toFixed(1)}%`;
        
        // Update material identification
        const isotope = document.getElementById('quantumIsotope');
        const materialType = document.getElementById('quantumMaterialType');
        if (isotope) isotope.textContent = quantum.classified_isotope || 'Unknown';
        if (materialType) materialType.textContent = quantum.material_type || 'Unknown';
        
        // Update quantum metrics
        const vqcConfidence = document.getElementById('quantumVQCConfidence');
        const qsvcConfidence = document.getElementById('quantumQSVCConfidence');
        if (vqcConfidence) vqcConfidence.textContent = `${((quantum.vqc_confidence || 0) * 100).toFixed(1)}%`;
        if (qsvcConfidence) qsvcConfidence.textContent = `${((quantum.qsvc_confidence || 0) * 100).toFixed(1)}%`;
        
        // Update analysis details
        const processingTime = document.getElementById('quantumProcessingTime');
        const modelAgreement = document.getElementById('quantumModelAgreement');
        if (processingTime) processingTime.textContent = `${(quantum.processing_time || 0).toFixed(2)}s`;
        if (modelAgreement) modelAgreement.textContent = `${((quantum.model_agreement || 0) * 100).toFixed(1)}%`;
    }
    
    // Switch to results tab
    showTab('analysis');
    totalScans++;
    updateSystemStats();
}

function updateThreatAssessment(threatData) {
    const alertBanner = document.getElementById('alertBanner');
    const threatIndicator = document.getElementById('threatIndicator');
    
    let threatLevel = 'clear';
    let alertClass = 'alert-clear';
    
    if (threatData && threatData.overall_threat_probability) {
        if (threatData.overall_threat_probability > 0.7) {
            threatLevel = 'danger';
            alertClass = 'alert-danger';
            threatsDetected++;
        } else if (threatData.overall_threat_probability > 0.3) {
            threatLevel = 'warning';
            alertClass = 'alert-warning';
        }
    }
    
    if (alertBanner) {
        alertBanner.className = `alert-banner ${alertClass}`;
        alertBanner.textContent = `Threat Level: ${threatLevel}`;
    }
    
    if (threatIndicator) {
        threatIndicator.className = `threat-indicator ${alertClass}`;
        threatIndicator.textContent = threatLevel;
    }
    
    updateSystemStats();
}

// Dashboard Functions
async function loadDashboardData() {
    try {
        const statsResponse = await apiRequest('/dashboard/stats');
        updateDashboardStats(statsResponse.data);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

function updateDashboardStats(stats) {
    if (stats.total_analyses) totalScans = stats.total_analyses;
    if (stats.threats_detected) threatsDetected = stats.threats_detected;
    updateSystemStats();
}

// UI Helper Functions
function updateSpectrumChart(energy, counts) {
    if (spectrumChart) {
        spectrumChart.data.labels = energy;
        spectrumChart.data.datasets[0].data = counts;
        spectrumChart.update();
    }
}

function updateFileInfo(name, size, points) {
    const fileInfoElements = {
        fileName: name,
        fileSize: size,
        dataPoints: points
    };
    
    Object.entries(fileInfoElements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    });
}

function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to corresponding nav item
    const navItem = document.querySelector(`[data-tab="${tabName}"]`);
    if (navItem) {
        navItem.classList.add('active');
    }
}

// Alias for showTab function (for compatibility with HTML onclick handlers)
function switchTab(tabName) {
    showTab(tabName);
}

// Generate PDF report function
function generateReport() {
    if (!currentSpectrumData) {
        showNotification('No spectrum data available for report generation', 'warning');
        return;
    }
    
    try {
        showNotification('Generating PDF report...', 'info');
        // This would typically call a backend endpoint to generate a PDF
        // For now, we'll show a placeholder
        setTimeout(() => {
            showNotification('PDF report generation feature coming soon', 'info');
        }, 1000);
    } catch (error) {
        showNotification('Failed to generate report: ' + error.message, 'error');
    }
}

// Clear spectrum data function
function clearSpectrum() {
    if (confirm('Are you sure you want to clear the current spectrum?')) {
        currentSpectrumData = null;
        
        // Clear the chart
        if (spectrumChart) {
            spectrumChart.destroy();
            spectrumChart = null;
        }
        
        // Reset file info
        updateFileInfo('', '', 0);
        
        // Disable analysis button
        const runAnalysisBtn = document.getElementById('runAnalysisBtn');
        if (runAnalysisBtn) {
            runAnalysisBtn.disabled = true;
        }
        
        showNotification('Spectrum data cleared', 'success');
    }
}

// Search isotopes function
function searchIsotopes() {
    const searchInput = document.getElementById('isotopeSearch');
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    
    if (!searchTerm) {
        showNotification('Please enter a search term', 'warning');
        return;
    }
    
    try {
        // This would typically search through the isotope database
        // For now, we'll show a placeholder
        showNotification(`Searching for isotopes containing "${searchTerm}"...`, 'info');
        setTimeout(() => {
            showNotification('Isotope search feature coming soon', 'info');
        }, 1000);
    } catch (error) {
        showNotification('Search failed: ' + error.message, 'error');
    }
}

function updateSystemStats() {
    const uptime = Math.floor((Date.now() - systemStartTime) / 1000);
    const hours = Math.floor(uptime / 3600);
    const minutes = Math.floor((uptime % 3600) / 60);
    const seconds = uptime % 60;
    
    const systemUptime = document.getElementById('systemUptime');
    const totalScansEl = document.getElementById('totalScans');
    const threatsDetectedEl = document.getElementById('threatsDetected');
    const systemStatus = document.getElementById('systemStatus');
    
    if (systemUptime) systemUptime.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    if (totalScansEl) totalScansEl.textContent = totalScans;
    if (threatsDetectedEl) threatsDetectedEl.textContent = threatsDetected;
    if (systemStatus) systemStatus.textContent = authToken ? 'Online' : 'Offline';
}

function updateSystemUptime() {
    updateSystemStats();
}

// ... (rest of the code remains the same)
// Live Mode Functions
function toggleLiveMode() {
    const toggle = document.getElementById('liveModeToggle');
    const status = document.getElementById('liveStatus');
    
    if (!toggle) return;
    
    isLiveModeActive = toggle.checked;
    
    if (status) {
        if (isLiveModeActive) {
            status.textContent = 'ACTIVE';
            status.className = 'live-status active';
            startLiveMode();
        } else {
            status.textContent = 'INACTIVE';
            status.className = 'live-status';
            stopLiveMode();
        }
    }
}

function startLiveMode() {
    if (!authToken) {
        showLoginModal();
        return;
    }
    
    liveModeInterval = setInterval(async () => {
        const isotopes = ['K-40', 'Cs-137', 'Co-60', 'U-238'];
        const randomIsotope = isotopes[Math.floor(Math.random() * isotopes.length)];
        const randomNoise = Math.floor(Math.random() * 3) + 1;
        
        try {
            const response = await apiRequest('/upload/synthetic', {
                method: 'POST',
                body: JSON.stringify({
                    isotope: randomIsotope,
                    noise_level: randomNoise
                })
            });
            
            currentSpectrumData = response.data.spectrum_data;
            
            if (document.querySelector('[data-tab="upload"]').classList.contains('active')) {
                updateSpectrumChart(currentSpectrumData.energy, currentSpectrumData.counts);
            }
            
            // Auto-run analysis
            if (!analysisInProgress) {
                runAnalysis();
            }
            
            addLogEntry('INFO', `Live scan completed - ${randomIsotope} detected`);
            
        } catch (error) {
            console.error('Live mode error:', error);
        }
    }, 10000);
}

function stopLiveMode() {
    if (liveModeInterval) {
        clearInterval(liveModeInterval);
        liveModeInterval = null;
    }
}

// Export Functions
async function exportToPDF() {
    if (!authToken) {
        showLoginModal();
        return;
    }
    
    try {
        const reportData = {
            spectrum_data: currentSpectrumData,
            analysis_results: currentAnalysisSession,
            user_info: currentUser,
            timestamp: new Date().toISOString()
        };
        
        const response = await apiRequest('/reports/generate', {
            method: 'POST',
            body: JSON.stringify(reportData)
        });
        
        // Create download link
        const link = document.createElement('a');
        link.href = response.data.download_url;
        link.download = `radiological_report_${Date.now()}.pdf`;
        link.click();
        
        showNotification('Report generated successfully', 'success');
    } catch (error) {
        showNotification('Failed to generate report: ' + error.message, 'error');
    }
}

function clearAllData() {
    if (confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
        currentSpectrumData = null;
        currentAnalysisSession = null;
        
        if (spectrumChart) {
            spectrumChart.data.labels = [];
            spectrumChart.data.datasets[0].data = [];
            spectrumChart.update();
        }
        
        // Reset UI elements
        updateFileInfo('No file selected', '0 KB', 0);
        const alertBanner = document.getElementById('alertBanner');
        if (alertBanner) {
            alertBanner.className = 'alert-banner alert-clear';
            alertBanner.textContent = 'Threat Level: Clear';
        }
        
        showNotification('All data cleared', 'info');
        addLogEntry('INFO', 'All system data cleared');
    }
}

// Logging Functions
function addLogEntry(level, message) {
    const logContainer = document.getElementById('logEntries');
    if (!logContainer) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${level.toLowerCase()}`;
    logEntry.innerHTML = `
        <span class="log-time">${timestamp}</span>
        <span class="log-level">[${level}]</span>
        <span class="log-message">${message}</span>
    `;
    
    logContainer.insertBefore(logEntry, logContainer.firstChild);
    
    // Keep only last 100 entries
    while (logContainer.children.length > 100) {
        logContainer.removeChild(logContainer.lastChild);
    }
}

// Notification System
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background:none;border:none;color:white;float:right;cursor:pointer;">&times;</button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => notification.classList.add('show'), 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 5000);
}

// Populate isotope database for UI
function populateIsotopeDatabase() {
    const container = document.getElementById('isotopeList');
    if (!container) return;
    
    const isotopes = [
        { symbol: 'K-40', name: 'Potassium-40', type: 'Natural', threat: 'Low' },
        { symbol: 'Cs-137', name: 'Cesium-137', type: 'Medical', threat: 'High' },
        { symbol: 'Co-60', name: 'Cobalt-60', type: 'Industrial', threat: 'High' },
        { symbol: 'U-238', name: 'Uranium-238', type: 'Nuclear', threat: 'Very High' }
    ];
    
    container.innerHTML = isotopes.map(isotope => `
        <div class="isotope-card">
            <h4>${isotope.symbol}</h4>
            <p><strong>${isotope.name}</strong></p>
            <p>Type: ${isotope.type}</p>
            <p>Threat: <span class="threat-${isotope.threat.toLowerCase().replace(' ', '-')}">${isotope.threat}</span></p>
        </div>
    `).join('');
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 DOM Content Loaded - Starting authentication check...');
    
    // Don't run dashboard initialization on login pages
    const currentPage = window.location.pathname;
    const isLoginPage = currentPage.includes('login.html') || currentPage.includes('debug_auth.html');
    
    if (isLoginPage) {
        console.log('📝 On login page - skipping dashboard initialization');
        return;
    }
    
    // Check authentication first
    if (!checkAuthentication()) {
        console.log('❌ Authentication failed - redirecting to login');
        return; // Will redirect to login if not authenticated
    }
    
    console.log('✅ Authentication successful');
    console.log('Current user:', currentUser);
    
    // Update UI with user info
    if (currentUser) {
        const userElement = document.getElementById('currentUser');
        if (userElement) {
            userElement.textContent = currentUser.username || currentUser.email || 'User';
            console.log('✅ Updated user display');
        } else {
            console.log('⚠️ currentUser element not found');
        }
    }
    
    // Initialize other components
    try {
        populateIsotopeDatabase();
        console.log('✅ Isotope database populated');
    } catch (e) {
        console.error('❌ Error populating isotope database:', e);
    }
    
    // Initialize logging
    try {
        addLogEntry('INFO', 'Radiological Threat Detection System initialized');
        addLogEntry('INFO', 'Frontend-Backend integration active');
        addLogEntry('INFO', `User logged in: ${currentUser ? currentUser.email : 'Unknown'}`);
        console.log('✅ Logging initialized');
    } catch (e) {
        console.error('❌ Error initializing logging:', e);
    }
    
    console.log('🎉 Application initialization complete');
});
