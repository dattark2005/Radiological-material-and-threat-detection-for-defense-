// API Configuration and Integration Layer
class RadiologicalAPI {
    constructor() {
        this.baseURL = 'http://localhost:5000/api';
        this.authToken = localStorage.getItem('authToken');
        this.currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    }

    // Generic API request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers
            });

            const data = await response.json();

            if (!response.ok) {
                if (response.status === 401) {
                    this.handleAuthError();
                    throw new Error('Authentication required');
                }
                throw new Error(data.error || 'API request failed');
            }

            return data;
        } catch (error) {
            console.error('API Error:', error);
            this.showNotification(error.message, 'error');
            throw error;
        }
    }

    // Authentication methods
    async login(email, password) {
        try {
            const response = await this.request('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });

            this.authToken = response.data.access_token;
            this.currentUser = response.data.user;
            localStorage.setItem('authToken', this.authToken);
            localStorage.setItem('currentUser', JSON.stringify(this.currentUser));

            this.showNotification('Login successful', 'success');
            return response.data;
        } catch (error) {
            throw error;
        }
    }

    async register(userData) {
        try {
            const response = await this.request('/auth/register', {
                method: 'POST',
                body: JSON.stringify(userData)
            });

            this.showNotification('Registration successful', 'success');
            return response.data;
        } catch (error) {
            throw error;
        }
    }

    logout() {
        this.authToken = null;
        this.currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('currentUser');
        this.showNotification('Logged out successfully', 'info');
    }

    // File upload methods
    async uploadSpectrum(file, metadata = {}) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('metadata', JSON.stringify({
            detector_type: 'NaI',
            measurement_time: 300,
            location: 'User Upload',
            ...metadata
        }));

        try {
            const response = await fetch(`${this.baseURL}/upload/spectrum`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Upload failed');
            }

            this.showNotification('File uploaded successfully', 'success');
            return data.data;
        } catch (error) {
            this.showNotification('Upload failed: ' + error.message, 'error');
            throw error;
        }
    }

    async generateSynthetic(params) {
        try {
            const response = await this.request('/upload/synthetic', {
                method: 'POST',
                body: JSON.stringify({
                    isotope: params.isotope,
                    activity: params.activity || 1000,
                    measurement_time: params.measurementTime || 300,
                    detector_type: 'NaI',
                    noise_level: params.noiseLevel || 0.1
                })
            });

            this.showNotification('Synthetic spectrum generated', 'success');
            return response.data;
        } catch (error) {
            throw error;
        }
    }

    // Analysis methods
    async startAnalysis(spectrumData) {
        try {
            const response = await this.request('/analysis/run', {
                method: 'POST',
                body: JSON.stringify({
                    spectrum_data: spectrumData,
                    analysis_type: 'full',
                    models: ['classical', 'quantum']
                })
            });

            this.showNotification('Analysis started', 'info');
            return response.data.session_id;
        } catch (error) {
            throw error;
        }
    }

    async getAnalysisStatus(sessionId) {
        return await this.request(`/analysis/status/${sessionId}`);
    }

    async getAnalysisResults(sessionId) {
        return await this.request(`/analysis/results/${sessionId}`);
    }

    // Threat assessment methods
    async getCurrentThreats() {
        return await this.request('/threats/current');
    }

    async getThreatHistory() {
        return await this.request('/threats/history');
    }

    // Dashboard methods
    async getDashboardStats() {
        return await this.request('/dashboard/stats');
    }

    async getRecentActivity() {
        return await this.request('/dashboard/recent-activity');
    }

    // Isotope database methods
    async getIsotopeDatabase() {
        return await this.request('/isotopes/database');
    }

    async searchIsotopes(query) {
        return await this.request('/isotopes/search', {
            method: 'POST',
            body: JSON.stringify({ query })
        });
    }

    // System logs methods
    async getSystemLogs(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return await this.request(`/logs/system?${queryString}`);
    }

    // Reports methods
    async generateReport(data) {
        return await this.request('/reports/generate', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Utility methods
    handleAuthError() {
        this.logout();
        window.showLoginModal();
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    isAuthenticated() {
        return !!this.authToken && !!this.currentUser;
    }

    getCurrentUser() {
        return this.currentUser;
    }
}

// Create global API instance
window.api = new RadiologicalAPI();
