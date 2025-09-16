# MongoDB Atlas Setup Guide

## 🚀 Quick Setup for MongoDB Atlas

### Step 1: Create MongoDB Atlas Account
1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Sign up for a free account
3. Create a new cluster (choose the free M0 tier)

### Step 2: Configure Database Access
1. In Atlas dashboard, go to **Database Access**
2. Click **Add New Database User**
3. Create a user with username and password
4. Grant **Read and write to any database** permissions

### Step 3: Configure Network Access
1. Go to **Network Access**
2. Click **Add IP Address**
3. Choose **Allow Access from Anywhere** (0.0.0.0/0) for development
4. Or add your specific IP address for production

### Step 4: Get Connection String
1. Go to **Clusters** and click **Connect**
2. Choose **Connect your application**
3. Select **Python** and version **3.6 or later**
4. Copy the connection string

### Step 5: Update Environment Variables
1. Open `backend/.env` file
2. Replace the MONGO_URI with your connection string:

```bash
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/radiological_db?retryWrites=true&w=majority
```

Replace:
- `<username>` with your database username
- `<password>` with your database password
- `cluster0.xxxxx.mongodb.net` with your actual cluster URL

### Step 6: Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 7: Run the Application
```bash
python run_local.py
```

## 🔧 Example Configuration

Your `.env` file should look like this:

```bash
# MongoDB Atlas Configuration
MONGO_URI=mongodb+srv://myuser:mypassword@cluster0.abc123.mongodb.net/radiological_db?retryWrites=true&w=majority

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=quantum-ml-radiological-detection-2024-secret-key
JWT_SECRET_KEY=jwt-quantum-ml-radiological-detection-2024-secret

# File Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# ML Model Configuration
MODEL_PATH=ml_models/
QUANTUM_BACKEND=qasm_simulator

# Security Configuration
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://127.0.0.1:5500

# Admin User (for initialization)
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

## 📊 Database Collections

The application will automatically create these collections:
- `users` - User accounts and authentication
- `spectrum_uploads` - Uploaded spectrum files
- `analysis_sessions` - ML analysis sessions
- `ml_results` - Analysis results from both classical and quantum models
- `threat_assessments` - Threat level assessments
- `system_logs` - Application logs and audit trail
- `isotope_references` - Isotope database with gamma ray signatures

## 🔒 Security Notes

1. **Never commit your actual MongoDB credentials to version control**
2. Use environment variables for all sensitive configuration
3. For production, restrict network access to specific IP addresses
4. Enable MongoDB Atlas monitoring and alerts
5. Regularly rotate database passwords

## 🐛 Troubleshooting

### Connection Issues
- Verify your IP address is whitelisted in Network Access
- Check username and password are correct
- Ensure the connection string format is correct

### Authentication Errors
- Verify database user has proper permissions
- Check if the database name in the connection string matches your setup

### Performance Issues
- Monitor your Atlas cluster metrics
- Consider upgrading from M0 (free tier) for production use
- Implement proper indexing for frequently queried fields

## 📈 Production Recommendations

1. **Upgrade to a paid tier** (M10 or higher) for production
2. **Enable backup** in Atlas dashboard
3. **Set up monitoring alerts** for performance and usage
4. **Use connection pooling** for high-traffic applications
5. **Implement proper indexing** on frequently queried fields
6. **Enable Atlas Search** for advanced text search capabilities

---

**Note**: The free M0 tier has limitations (512MB storage, shared CPU). For production use with multiple users and large datasets, consider upgrading to a dedicated cluster.
