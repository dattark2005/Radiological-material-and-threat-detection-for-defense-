# Deployment Guide - Quantum ML Radiological Threat Detection System

This guide provides comprehensive instructions for deploying the Quantum ML Radiological Threat Detection System in various environments.

## Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.11+ (for manual installation)
- PostgreSQL 15+ (for manual installation)
- Redis 7+ (for manual installation)
- Nginx (for production deployment)

## Quick Start with Docker

### 1. Clone and Setup

```bash
git clone <repository-url>
cd radiological-system/backend
```

### 2. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables
nano .env
```

Required environment variables:
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/radiological_db
REDIS_URL=redis://redis:6379/0

# Security
SECRET_KEY=your-production-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Admin User
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=secure-admin-password

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=52428800  # 50MB

# ML Models
MODEL_PATH=ml_models/
QUANTUM_BACKEND=qasm_simulator

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# CORS
CORS_ORIGINS=http://localhost,http://localhost:3000,https://yourdomain.com
```

### 3. Deploy with Docker Compose

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backend
```

### 4. Initialize Database

```bash
# Run database initialization
docker-compose exec backend python scripts/init_db.py

# Run migrations (if needed)
docker-compose exec backend python scripts/migrate_db.py
```

### 5. Access the System

- Frontend: http://localhost
- Backend API: http://localhost:5000
- Health Check: http://localhost:5000/health

## Manual Installation

### 1. System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip postgresql redis-server nginx
```

**CentOS/RHEL:**
```bash
sudo yum install python3.11 python3.11-venv python3-pip postgresql-server redis nginx
```

### 2. Database Setup

```bash
# PostgreSQL setup
sudo -u postgres createuser radiological_user
sudo -u postgres createdb radiological_db
sudo -u postgres psql -c "ALTER USER radiological_user PASSWORD 'your_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE radiological_db TO radiological_user;"
```

### 3. Application Setup

```bash
# Create application directory
sudo mkdir -p /opt/radiological-system
sudo chown $USER:$USER /opt/radiological-system
cd /opt/radiological-system

# Clone repository
git clone <repository-url> .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 4. Configuration

```bash
# Copy and edit environment file
cp backend/.env.example backend/.env
nano backend/.env

# Update database URL
DATABASE_URL=postgresql://radiological_user:your_password@localhost:5432/radiological_db
```

### 5. Initialize Database

```bash
cd backend
python scripts/init_db.py
```

### 6. Create Systemd Service

Create `/etc/systemd/system/radiological-backend.service`:

```ini
[Unit]
Description=Radiological System Backend
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=radiological
Group=radiological
WorkingDirectory=/opt/radiological-system/backend
Environment=PATH=/opt/radiological-system/venv/bin
ExecStart=/opt/radiological-system/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 4 --timeout 120 app:create_app()
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable radiological-backend
sudo systemctl start radiological-backend
sudo systemctl status radiological-backend
```

## Production Deployment

### 1. SSL/TLS Configuration

Update `nginx.conf` for HTTPS:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 2. Database Optimization

**PostgreSQL Configuration (`postgresql.conf`):**
```ini
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Connection settings
max_connections = 100

# Logging
log_statement = 'mod'
log_min_duration_statement = 1000
```

### 3. Monitoring Setup

**Prometheus Configuration:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'radiological-system'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/api/monitoring/metrics'
```

### 4. Backup Strategy

**Database Backup Script:**
```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="/opt/backups/radiological"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/radiological_backup_$DATE.sql"

mkdir -p $BACKUP_DIR

pg_dump -h localhost -U radiological_user radiological_db > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

**Cron Job:**
```bash
# Add to crontab
0 2 * * * /opt/scripts/backup_db.sh
```

## Scaling and High Availability

### 1. Load Balancer Configuration

**HAProxy Configuration:**
```
backend radiological_backend
    balance roundrobin
    server backend1 10.0.1.10:5000 check
    server backend2 10.0.1.11:5000 check
    server backend3 10.0.1.12:5000 check
```

### 2. Database Clustering

**PostgreSQL Master-Slave Setup:**
```bash
# On master server
echo "wal_level = replica" >> /etc/postgresql/15/main/postgresql.conf
echo "max_wal_senders = 3" >> /etc/postgresql/15/main/postgresql.conf

# Create replication user
sudo -u postgres psql -c "CREATE USER replicator REPLICATION LOGIN PASSWORD 'repl_password';"
```

### 3. Redis Clustering

**Redis Sentinel Configuration:**
```
# sentinel.conf
sentinel monitor radiological-redis 127.0.0.1 6379 2
sentinel down-after-milliseconds radiological-redis 5000
sentinel failover-timeout radiological-redis 10000
```

## Security Hardening

### 1. Firewall Configuration

```bash
# UFW rules
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 5432/tcp  # PostgreSQL (internal only)
sudo ufw deny 6379/tcp  # Redis (internal only)
sudo ufw enable
```

### 2. Application Security

**Environment Variables:**
```bash
# Use strong secrets
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)

# Database security
DATABASE_URL=postgresql://limited_user:strong_password@localhost:5432/radiological_db
```

**Rate Limiting:**
```nginx
# In nginx.conf
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=upload:10m rate=2r/s;
```

## Monitoring and Maintenance

### 1. Health Checks

```bash
# System health check script
#!/bin/bash
# health_check.sh

# Check backend health
curl -f http://localhost:5000/health || echo "Backend unhealthy"

# Check database
pg_isready -h localhost -p 5432 || echo "Database unhealthy"

# Check Redis
redis-cli ping || echo "Redis unhealthy"

# Check disk space
df -h | awk '$5 > 80 {print "Disk space warning: " $0}'
```

### 2. Log Rotation

```bash
# /etc/logrotate.d/radiological-system
/opt/radiological-system/backend/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 radiological radiological
    postrotate
        systemctl reload radiological-backend
    endscript
}
```

### 3. Performance Monitoring

**Key Metrics to Monitor:**
- API response times
- Database query performance
- Memory and CPU usage
- Disk I/O and space
- Network throughput
- Error rates and logs

## Troubleshooting

### Common Issues

**1. Database Connection Errors**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check connection
psql -h localhost -U radiological_user -d radiological_db

# Check logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

**2. Redis Connection Issues**
```bash
# Check Redis status
sudo systemctl status redis

# Test connection
redis-cli ping

# Check logs
sudo tail -f /var/log/redis/redis-server.log
```

**3. Application Errors**
```bash
# Check application logs
tail -f /opt/radiological-system/backend/logs/app.log

# Check systemd logs
sudo journalctl -u radiological-backend -f

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Performance Issues

**1. Slow Database Queries**
```sql
-- Enable query logging
ALTER SYSTEM SET log_min_duration_statement = 1000;
SELECT pg_reload_conf();

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

**2. High Memory Usage**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head

# Check application memory
docker stats radiological_backend
```

## Backup and Recovery

### 1. Full System Backup

```bash
#!/bin/bash
# full_backup.sh

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_ROOT="/opt/backups/$BACKUP_DATE"

mkdir -p $BACKUP_ROOT

# Database backup
pg_dump radiological_db > $BACKUP_ROOT/database.sql

# Application files
tar -czf $BACKUP_ROOT/application.tar.gz /opt/radiological-system

# Configuration files
tar -czf $BACKUP_ROOT/config.tar.gz /etc/nginx /etc/systemd/system/radiological-*

echo "Full backup completed: $BACKUP_ROOT"
```

### 2. Disaster Recovery

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR=$1

# Restore database
psql radiological_db < $BACKUP_DIR/database.sql

# Restore application
tar -xzf $BACKUP_DIR/application.tar.gz -C /

# Restore configuration
tar -xzf $BACKUP_DIR/config.tar.gz -C /

# Restart services
sudo systemctl restart radiological-backend nginx postgresql redis

echo "System restored from $BACKUP_DIR"
```

## Support and Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Review system logs
- Check disk space
- Verify backups
- Update security patches

**Monthly:**
- Database maintenance (VACUUM, ANALYZE)
- Review performance metrics
- Update dependencies
- Security audit

**Quarterly:**
- Full system backup test
- Disaster recovery drill
- Performance optimization review
- Security assessment

For additional support, refer to the system documentation or contact the development team.
