// Global variables
let spectrumChart = null;
let currentSpectrumData = null;
let systemStartTime = Date.now();
let totalScans = 0;
let threatsDetected = 0;
let isLiveModeActive = false;
let liveModeInterval = null;
let analysisInProgress = false;

// Isotope database
const isotopeDatabase = {
    'K-40': {
        name: 'Potassium-40',
        type: 'Natural Background',
        peaks: [1460.8],
        halfLife: '1.25 billion years',
        threat: 'Low',
        description: 'Naturally occurring radioactive isotope found in soil, food, and human body'
    },
    'Cs-137': {
        name: 'Cesium-137',
        type: 'Medical/Industrial',
        peaks: [661.7],
        halfLife: '30.17 years',
        threat: 'High',
        description: 'Artificial radioisotope used in medical devices and industrial applications'
    },
    'Co-60': {
        name: 'Cobalt-60',
        type: 'Industrial Source',
        peaks: [1173.2, 1332.5],
        halfLife: '5.27 years',
        threat: 'High',
        description: 'Artificial radioisotope used in medical therapy and industrial radiography'
    },
    'U-238': {
        name: 'Uranium-238',
        type: 'Nuclear Material',
        peaks: [1001.0, 766.4],
        halfLife: '4.47 billion years',
        threat: 'Very High',
        description: 'Naturally occurring uranium isotope, parent of uranium decay series'
    }
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    updateSystemStats();
    populateIsotopeDatabase();
    
    // Start system uptime counter
    setInterval(updateSystemUptime, 1000);
});

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
                    labels: {
                        color: '#e0e0e0'
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Energy (keV)',
                        color: '#00ccff'
                    },
                    ticks: {
                        color: '#888'
                    },
                    grid: {
                        color: '#333'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Counts',
                        color: '#00ccff'
                    },
                    ticks: {
                        color: '#888'
                    },
                    grid: {
                        color: '#333'
                    }
                }
            }
        }
    });
    
    addLogEntry('INFO', 'System initialized successfully');
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', function() {
            const tab = this.dataset.tab;
            switchTab(tab);
        });
    });
    
    // File upload
    const fileInput = document.getElementById('fileInput');
    const fileUploadArea = document.getElementById('fileUploadArea');
    
    fileUploadArea.addEventListener('click', () => fileInput.click());
    fileUploadArea.addEventListener('dragover', handleDragOver);
    fileUploadArea.addEventListener('drop', handleFileDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Live mode toggle
    document.getElementById('liveModeToggle').addEventListener('change', toggleLiveMode);
    
    // Isotope search
    document.getElementById('isotopeSearch').addEventListener('input', filterIsotopes);
}

function switchTab(tabName) {
    // Update navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');
    
    addLogEntry('INFO', `Switched to ${tabName} tab`);
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#00ff88';
}

function handleFileDrop(e) {
    e.preventDefault();
    e.currentTarget.style.borderColor = '#555';
    const files = e.dataTransfer.files;
    processFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    processFiles(files);
}

function processFiles(files) {
    if (files.length === 0) return;
    
    const file = files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            let data;
            if (file.name.endsWith('.json')) {
                data = JSON.parse(e.target.result);
            } else if (file.name.endsWith('.csv')) {
                data = parseCSV(e.target.result);
            }
            
            if (data && data.energy && data.counts) {
                currentSpectrumData = data;
                updateSpectrumChart(data.energy, data.counts);
                document.getElementById('runAnalysisBtn').disabled = false;
                addLogEntry('INFO', `Loaded spectrum data from ${file.name}`);
            } else {
                throw new Error('Invalid file format');
            }
        } catch (error) {
            addLogEntry('ERROR', `Failed to load file: ${error.message}`);
            alert('Error loading file. Please ensure it contains energy and counts data.');
        }
    };
    
    reader.readAsText(file);
}

function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    
    const energyIndex = headers.findIndex(h => h.includes('energy'));
    const countsIndex = headers.findIndex(h => h.includes('count'));
    
    if (energyIndex === -1 || countsIndex === -1) {
        throw new Error('CSV must contain energy and counts columns');
    }
    
    const energy = [];
    const counts = [];
    
    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',');
        if (values.length > Math.max(energyIndex, countsIndex)) {
            energy.push(parseFloat(values[energyIndex]));
            counts.push(parseFloat(values[countsIndex]));
        }
    }
    
    return { energy, counts };
}

function generateSpectrum() {
    const isotope = document.getElementById('isotopeSelect').value;
    const noiseLevel = parseInt(document.getElementById('noiseLevel').value);
    
    let spectrumData;
    
    if (isotope === 'mixed') {
        spectrumData = generateMixedSpectrum(noiseLevel);
    } else {
        spectrumData = generateSingleIsotopeSpectrum(isotope, noiseLevel);
    }
    
    currentSpectrumData = spectrumData;
    updateSpectrumChart(spectrumData.energy, spectrumData.counts);
    document.getElementById('runAnalysisBtn').disabled = false;
    
    addLogEntry('INFO', `Generated synthetic spectrum for ${isotope} with noise level ${noiseLevel}`);
}

function generateSingleIsotopeSpectrum(isotope, noiseLevel) {
    const energy = [];
    const counts = [];
    const isotopeData = isotopeDatabase[isotope];
    
    // Generate energy range from 0 to 2000 keV
    for (let e = 0; e <= 2000; e += 10) {
        energy.push(e);
        
        let count = Math.random() * 50 * noiseLevel; // Background noise
        
        // Add peaks for the isotope
        isotopeData.peaks.forEach(peakEnergy => {
            const sigma = 20; // Peak width
            const amplitude = 1000 + Math.random() * 500; // Peak height
            const gaussian = amplitude * Math.exp(-Math.pow(e - peakEnergy, 2) / (2 * sigma * sigma));
            count += gaussian;
        });
        
        counts.push(Math.max(0, count + (Math.random() - 0.5) * 20 * noiseLevel));
    }
    
    return { energy, counts, isotope };
}

function generateMixedSpectrum(noiseLevel) {
    const energy = [];
    const counts = [];
    const isotopes = ['K-40', 'Cs-137'];
    
    for (let e = 0; e <= 2000; e += 10) {
        energy.push(e);
        
        let count = Math.random() * 50 * noiseLevel;
        
        isotopes.forEach(isotope => {
            const isotopeData = isotopeDatabase[isotope];
            isotopeData.peaks.forEach(peakEnergy => {
                const sigma = 20;
                const amplitude = 500 + Math.random() * 300;
                const gaussian = amplitude * Math.exp(-Math.pow(e - peakEnergy, 2) / (2 * sigma * sigma));
                count += gaussian;
            });
        });
        
        counts.push(Math.max(0, count + (Math.random() - 0.5) * 20 * noiseLevel));
    }
    
    return { energy, counts, isotope: 'mixed' };
}

function updateSpectrumChart(energy, counts) {
    spectrumChart.data.labels = energy;
    spectrumChart.data.datasets[0].data = counts;
    spectrumChart.update();
}

function clearSpectrum() {
    currentSpectrumData = null;
    spectrumChart.data.labels = [];
    spectrumChart.data.datasets[0].data = [];
    spectrumChart.update();
    document.getElementById('runAnalysisBtn').disabled = true;
    addLogEntry('INFO', 'Spectrum data cleared');
}

function runAnalysis() {
    if (!currentSpectrumData || analysisInProgress) return;
    
    analysisInProgress = true;
    document.getElementById('runAnalysisBtn').disabled = true;
    
    // Show progress
    const progressCard = document.getElementById('analysisProgress');
    progressCard.style.display = 'block';
    
    // Switch to analysis tab
    switchTab('analysis');
    
    // Simulate analysis progress
    simulateAnalysisProgress().then(() => {
        const results = performAnalysis(currentSpectrumData);
        displayAnalysisResults(results);
        updateThreatAssessment(results);
        updateExplainability(results);
        
        progressCard.style.display = 'none';
        analysisInProgress = false;
        
        totalScans++;
        if (results.classical.threatProbability > 0.5 || results.quantum.threatProbability > 0.5) {
            threatsDetected++;
        }
        updateSystemStats();
        
        addLogEntry('INFO', `Analysis completed - Threat probability: ${Math.max(results.classical.threatProbability, results.quantum.threatProbability).toFixed(2)}`);
    });
}

function simulateAnalysisProgress() {
    return new Promise((resolve) => {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        const steps = [
            { progress: 20, text: 'Preprocessing spectral data...' },
            { progress: 40, text: 'Running Classical CNN model...' },
            { progress: 60, text: 'Executing Quantum VQC...' },
            { progress: 80, text: 'Analyzing results...' },
            { progress: 100, text: 'Analysis complete!' }
        ];
        
        let currentStep = 0;
        
        const updateProgress = () => {
            if (currentStep < steps.length) {
                const step = steps[currentStep];
                progressFill.style.width = step.progress + '%';
                progressText.textContent = step.text;
                currentStep++;
                setTimeout(updateProgress, 1000);
            } else {
                resolve();
            }
        };
        
        updateProgress();
    });
}

function performAnalysis(spectrumData) {
    // Simulate ML model analysis
    const peakEnergies = findPeaks(spectrumData.energy, spectrumData.counts);
    
    // Classical model results
    const classicalResults = simulateClassicalModel(peakEnergies, spectrumData);
    
    // Quantum model results (slightly different)
    const quantumResults = simulateQuantumModel(peakEnergies, spectrumData);
    
    return {
        classical: classicalResults,
        quantum: quantumResults,
        peaks: peakEnergies
    };
}

function findPeaks(energy, counts) {
    const peaks = [];
    const threshold = Math.max(...counts) * 0.1; // 10% of max count
    
    for (let i = 1; i < counts.length - 1; i++) {
        if (counts[i] > counts[i-1] && counts[i] > counts[i+1] && counts[i] > threshold) {
            peaks.push({
                energy: energy[i],
                counts: counts[i],
                significance: counts[i] / Math.max(...counts)
            });
        }
    }
    
    return peaks.sort((a, b) => b.significance - a.significance).slice(0, 5);
}

function simulateClassicalModel(peaks, spectrumData) {
    let isotope = 'Unknown';
    let threatProbability = 0;
    let confidence = 'Low';
    let quantity = 'Small';
    
    // Check for known isotope signatures
    for (const [isotopeKey, isotopeData] of Object.entries(isotopeDatabase)) {
        const matchingPeaks = peaks.filter(peak => 
            isotopeData.peaks.some(refPeak => Math.abs(peak.energy - refPeak) < 30)
        );
        
        if (matchingPeaks.length > 0) {
            isotope = isotopeKey;
            
            // Calculate threat probability based on isotope and peak intensity
            if (isotopeData.threat === 'Very High') {
                threatProbability = 0.85 + Math.random() * 0.1;
            } else if (isotopeData.threat === 'High') {
                threatProbability = 0.65 + Math.random() * 0.2;
            } else if (isotopeData.threat === 'Low') {
                threatProbability = 0.1 + Math.random() * 0.2;
            }
            
            // Adjust based on peak intensity
            const maxPeakIntensity = Math.max(...matchingPeaks.map(p => p.significance));
            if (maxPeakIntensity > 0.8) {
                quantity = 'Large';
                confidence = 'High';
                threatProbability *= 1.2;
            } else if (maxPeakIntensity > 0.5) {
                quantity = 'Medium';
                confidence = 'Medium';
            }
            
            break;
        }
    }
    
    // Add some randomness for realism
    threatProbability = Math.min(1, threatProbability + (Math.random() - 0.5) * 0.1);
    
    return {
        isotope,
        threatProbability,
        confidence,
        quantity
    };
}

function simulateQuantumModel(peaks, spectrumData) {
    // Quantum model gives slightly different results
    const classicalResults = simulateClassicalModel(peaks, spectrumData);
    
    return {
        isotope: classicalResults.isotope,
        threatProbability: Math.min(1, classicalResults.threatProbability + (Math.random() - 0.5) * 0.15),
        confidence: classicalResults.confidence,
        quantity: classicalResults.quantity
    };
}

function displayAnalysisResults(results) {
    // Classical results
    document.getElementById('classicalThreat').textContent = (results.classical.threatProbability * 100).toFixed(1) + '%';
    document.getElementById('classicalIsotope').textContent = results.classical.isotope;
    document.getElementById('classicalQuantity').textContent = results.classical.quantity;
    document.getElementById('classicalConfidence').textContent = results.classical.confidence;
    
    // Quantum results
    document.getElementById('quantumThreat').textContent = (results.quantum.threatProbability * 100).toFixed(1) + '%';
    document.getElementById('quantumIsotope').textContent = results.quantum.isotope;
    document.getElementById('quantumQuantity').textContent = results.quantum.quantity;
    document.getElementById('quantumConfidence').textContent = results.quantum.confidence;
}

function updateThreatAssessment(results) {
    const maxThreat = Math.max(results.classical.threatProbability, results.quantum.threatProbability);
    const alertBanner = document.getElementById('alertBanner');
    const threatIndicator = document.getElementById('threatIndicator');
    const contaminationZone = document.getElementById('contaminationZone');
    
    let alertClass, alertText, alertIcon;
    
    if (maxThreat > 0.8) {
        alertClass = 'danger';
        alertText = 'HIGH ALERT - Significant threat detected';
        alertIcon = 'fas fa-exclamation-triangle';
    } else if (maxThreat > 0.5) {
        alertClass = 'warning';
        alertText = 'UNCERTAIN - Manual inspection required';
        alertIcon = 'fas fa-exclamation-circle';
    } else {
        alertClass = 'clear';
        alertText = 'CLEAR - No threat detected';
        alertIcon = 'fas fa-shield-alt';
    }
    
    // Update alert banner
    alertBanner.className = `alert-banner ${alertClass}`;
    alertBanner.innerHTML = `
        <div class="alert-content">
            <i class="${alertIcon}"></i>
            <span>${alertText}</span>
        </div>
    `;
    
    // Update threat indicator in dashboard
    const threatDisplay = threatIndicator.querySelector('.threat-level-display');
    threatDisplay.className = `threat-level-display ${alertClass}`;
    threatDisplay.innerHTML = `
        <span class="threat-text">${alertClass.toUpperCase()}</span>
        <span class="threat-description">${alertText}</span>
    `;
    
    // Update contamination zone
    contaminationZone.className = `contamination-zone ${alertClass}`;
    
    // Adjust zone size based on quantity
    const quantity = results.classical.quantity || results.quantum.quantity;
    if (quantity === 'Large') {
        contaminationZone.style.width = '250px';
        contaminationZone.style.height = '250px';
    } else if (quantity === 'Medium') {
        contaminationZone.style.width = '150px';
        contaminationZone.style.height = '150px';
    } else {
        contaminationZone.style.width = '100px';
        contaminationZone.style.height = '100px';
    }
}

function updateExplainability(results) {
    const explainabilityContent = document.getElementById('explainabilityContent');
    
    let explanation = '<h4>Analysis Summary</h4>';
    explanation += `<p><strong>Detected Peaks:</strong> ${results.peaks.length} significant peaks found</p>`;
    
    if (results.peaks.length > 0) {
        explanation += '<h5>Peak Analysis:</h5><ul>';
        results.peaks.forEach(peak => {
            explanation += `<li>Energy: ${peak.energy.toFixed(1)} keV, Intensity: ${(peak.significance * 100).toFixed(1)}%</li>`;
        });
        explanation += '</ul>';
    }
    
    explanation += '<h5>Model Comparison:</h5>';
    explanation += `<p><strong>Classical CNN:</strong> ${(results.classical.threatProbability * 100).toFixed(1)}% threat probability</p>`;
    explanation += `<p><strong>Quantum VQC:</strong> ${(results.quantum.threatProbability * 100).toFixed(1)}% threat probability</p>`;
    
    const avgThreat = (results.classical.threatProbability + results.quantum.threatProbability) / 2;
    explanation += `<p><strong>Consensus:</strong> ${(avgThreat * 100).toFixed(1)}% average threat probability</p>`;
    
    if (results.classical.isotope !== 'Unknown') {
        const isotopeData = isotopeDatabase[results.classical.isotope];
        explanation += `<h5>Isotope Information:</h5>`;
        explanation += `<p><strong>Identified:</strong> ${isotopeData.name} (${results.classical.isotope})</p>`;
        explanation += `<p><strong>Type:</strong> ${isotopeData.type}</p>`;
        explanation += `<p><strong>Description:</strong> ${isotopeData.description}</p>`;
    }
    
    explainabilityContent.innerHTML = explanation;
}

function toggleLiveMode() {
    const toggle = document.getElementById('liveModeToggle');
    const status = document.getElementById('liveStatus');
    
    isLiveModeActive = toggle.checked;
    
    if (isLiveModeActive) {
        status.textContent = 'Active - Scanning every 10s';
        status.style.color = '#00ff88';
        liveModeInterval = setInterval(performLiveScan, 10000);
        addLogEntry('INFO', 'Live mode activated');
    } else {
        status.textContent = 'Inactive';
        status.style.color = '#888';
        if (liveModeInterval) {
            clearInterval(liveModeInterval);
        }
        addLogEntry('INFO', 'Live mode deactivated');
    }
}

function performLiveScan() {
    if (!isLiveModeActive) return;
    
    // Generate random spectrum
    const isotopes = ['K-40', 'Cs-137', 'Co-60', 'U-238'];
    const randomIsotope = isotopes[Math.floor(Math.random() * isotopes.length)];
    const randomNoise = Math.floor(Math.random() * 3) + 1;
    
    const spectrumData = generateSingleIsotopeSpectrum(randomIsotope, randomNoise);
    currentSpectrumData = spectrumData;
    
    if (document.querySelector('[data-tab="upload"]').classList.contains('active')) {
        updateSpectrumChart(spectrumData.energy, spectrumData.counts);
    }
    
    // Auto-run analysis
    const results = performAnalysis(spectrumData);
    displayAnalysisResults(results);
    updateThreatAssessment(results);
    updateExplainability(results);
    
    totalScans++;
    if (results.classical.threatProbability > 0.5 || results.quantum.threatProbability > 0.5) {
        threatsDetected++;
    }
    updateSystemStats();
    
    addLogEntry('INFO', `Live scan completed - ${randomIsotope} detected`);
}

function updateSystemStats() {
    document.getElementById('totalScans').textContent = totalScans;
    document.getElementById('threatsDetected').textContent = threatsDetected;
}

function updateSystemUptime() {
    const uptime = Date.now() - systemStartTime;
    const hours = Math.floor(uptime / 3600000);
    const minutes = Math.floor((uptime % 3600000) / 60000);
    const seconds = Math.floor((uptime % 60000) / 1000);
    
    document.getElementById('systemUptime').textContent = 
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

function addLogEntry(level, message) {
    const logsContainer = document.getElementById('logsContainer');
    const timestamp = new Date().toLocaleString();
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `
        <span class="timestamp">[${timestamp}]</span>
        <span class="log-level ${level.toLowerCase()}">${level}</span>
        <span class="message">${message}</span>
    `;
    
    logsContainer.insertBefore(logEntry, logsContainer.firstChild);
    
    // Keep only last 50 entries
    while (logsContainer.children.length > 50) {
        logsContainer.removeChild(logsContainer.lastChild);
    }
}

function populateIsotopeDatabase() {
    const isotopeList = document.getElementById('isotopeList');
    
    Object.entries(isotopeDatabase).forEach(([key, isotope]) => {
        const item = document.createElement('div');
        item.className = 'isotope-item';
        item.innerHTML = `
            <div class="isotope-name">${isotope.name} (${key})</div>
            <div class="isotope-details">
                Type: ${isotope.type} | Half-life: ${isotope.halfLife} | Threat Level: ${isotope.threat}
                <br>Peaks: ${isotope.peaks.join(', ')} keV
                <br>${isotope.description}
            </div>
        `;
        
        item.addEventListener('click', () => {
            // Generate spectrum for this isotope
            document.getElementById('isotopeSelect').value = key;
            generateSpectrum();
            switchTab('upload');
        });
        
        isotopeList.appendChild(item);
    });
}

function searchIsotopes() {
    filterIsotopes();
}

function filterIsotopes() {
    const searchTerm = document.getElementById('isotopeSearch').value.toLowerCase();
    const items = document.querySelectorAll('.isotope-item');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (text.includes(searchTerm)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

function generateReport() {
    // Create PDF report using jsPDF
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    // Header
    doc.setFontSize(20);
    doc.text('Radiological Threat Detection Report', 20, 20);
    
    // System info
    doc.setFontSize(12);
    doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 40);
    doc.text(`Total Scans: ${totalScans}`, 20, 50);
    doc.text(`Threats Detected: ${threatsDetected}`, 20, 60);
    
    // Current analysis results
    if (currentSpectrumData) {
        doc.text('Latest Analysis Results:', 20, 80);
        
        const classicalThreat = document.getElementById('classicalThreat').textContent;
        const quantumThreat = document.getElementById('quantumThreat').textContent;
        const isotope = document.getElementById('classicalIsotope').textContent;
        
        doc.text(`Classical Model Threat: ${classicalThreat}`, 20, 90);
        doc.text(`Quantum Model Threat: ${quantumThreat}`, 20, 100);
        doc.text(`Identified Isotope: ${isotope}`, 20, 110);
    }
    
    // Save the PDF
    doc.save('radiological-threat-report.pdf');
    
    addLogEntry('INFO', 'PDF report generated and downloaded');
}

function clearAllData() {
    if (confirm('Are you sure you want to clear all data? This action cannot be undone.')) {
        // Reset counters
        totalScans = 0;
        threatsDetected = 0;
        systemStartTime = Date.now();
        
        // Clear spectrum
        clearSpectrum();
        
        // Reset analysis results
        document.getElementById('classicalThreat').textContent = '--';
        document.getElementById('classicalIsotope').textContent = '--';
        document.getElementById('classicalQuantity').textContent = '--';
        document.getElementById('classicalConfidence').textContent = '--';
        
        document.getElementById('quantumThreat').textContent = '--';
        document.getElementById('quantumIsotope').textContent = '--';
        document.getElementById('quantumQuantity').textContent = '--';
        document.getElementById('quantumConfidence').textContent = '--';
        
        // Reset threat assessment
        const alertBanner = document.getElementById('alertBanner');
        alertBanner.className = 'alert-banner clear';
        alertBanner.innerHTML = `
            <div class="alert-content">
                <i class="fas fa-shield-alt"></i>
                <span>No active threats detected</span>
            </div>
        `;
        
        // Clear logs
        const logsContainer = document.getElementById('logsContainer');
        logsContainer.innerHTML = '';
        
        // Update stats
        updateSystemStats();
        
        addLogEntry('INFO', 'All system data cleared');
    }
}
