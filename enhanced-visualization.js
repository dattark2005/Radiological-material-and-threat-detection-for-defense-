/**
 * Enhanced Visualization Module
 * Provides 3D spectrum visualization, interactive peak identification,
 * time-series analysis, and spatial heatmap functionality
 */

class EnhancedVisualization {
    constructor() {
        this.currentMode = '2d';
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.spectrumMesh = null;
        this.peakMarkers = [];
        this.timeSeriesData = [];
        this.spatialData = [];
        
        this.init();
    }

    init() {
        console.log('🎨 Initializing Enhanced Visualization...');
        this.setupEventListeners();
        this.initializeTimeSeriesChart();
        this.initializeSpatialHeatmap();
        this.generateSampleData();
    }

    setupEventListeners() {
        // Visualization mode switcher
        document.querySelectorAll('.viz-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.switchVisualizationMode(e.target.dataset.mode);
            });
        });

        // Peak analysis toggle
        const peakToggle = document.getElementById('togglePeakAnalysis');
        if (peakToggle) {
            peakToggle.addEventListener('click', () => {
                this.togglePeakAnalysis();
            });
        }

        // Time series refresh
        const refreshBtn = document.getElementById('refreshTimeSeriesBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.refreshTimeSeries();
            });
        }

        // Time range selector
        const timeRangeSelect = document.getElementById('timeRangeSelect');
        if (timeRangeSelect) {
            timeRangeSelect.addEventListener('change', (e) => {
                this.updateTimeRange(e.target.value);
            });
        }

        // Threat level filter
        const threatFilter = document.getElementById('threatLevelFilter');
        if (threatFilter) {
            threatFilter.addEventListener('change', (e) => {
                this.updateThreatFilter(e.target.value);
            });
        }
    }

    // ===== 3D SPECTRUM VISUALIZATION =====
    
    switchVisualizationMode(mode) {
        console.log(`🔄 Switching to ${mode} visualization mode`);
        
        // Update button states
        document.querySelectorAll('.viz-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-mode="${mode}"]`).classList.add('active');
        
        // Hide all containers
        document.getElementById('spectrumChart').style.display = mode === '2d' ? 'block' : 'none';
        document.getElementById('spectrum3D').style.display = mode === '3d' ? 'block' : 'none';
        document.getElementById('spectrumInteractive').style.display = mode === 'interactive' ? 'block' : 'none';
        document.getElementById('spectrumHeatmap').style.display = mode === 'heatmap' ? 'block' : 'none';
        
        this.currentMode = mode;
        
        // Initialize the selected visualization
        switch(mode) {
            case '3d':
                this.initialize3DVisualization();
                break;
            case 'interactive':
                this.initializeInteractiveVisualization();
                break;
            case 'heatmap':
                this.initializeSpectrumHeatmap();
                break;
            default:
                // 2D mode is handled by existing Chart.js
                break;
        }
    }

    initialize3DVisualization() {
        const container = document.getElementById('spectrum3D');
        if (!container) return;

        // Clear existing content
        container.innerHTML = '';

        // Scene setup
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a2e);

        // Camera setup
        this.camera = new THREE.PerspectiveCamera(75, container.offsetWidth / container.offsetHeight, 0.1, 1000);
        this.camera.position.set(50, 30, 50);

        // Renderer setup
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(container.offsetWidth, container.offsetHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(this.renderer.domElement);

        // Controls
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.05;
        }

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(50, 50, 25);
        directionalLight.castShadow = true;
        this.scene.add(directionalLight);

        // Create 3D spectrum surface
        this.create3DSpectrum();

        // Animation loop
        this.animate3D();
    }

    create3DSpectrum() {
        // Generate sample spectrum data if not available
        const spectrumData = this.getCurrentSpectrumData();
        
        const width = 100;
        const height = 100;
        const geometry = new THREE.PlaneGeometry(width, height, width - 1, height - 1);
        
        // Create height map from spectrum data
        const vertices = geometry.attributes.position.array;
        for (let i = 0; i < vertices.length; i += 3) {
            const x = vertices[i];
            const y = vertices[i + 1];
            
            // Map x,y to spectrum data
            const dataIndex = Math.floor(((x + width/2) / width) * spectrumData.length);
            const intensity = spectrumData[Math.max(0, Math.min(dataIndex, spectrumData.length - 1))] || 0;
            
            vertices[i + 2] = intensity * 0.1; // Scale height
        }
        
        geometry.attributes.position.needsUpdate = true;
        geometry.computeVertexNormals();

        // Create material with color gradient
        const material = new THREE.MeshLambertMaterial({
            color: 0x00ff88,
            wireframe: false,
            transparent: true,
            opacity: 0.8
        });

        // Create mesh
        if (this.spectrumMesh) {
            this.scene.remove(this.spectrumMesh);
        }
        
        this.spectrumMesh = new THREE.Mesh(geometry, material);
        this.spectrumMesh.rotation.x = -Math.PI / 2;
        this.spectrumMesh.receiveShadow = true;
        this.scene.add(this.spectrumMesh);

        // Add peak markers
        this.addPeakMarkers3D(spectrumData);
    }

    addPeakMarkers3D(spectrumData) {
        // Clear existing markers
        this.peakMarkers.forEach(marker => this.scene.remove(marker));
        this.peakMarkers = [];

        // Find peaks
        const peaks = this.findPeaks(spectrumData);
        
        peaks.forEach(peak => {
            const geometry = new THREE.SphereGeometry(1, 8, 6);
            const material = new THREE.MeshBasicMaterial({ 
                color: peak.intensity > 0.7 ? 0xff0000 : peak.intensity > 0.4 ? 0xffaa00 : 0x00ff00 
            });
            
            const marker = new THREE.Mesh(geometry, material);
            marker.position.set(
                (peak.energy / spectrumData.length) * 100 - 50,
                peak.intensity * 10,
                0
            );
            
            this.scene.add(marker);
            this.peakMarkers.push(marker);
        });
    }

    animate3D() {
        if (!this.renderer || !this.scene || !this.camera) return;
        
        requestAnimationFrame(() => this.animate3D());
        
        if (this.controls) {
            this.controls.update();
        }
        
        // Rotate spectrum slowly
        if (this.spectrumMesh) {
            this.spectrumMesh.rotation.z += 0.005;
        }
        
        this.renderer.render(this.scene, this.camera);
    }

    // ===== INTERACTIVE VISUALIZATION =====
    
    initializeInteractiveVisualization() {
        const container = document.getElementById('spectrumInteractive');
        if (!container) return;

        const spectrumData = this.getCurrentSpectrumData();
        const energyData = Array.from({length: spectrumData.length}, (_, i) => i * 10); // 0-2000 keV

        const trace = {
            x: energyData,
            y: spectrumData,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Gamma Spectrum',
            line: {
                color: '#00ff88',
                width: 2
            },
            marker: {
                size: 4,
                color: spectrumData.map(val => val > 0.5 ? '#ff0000' : '#00ff88')
            },
            hovertemplate: '<b>Energy:</b> %{x} keV<br><b>Counts:</b> %{y}<br><extra></extra>'
        };

        // Add peak annotations
        const peaks = this.findPeaks(spectrumData);
        const annotations = peaks.map(peak => ({
            x: peak.energy * 10,
            y: peak.intensity,
            text: `Peak: ${(peak.energy * 10).toFixed(0)} keV`,
            showarrow: true,
            arrowhead: 2,
            arrowsize: 1,
            arrowwidth: 2,
            arrowcolor: '#ff6b6b',
            bgcolor: 'rgba(255, 107, 107, 0.8)',
            bordercolor: '#ff6b6b',
            font: { color: 'white', size: 10 }
        }));

        const layout = {
            title: {
                text: 'Interactive Gamma-Ray Spectrum Analysis',
                font: { color: '#ffffff', size: 16 }
            },
            xaxis: {
                title: 'Energy (keV)',
                color: '#ffffff',
                gridcolor: '#444444'
            },
            yaxis: {
                title: 'Counts',
                color: '#ffffff',
                gridcolor: '#444444'
            },
            plot_bgcolor: '#1a1a2e',
            paper_bgcolor: '#1a1a2e',
            annotations: annotations,
            showlegend: true
        };

        const config = {
            responsive: true,
            displayModeBar: true,
            modeBarButtonsToAdd: ['select2d', 'lasso2d'],
            toImageButtonOptions: {
                format: 'png',
                filename: 'spectrum_analysis',
                height: 500,
                width: 700,
                scale: 1
            }
        };

        Plotly.newPlot(container, [trace], layout, config);

        // Add click event for peak identification
        container.on('plotly_click', (data) => {
            const point = data.points[0];
            this.showPeakDetails(point.x, point.y);
        });
    }

    // ===== SPECTRUM HEATMAP =====
    
    initializeSpectrumHeatmap() {
        const container = document.getElementById('spectrumHeatmap');
        if (!container) return;

        // Generate time-energy heatmap data
        const timeSteps = 24; // 24 hours
        const energyBins = 100; // 100 energy bins
        const heatmapData = [];
        
        for (let t = 0; t < timeSteps; t++) {
            const row = [];
            for (let e = 0; e < energyBins; e++) {
                // Simulate varying intensity over time and energy
                const baseIntensity = Math.exp(-Math.pow((e - 30) / 15, 2)) * 0.8; // Cs-137 peak at ~662 keV
                const timeVariation = 0.5 + 0.5 * Math.sin(t * Math.PI / 12); // Daily variation
                const noise = Math.random() * 0.2;
                row.push(baseIntensity * timeVariation + noise);
            }
            heatmapData.push(row);
        }

        const trace = {
            z: heatmapData,
            type: 'heatmap',
            colorscale: [
                [0, '#000428'],
                [0.2, '#004e92'],
                [0.4, '#009ffd'],
                [0.6, '#00d2ff'],
                [0.8, '#ffaa00'],
                [1, '#ff0000']
            ],
            showscale: true,
            colorbar: {
                title: 'Intensity',
                titlefont: { color: '#ffffff' },
                tickfont: { color: '#ffffff' }
            }
        };

        const layout = {
            title: {
                text: 'Spectrum Intensity Heatmap (Time vs Energy)',
                font: { color: '#ffffff', size: 16 }
            },
            xaxis: {
                title: 'Energy Bins',
                color: '#ffffff'
            },
            yaxis: {
                title: 'Time (Hours)',
                color: '#ffffff'
            },
            plot_bgcolor: '#1a1a2e',
            paper_bgcolor: '#1a1a2e'
        };

        Plotly.newPlot(container, [trace], layout, { responsive: true });
    }

    // ===== TIME SERIES ANALYSIS =====
    
    initializeTimeSeriesChart() {
        const container = document.getElementById('timeSeriesChart');
        if (!container) return;

        this.generateTimeSeriesData();
        this.renderTimeSeriesChart();
    }

    generateTimeSeriesData() {
        const now = new Date();
        const hours = 24;
        this.timeSeriesData = [];

        for (let i = hours; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            const threatLevel = Math.random() * 0.8 + 0.1 + 0.3 * Math.sin(i * Math.PI / 12);
            const detectionCount = Math.floor(Math.random() * 50 + 10);
            
            this.timeSeriesData.push({
                time: time,
                threatLevel: Math.min(1, threatLevel),
                detectionCount: detectionCount,
                avgEnergy: 400 + Math.random() * 800,
                peakCount: Math.floor(Math.random() * 5 + 1)
            });
        }
    }

    renderTimeSeriesChart() {
        const container = document.getElementById('timeSeriesChart');
        const times = this.timeSeriesData.map(d => d.time);

        const threatTrace = {
            x: times,
            y: this.timeSeriesData.map(d => d.threatLevel),
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Threat Level',
            yaxis: 'y',
            line: { color: '#ff6b6b', width: 3 },
            marker: { size: 6 }
        };

        const countTrace = {
            x: times,
            y: this.timeSeriesData.map(d => d.detectionCount),
            type: 'scatter',
            mode: 'lines',
            name: 'Detection Count',
            yaxis: 'y2',
            line: { color: '#4ecdc4', width: 2 }
        };

        const layout = {
            title: {
                text: 'Threat Level & Detection Trends',
                font: { color: '#ffffff', size: 14 }
            },
            xaxis: {
                title: 'Time',
                color: '#ffffff',
                type: 'date'
            },
            yaxis: {
                title: 'Threat Level',
                color: '#ff6b6b',
                side: 'left',
                range: [0, 1]
            },
            yaxis2: {
                title: 'Detection Count',
                color: '#4ecdc4',
                side: 'right',
                overlaying: 'y'
            },
            plot_bgcolor: '#1a1a2e',
            paper_bgcolor: '#1a1a2e',
            legend: { font: { color: '#ffffff' } }
        };

        Plotly.newPlot(container, [threatTrace, countTrace], layout, { responsive: true });
    }

    // ===== SPATIAL HEATMAP =====
    
    initializeSpatialHeatmap() {
        const container = document.getElementById('spatialHeatmap');
        if (!container) return;

        this.generateSpatialData();
        this.renderSpatialHeatmap();
    }

    generateSpatialData() {
        // Generate random spatial threat data
        this.spatialData = [];
        const gridSize = 20;
        
        for (let x = 0; x < gridSize; x++) {
            const row = [];
            for (let y = 0; y < gridSize; y++) {
                // Create some hotspots
                const distance1 = Math.sqrt(Math.pow(x - 5, 2) + Math.pow(y - 5, 2));
                const distance2 = Math.sqrt(Math.pow(x - 15, 2) + Math.pow(y - 12, 2));
                
                const threat1 = Math.exp(-distance1 / 3) * 0.8;
                const threat2 = Math.exp(-distance2 / 4) * 0.6;
                const background = Math.random() * 0.1;
                
                row.push(Math.min(1, threat1 + threat2 + background));
            }
            this.spatialData.push(row);
        }
    }

    renderSpatialHeatmap() {
        const container = document.getElementById('spatialHeatmap');

        const trace = {
            z: this.spatialData,
            type: 'heatmap',
            colorscale: [
                [0, '#2d5016'],
                [0.3, '#61a3ba'],
                [0.6, '#d4af37'],
                [0.8, '#ff6b35'],
                [1, '#d32f2f']
            ],
            showscale: true,
            colorbar: {
                title: 'Threat Level',
                titlefont: { color: '#ffffff' },
                tickfont: { color: '#ffffff' }
            }
        };

        const layout = {
            title: {
                text: 'Spatial Threat Distribution Map',
                font: { color: '#ffffff', size: 14 }
            },
            xaxis: {
                title: 'Location X',
                color: '#ffffff'
            },
            yaxis: {
                title: 'Location Y',
                color: '#ffffff'
            },
            plot_bgcolor: '#1a1a2e',
            paper_bgcolor: '#1a1a2e'
        };

        Plotly.newPlot(container, [trace], layout, { responsive: true });
    }

    // ===== UTILITY FUNCTIONS =====
    
    getCurrentSpectrumData() {
        // Get current spectrum data from the main chart or generate sample data
        if (window.currentSpectrumData && window.currentSpectrumData.counts) {
            return window.currentSpectrumData.counts;
        }
        
        // Generate sample spectrum with Cs-137 peak
        const data = new Array(200).fill(0);
        for (let i = 0; i < data.length; i++) {
            const energy = i * 10; // 0-2000 keV
            
            // Background
            data[i] = Math.random() * 0.1 + 0.05;
            
            // Cs-137 peak at 662 keV
            if (energy > 650 && energy < 680) {
                data[i] += Math.exp(-Math.pow((energy - 662) / 8, 2)) * 0.8;
            }
            
            // K-40 peak at 1461 keV
            if (energy > 1450 && energy < 1470) {
                data[i] += Math.exp(-Math.pow((energy - 1461) / 10, 2)) * 0.4;
            }
        }
        
        return data;
    }

    findPeaks(data, threshold = 0.3) {
        const peaks = [];
        
        for (let i = 1; i < data.length - 1; i++) {
            if (data[i] > data[i-1] && data[i] > data[i+1] && data[i] > threshold) {
                peaks.push({
                    energy: i,
                    intensity: data[i],
                    width: this.calculatePeakWidth(data, i)
                });
            }
        }
        
        return peaks.sort((a, b) => b.intensity - a.intensity).slice(0, 10); // Top 10 peaks
    }

    calculatePeakWidth(data, peakIndex) {
        const peakValue = data[peakIndex];
        const halfMax = peakValue / 2;
        
        let leftIndex = peakIndex;
        let rightIndex = peakIndex;
        
        // Find left half-maximum
        while (leftIndex > 0 && data[leftIndex] > halfMax) {
            leftIndex--;
        }
        
        // Find right half-maximum
        while (rightIndex < data.length - 1 && data[rightIndex] > halfMax) {
            rightIndex++;
        }
        
        return rightIndex - leftIndex;
    }

    showPeakDetails(energy, intensity) {
        const panel = document.getElementById('peakAnalysisPanel');
        const details = document.getElementById('peakDetails');
        
        if (!panel || !details) return;
        
        // Identify isotope based on energy
        const isotope = this.identifyIsotope(energy);
        
        details.innerHTML = `
            <div class="peak-info">
                <h5>Peak Analysis</h5>
                <p><strong>Energy:</strong> ${energy.toFixed(1)} keV</p>
                <p><strong>Intensity:</strong> ${intensity.toFixed(3)} counts</p>
                <p><strong>Likely Isotope:</strong> ${isotope.name}</p>
                <p><strong>Confidence:</strong> ${isotope.confidence}%</p>
                <p><strong>Notes:</strong> ${isotope.notes}</p>
            </div>
        `;
        
        panel.style.display = 'block';
    }

    identifyIsotope(energy) {
        const isotopes = [
            { name: 'Cs-137', energy: 662, tolerance: 20, notes: 'Common medical/industrial source' },
            { name: 'K-40', energy: 1461, tolerance: 30, notes: 'Natural background radiation' },
            { name: 'Co-60', energy: 1173, tolerance: 25, notes: 'Industrial radiography source' },
            { name: 'Co-60', energy: 1333, tolerance: 25, notes: 'Industrial radiography source' },
            { name: 'U-238', energy: 1001, tolerance: 40, notes: 'Natural uranium decay' },
            { name: 'Ra-226', energy: 186, tolerance: 15, notes: 'Radium decay product' }
        ];
        
        for (const isotope of isotopes) {
            if (Math.abs(energy - isotope.energy) <= isotope.tolerance) {
                const confidence = Math.max(60, 100 - Math.abs(energy - isotope.energy) * 2);
                return { ...isotope, confidence: confidence.toFixed(0) };
            }
        }
        
        return { name: 'Unknown', confidence: '0', notes: 'No matching isotope found in database' };
    }

    togglePeakAnalysis() {
        const panel = document.getElementById('peakAnalysisPanel');
        if (panel) {
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }
    }

    refreshTimeSeries() {
        console.log('🔄 Refreshing time series data...');
        this.generateTimeSeriesData();
        this.renderTimeSeriesChart();
    }

    updateTimeRange(range) {
        console.log(`📊 Updating time range to: ${range}`);
        // Implement time range filtering logic
        this.refreshTimeSeries();
    }

    updateThreatFilter(level) {
        console.log(`🎯 Updating threat filter to: ${level}`);
        // Implement threat level filtering logic
        this.renderSpatialHeatmap();
    }

    generateSampleData() {
        // Generate some initial sample data for demonstration
        setTimeout(() => {
            if (this.currentMode === '3d') {
                this.create3DSpectrum();
            }
        }, 1000);
    }

    // ===== ENHANCED CHART.JS ANIMATIONS =====
    
    enhanceExistingChart() {
        // Add animations and interactions to the existing 2D chart
        if (window.spectrumChart) {
            window.spectrumChart.options.animation = {
                duration: 2000,
                easing: 'easeInOutQuart'
            };
            
            window.spectrumChart.options.plugins = {
                ...window.spectrumChart.options.plugins,
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            const energy = context.parsed.x;
                            const isotope = this.identifyIsotope(energy);
                            return `Possible: ${isotope.name} (${isotope.confidence}%)`;
                        }
                    }
                }
            };
            
            window.spectrumChart.update();
        }
    }
}

// Initialize enhanced visualization when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for other scripts to load
    setTimeout(() => {
        window.enhancedViz = new EnhancedVisualization();
        console.log('✅ Enhanced Visualization initialized');
    }, 1000);
});

// Export for global access
window.EnhancedVisualization = EnhancedVisualization;
