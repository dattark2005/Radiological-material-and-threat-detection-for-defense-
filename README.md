# Quantum ML Radiological Threat Detection System

A production-ready quantum machine learning-based radiological threat detection dashboard with comprehensive API backend and modern web interface.

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+ installed
- Modern web browser (Chrome, Firefox, Edge)

### Installation & Setup

1. **Install Python Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the Backend Server**
   ```bash
   python run_local.py
   ```
   
   The server will start on `http://localhost:5000`

3. **Open the Frontend**
   - Open `index.html` in your web browser
   - Or double-click the file to launch it

### 🔐 Default Login Credentials
- **Username**: admin
- **Email**: admin@example.com
- **Password**: admin123

## 📋 How to Use

### 1. Authentication
- Click "Login" in the top-right corner
- Enter the default credentials above
- The system will authenticate with the backend API

### 2. Data Upload & Analysis
- **Upload Files**: Drag and drop CSV/JSON spectrum files
- **Generate Synthetic**: Create synthetic spectra for K-40, Cs-137, Co-60, U-238
- **Run Analysis**: Process data through dual ML models (Classical CNN + Quantum VQC/QNN)

### 3. Threat Assessment
- View real-time threat levels (Clear/Low/Medium/High/Very High)
- Monitor contamination radius visualization
- Check emergency response recommendations

### 4. System Features
- **Dashboard**: Live system statistics and metrics
- **Isotope Database**: Comprehensive radioactive isotope reference
- **System Logs**: Real-time activity monitoring with severity levels
- **Reports**: Generate detailed PDF threat assessment reports

## 🏗️ Project Structure

```
├── index.html              # Main dashboard interface
├── styles.css              # Complete styling with defense-tech dark theme
├── api.js                  # Backend API communication layer
├── main.js                 # Full frontend functionality with real API integration
├── backend/
│   ├── api/                # API blueprints (auth, upload, analysis, etc.)
│   ├── config/             # Application configuration
│   ├── models/             # Database models
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions
│   ├── app.py              # Flask application factory
│   ├── run_local.py        # Local development server
│   ├── requirements.txt    # Python dependencies
│   ├── .env                # Environment configuration
│   └── README.md           # Backend documentation
└── README.md               # This file
```

## 🔧 Development

### Production Backend
```bash
cd backend
pip install -r requirements.txt
python run_local.py
```
- Complete Flask application with SQLite database
- Full authentication and authorization system
- Persistent data storage and session management
- Comprehensive API endpoints
- Real-time WebSocket support

## 🎯 Key Features

### Frontend
- **Modern Defense-Tech UI**: Dark theme with neon highlights
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live data visualization
- **Interactive Charts**: Spectrum visualization with Chart.js
- **Authentication**: Secure login/logout system

### Backend API Endpoints
- **Authentication**: `/api/auth/login`, `/api/auth/register`, `/api/auth/profile`, `/api/auth/logout`
- **Data Upload**: `/api/upload/spectrum`, `/api/upload/synthetic`, `/api/upload/history`
- **ML Analysis**: `/api/analysis/run`, `/api/analysis/status/<id>`, `/api/analysis/results/<id>`
- **Threat Assessment**: `/api/threats/current`, `/api/threats/history`
- **Dashboard**: `/api/dashboard/stats`, `/api/dashboard/recent`
- **Reports**: `/api/reports/generate`, `/api/reports/download/<id>`
- **System**: `/api/isotopes/database`, `/api/logs/system`, `/api/monitoring/health`

### ML Analysis
- **Classical CNN**: Traditional convolutional neural network
- **Quantum VQC/QNN**: Quantum variational classifier
- **Dual Processing**: Parallel analysis with both models
- **Confidence Scoring**: Reliability metrics for predictions

## 🛠️ Troubleshooting

### Backend Issues
- **Port 5000 in use**: Change port in `run_local.py`
- **Module not found**: Run `pip install -r requirements.txt` in backend directory
- **Database errors**: Delete `radiological.db` file and restart server

### Frontend Issues
- **API connection failed**: Verify backend server is running on localhost:5000
- **Login not working**: Check browser console for error messages
- **Charts not loading**: Ensure internet connection for Chart.js CDN

### Common Solutions
1. **Clear browser cache** if experiencing loading issues
2. **Check browser console** (F12) for JavaScript errors
3. **Verify server logs** in terminal for backend error messages
4. **Ensure firewall** allows connections to localhost:5000

## 📊 System Requirements

### Minimum Requirements
- **OS**: Windows 10, macOS 10.15, Ubuntu 18.04
- **Python**: 3.8+
- **RAM**: 4GB
- **Storage**: 1GB free space
- **Browser**: Chrome 90+, Firefox 88+, Edge 90+

### Recommended Requirements
- **OS**: Windows 11, macOS 12+, Ubuntu 20.04+
- **Python**: 3.10+
- **RAM**: 8GB
- **Storage**: 2GB free space
- **Browser**: Latest version of Chrome, Firefox, or Edge

## 🔒 Security Features

- JWT-based authentication
- CORS protection
- Input validation
- Rate limiting (in full backend)
- Secure file upload handling
- Role-based access control

## 📈 Performance

- **Response Time**: < 100ms for API calls
- **File Upload**: Supports files up to 10MB
- **Concurrent Users**: Up to 50 (simple server)
- **Analysis Time**: 5-15 seconds per spectrum

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review browser console for error messages
3. Check backend server logs
4. Ensure all dependencies are installed correctly

---

**Last Updated**: September 2024  
**Version**: 2.0.0  
**License**: MIT
