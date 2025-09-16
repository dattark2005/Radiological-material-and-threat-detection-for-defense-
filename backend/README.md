# Quantum ML Radiological Threat Detection System - Backend

A production-ready quantum machine learning-based radiological threat detection system with comprehensive API endpoints and real-time capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SQLite (included with Python)

### Installation
```bash
cd backend
pip install -r requirements.txt
python run_local.py
```

The server will start on `http://localhost:5000`

## 📋 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login  
- `GET /api/auth/profile` - Get user profile
- `POST /api/auth/logout` - User logout

### Data Upload
- `POST /api/upload/spectrum` - Upload spectrum file (CSV/JSON)
- `POST /api/upload/synthetic` - Generate synthetic spectrum
- `GET /api/upload/history` - Get upload history

### ML Analysis
- `POST /api/analysis/run` - Start ML analysis
- `GET /api/analysis/status/<session_id>` - Check analysis status
- `GET /api/analysis/results/<session_id>` - Get analysis results
- `GET /api/analysis/history` - Get analysis history

### Threat Assessment
- `GET /api/threats/current` - Get current threat assessment
- `GET /api/threats/history` - Get threat history

### Dashboard & Reports
- `GET /api/dashboard/stats` - Get dashboard statistics
- `POST /api/reports/generate` - Generate PDF report
- `GET /api/isotopes/database` - Get isotope database

## 🏗️ Project Structure

```
backend/
├── api/                    # API blueprints
│   ├── auth.py            # Authentication endpoints
│   ├── upload.py          # File upload endpoints
│   ├── analysis.py        # ML analysis endpoints
│   ├── threats.py         # Threat assessment endpoints
│   ├── dashboard.py       # Dashboard endpoints
│   ├── isotopes.py        # Isotope database endpoints
│   ├── reports.py         # Report generation endpoints
│   ├── monitoring.py      # System monitoring endpoints
│   └── logs.py            # Logging endpoints
├── config/                # Configuration
│   └── config.py          # Application configuration
├── models/                # Database models
│   └── database.py        # SQLAlchemy models
├── services/              # Business logic services
│   ├── ml_service.py      # ML analysis service
│   ├── threat_service.py  # Threat assessment service
│   ├── report_service.py  # Report generation service
│   ├── isotope_service.py # Isotope database service
│   └── monitoring_service.py # System monitoring service
├── utils/                 # Utility functions
│   ├── auth.py            # Authentication utilities
│   ├── validation.py      # Input validation
│   └── helpers.py         # General helpers
├── app.py                 # Flask application factory
├── run_local.py           # Local development server
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── README.md              # This file
```

## ⚙️ Configuration

The `.env` file contains all necessary configuration:
- Database: SQLite (local file)
- Authentication: JWT tokens
- File uploads: Local storage
- ML models: Simulated processing

## 🔒 Security Features

- JWT-based authentication
- Role-based access control (admin, operator, viewer)
- Input validation and sanitization
- Secure file upload handling
- CORS protection

## 📊 Features

### Core Functionality
- **Dual ML Analysis**: Classical CNN and Quantum VQC/QNN models
- **Real-time Processing**: WebSocket support for live updates
- **File Processing**: CSV/JSON spectrum file support
- **Synthetic Data**: Generate test spectra for various isotopes
- **Threat Assessment**: Real-time threat level calculation
- **Isotope Database**: Comprehensive radioactive isotope reference
- **Report Generation**: PDF threat assessment reports
- **System Monitoring**: Health checks and performance metrics

### ML Models
- Classical Convolutional Neural Network (CNN)
- Quantum Variational Classifier (VQC)
- Quantum Neural Network (QNN)
- Parallel processing with confidence scoring

## 🚀 Running the Application

1. **Start Backend**:
   ```bash
   cd backend
   python run_local.py
   ```

2. **Default Admin User**:
   - Username: admin
   - Email: admin@example.com
   - Password: admin123

3. **Access Points**:
   - API: http://localhost:5000/api
   - Health: http://localhost:5000/health

## 🧪 API Response Format

### Success Response
```json
{
  "success": true,
  "data": {...},
  "message": "Optional message"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

## 🔧 Development

### Adding New Features
1. Create new API blueprint in `api/` directory
2. Register blueprint in `app.py`
3. Add business logic in `services/`
4. Update database models if needed

### Database Operations
- Models defined in `models/database.py`
- Automatic table creation on startup
- SQLite database file: `radiological.db`

## 📈 Performance

- SQLite database for fast local development
- In-memory caching for frequently accessed data
- Async ML processing
- Optimized query patterns

## 🐛 Troubleshooting

### Common Issues

**Port 5000 in use**:
```bash
# Change port in run_local.py
app.run(host='0.0.0.0', port=5001, debug=True)
```

**Module not found**:
```bash
pip install -r requirements.txt
```

**Database issues**:
- Delete `radiological.db` file to reset database
- Restart server to recreate tables

## 📄 License

MIT License - see LICENSE file for details.

---

**Version**: 2.0.0  
**Last Updated**: September 2024
