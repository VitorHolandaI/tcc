# VPS Deployment Guide

## Overview

This guide explains how to deploy the complete TCC monitoring system to a VPS using Docker Compose and Nginx as a reverse proxy.

## System Architecture

The system consists of 7 microservices:

| Service | Port | Purpose |
|---------|------|---------|
| **Main API** | 8000 | Core backend (provas, submissoes, usuarios) |
| **Recording Service** | 8001 | Screen recording stream processing |
| **Analysis Service** | 8002 | Gaze/head position analysis |
| **Webcam Service** | 8003 | Webcam stream processing |
| **Audio Service** | 8004 | Audio stream processing + analysis |
| **Keystroke Service** | 8005 | Keystroke dynamics analysis |
| **Frontend** | 3000 | React application (internal) |
| **Nginx** | 80/443 | Reverse proxy (external) |

## Prerequisites

On your VPS, install:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Install Git
sudo apt install git -y
```

## Clone Repository

```bash
cd /opt
sudo git clone https://github.com/your-username/tcc.git
cd tcc
sudo chown -R $USER:$USER .
```

## Environment Configuration

### 1. Backend Environment

Create `/opt/tcc/back/.env`:

```env
# Database
DATABASE_URL=postgresql://tcc_user:secure_password_here@postgres:5432/tcc_db

# Firebase (get from Firebase Console)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/...

# Security
SECRET_KEY=generate-a-long-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Judge0 (for code execution)
JUDGE0_URL=http://judge0:2358
JUDGE0_API_KEY=your-judge0-api-key
```

### 2. Frontend Environment

Create `/opt/tcc/front/.env.production`:

```env
VITE_API_BASE_URL=/api
VITE_RECORDING_SERVICE_URL=/api/recording
VITE_ANALYSIS_SERVICE_URL=/api/analysis
VITE_WEBCAM_SERVICE_URL=/api/webcam
VITE_AUDIO_SERVICE_URL=/api/audio
VITE_KEYSTROKE_SERVICE_URL=/api/keystroke

# Firebase Web Config (get from Firebase Console)
VITE_FIREBASE_API_KEY=AIzaSy...
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123:web:abc...
```

### 3. PostgreSQL Configuration

Create `/opt/tcc/postgres/.env`:

```env
POSTGRES_USER=tcc_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=tcc_db
```

## Docker Compose Setup

The `docker-compose.yml` is already configured. Key points:

- **Volumes**: Persistent data stored in `/opt/tcc/data/`
- **Networks**: All services on internal `tcc-network`
- **Health Checks**: Services wait for dependencies
- **Nginx**: Exposes only port 80/443 externally

## Deployment Steps

### 1. Create Required Directories

```bash
cd /opt/tcc
mkdir -p data/recordings data/webcam_recordings data/audio_recordings
mkdir -p logs
```

### 2. Build and Start Services

```bash
# Build all images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 3. Initialize Database

```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Create initial admin user (optional)
docker-compose exec backend python -m scripts.create_admin
```

## Nginx Configuration

The `front/nginx.conf` is already configured with all proxy routes:

- `/api/` → Main API (port 8000)
- `/api/recording/` → Recording Service (port 8001) + WebSocket
- `/api/analysis/` → Analysis Service (port 8002)
- `/api/webcam/` → Webcam Service (port 8003) + WebSocket
- `/api/audio/` → Audio Service (port 8004) + WebSocket
- `/api/keystroke/` → Keystroke Service (port 8005)

All routes:
- Strip the prefix (e.g., `/api/recording/` → `/`)
- Forward headers (Host, X-Real-IP, X-Forwarded-For)
- Support WebSocket upgrades for streaming services
- Have appropriate timeouts (120s-300s)

## SSL/HTTPS Setup (Optional but Recommended)

### Using Certbot (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal is configured automatically
sudo certbot renew --dry-run
```

### Manual SSL Configuration

Update `front/nginx.conf`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # ... rest of configuration
}
```

Then rebuild frontend:

```bash
docker-compose build frontend
docker-compose up -d frontend
```

## Monitoring and Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f recording-service
docker-compose logs -f analysis-service

# Last 100 lines
docker-compose logs --tail=100
```

### Check Service Health

```bash
# Container status
docker-compose ps

# Resource usage
docker stats

# Disk usage
docker system df
```

### Access Service Endpoints

```bash
# Health checks (from VPS)
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health

# From outside (through nginx)
curl https://your-domain.com/api/health
```

## Updates and Maintenance

### Update Code

```bash
cd /opt/tcc
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Or specific service
docker-compose build backend
docker-compose up -d backend
```

### Database Backup

```bash
# Backup
docker-compose exec postgres pg_dump -U tcc_user tcc_db > backup_$(date +%Y%m%d).sql

# Restore
cat backup_20240101.sql | docker-compose exec -T postgres psql -U tcc_user tcc_db
```

### Clean Up Old Data

```bash
# Remove old recordings (older than 30 days)
find /opt/tcc/data/recordings -type f -mtime +30 -delete
find /opt/tcc/data/webcam_recordings -type f -mtime +30 -delete
find /opt/tcc/data/audio_recordings -type f -mtime +30 -delete

# Remove old logs (older than 7 days)
find /opt/tcc/logs -type f -mtime +7 -delete

# Docker cleanup
docker system prune -a --volumes -f
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs service-name

# Check if port is in use
sudo netstat -tulpn | grep :8000

# Restart specific service
docker-compose restart service-name

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U tcc_user -d tcc_db -c "SELECT 1;"
```

### Nginx 502 Bad Gateway

```bash
# Check if backend services are running
docker-compose ps

# Check nginx logs
docker-compose logs frontend

# Test backend directly
curl http://localhost:8000/health

# Restart nginx
docker-compose restart frontend
```

### Storage Full

```bash
# Check disk usage
df -h
docker system df

# Clean up
docker system prune -a --volumes
find /opt/tcc/data -type f -mtime +30 -delete
```

## Firewall Configuration

```bash
# Allow SSH (important - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## Performance Tuning

### Increase File Upload Limits

In `front/nginx.conf`:

```nginx
http {
    client_max_body_size 100M;
    client_body_timeout 300s;
}
```

### PostgreSQL Tuning

In `docker-compose.yml`, add to postgres service:

```yaml
command:
  - "postgres"
  - "-c"
  - "max_connections=200"
  - "-c"
  - "shared_buffers=256MB"
  - "-c"
  - "effective_cache_size=1GB"
```

### Docker Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
```

## Support

For issues, check:
- **Logs**: `docker-compose logs -f`
- **Documentation**: `/docs/` folder
- **GitHub Issues**: https://github.com/your-username/tcc/issues

## Post-Deployment Checklist

- [ ] All services running (`docker-compose ps`)
- [ ] Database initialized and accessible
- [ ] Frontend accessible via domain/IP
- [ ] SSL certificate installed and auto-renewal configured
- [ ] Firewall configured (ports 22, 80, 443 only)
- [ ] Backup script configured in cron
- [ ] Monitoring/alerting configured (optional)
- [ ] Environment variables secured (not in git)
- [ ] Test complete exam flow (create prova, student submission, recording, analysis)
- [ ] Test all 3 types of analysis (gaze, audio, keystroke)
- [ ] Verify video playback works

## Production Recommendations

1. **Security**:
   - Use strong passwords for PostgreSQL
   - Keep environment files secure (chmod 600)
   - Enable SSL/HTTPS
   - Use firewall (ufw)
   - Keep Docker and system updated

2. **Backups**:
   - Daily database backups to external storage
   - Weekly full system backup
   - Test restore procedures

3. **Monitoring**:
   - Set up Prometheus + Grafana (optional)
   - Configure email alerts for service failures
   - Monitor disk usage

4. **Scaling** (if needed):
   - Use Docker Swarm or Kubernetes
   - Separate database server
   - Use object storage (S3) for recordings
   - Add load balancer for multiple frontend instances
