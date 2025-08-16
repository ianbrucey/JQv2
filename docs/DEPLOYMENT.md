# JQv2 Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the JQv2 Legal Document Management System in various environments, from local development to production deployments.

## Prerequisites

### System Requirements

#### Minimum Requirements
- **OS**: macOS 10.15+, Ubuntu 18.04+, Windows 10+ (with WSL2)
- **Python**: 3.13 or higher
- **Node.js**: 18.0 or higher
- **Memory**: 4GB RAM
- **Storage**: 10GB available space
- **tmux**: Latest version (for LocalRuntime)

#### Recommended Requirements
- **OS**: macOS 12+, Ubuntu 20.04+
- **Python**: 3.13+
- **Node.js**: 20.0+
- **Memory**: 8GB+ RAM
- **Storage**: 50GB+ available space
- **CPU**: 4+ cores

### Dependencies

#### Required System Dependencies
```bash
# macOS
brew install tmux python@3.13 node

# Ubuntu/Debian
sudo apt update
sudo apt install tmux python3.13 python3.13-venv nodejs npm

# CentOS/RHEL
sudo yum install tmux python3.13 nodejs npm
```

#### Optional Dependencies
```bash
# Docker (for development runtime)
# macOS
brew install docker

# Ubuntu
sudo apt install docker.io docker-compose

# Git (for version control)
sudo apt install git
```

## Local Development Setup

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ianbrucey/JQv2.git
cd JQv2

# 2. Set up Python environment
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install --upgrade pip
pip install -e .

# 4. Set up frontend
cd frontend
npm install
npm run build
cd ..

# 5. Configure environment
export LEGAL_WORKSPACE_ROOT=/tmp/legal_workspace
export DRAFT_SYSTEM_PATH=/tmp/draft_system
mkdir -p $LEGAL_WORKSPACE_ROOT $DRAFT_SYSTEM_PATH

# 6. Initialize legal system
python scripts/setup_legal_system.py

# 7. Start the server
LEGAL_WORKSPACE_ROOT=/tmp/legal_workspace DRAFT_SYSTEM_PATH=/tmp/draft_system \
python -m uvicorn openhands.server.listen:app --host 127.0.0.1 --port 3000
```

### Environment Configuration

Create a `.env.local` file for local development:

```bash
# .env.local
# Legal Workspace Configuration
LEGAL_WORKSPACE_ROOT=/tmp/legal_workspace
DRAFT_SYSTEM_PATH=/tmp/draft_system

# OpenHands Configuration
WORKSPACE_BASE=/tmp/legal_workspace
DEFAULT_WORKSPACE_MOUNT_PATH_IN_SANDBOX=/workspace

# File Storage Configuration
FILE_STORE=local
FILE_STORE_PATH=/tmp/legal_workspace/files

# Runtime Configuration
OPENHANDS_RUNTIME=local
OPENHANDS_ENABLE_AUTO_RUNTIME=true

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
```

### Development Workflow

```bash
# Start development server with hot reload
cd frontend
npm run dev &

# Start backend with auto-reload
cd ..
source venv/bin/activate
uvicorn openhands.server.listen:app --reload --host 127.0.0.1 --port 3000
```

## Production Deployment

### Server Setup

#### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.13 python3.13-venv nodejs npm tmux nginx supervisor

# Create application user
sudo useradd -m -s /bin/bash openhands
sudo usermod -aG sudo openhands
```

#### 2. Application Deployment

```bash
# Switch to application user
sudo su - openhands

# Clone repository
git clone https://github.com/ianbrucey/JQv2.git /opt/jqv2
cd /opt/jqv2

# Set up Python environment
python3.13 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .

# Build frontend
cd frontend
npm ci --production
npm run build
cd ..

# Create production directories
sudo mkdir -p /var/lib/jqv2/{legal_workspace,draft_system,logs}
sudo chown -R openhands:openhands /var/lib/jqv2
```

#### 3. Configuration

Create production configuration:

```bash
# /opt/jqv2/.env.production
# Legal Workspace Configuration
LEGAL_WORKSPACE_ROOT=/var/lib/jqv2/legal_workspace
DRAFT_SYSTEM_PATH=/var/lib/jqv2/draft_system

# OpenHands Configuration
WORKSPACE_BASE=/var/lib/jqv2/legal_workspace
DEFAULT_WORKSPACE_MOUNT_PATH_IN_SANDBOX=/workspace

# File Storage Configuration
FILE_STORE=local
FILE_STORE_PATH=/var/lib/jqv2/legal_workspace/files

# Runtime Configuration
OPENHANDS_RUNTIME=local
OPENHANDS_ENABLE_AUTO_RUNTIME=true

# Production Settings
DEBUG=false
LOG_LEVEL=WARNING
LOG_FILE=/var/lib/jqv2/logs/app.log

# Security Settings
SECRET_KEY=your-secret-key-change-this
ALLOWED_HOSTS=your-domain.com,localhost
```

#### 4. Process Management with Supervisor

Create supervisor configuration:

```bash
# /etc/supervisor/conf.d/jqv2.conf
[program:jqv2]
command=/opt/jqv2/venv/bin/python -m uvicorn openhands.server.listen:app --host 127.0.0.1 --port 3000
directory=/opt/jqv2
user=openhands
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/lib/jqv2/logs/app.log
environment=LEGAL_WORKSPACE_ROOT="/var/lib/jqv2/legal_workspace",DRAFT_SYSTEM_PATH="/var/lib/jqv2/draft_system"
```

Start the service:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start jqv2
```

#### 5. Reverse Proxy with Nginx

Configure Nginx:

```nginx
# /etc/nginx/sites-available/jqv2
server {
    listen 80;
    server_name your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

    # Main application
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static/ {
        alias /opt/jqv2/frontend/dist/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # File uploads
    client_max_body_size 100M;
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/jqv2 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Docker Deployment

### Docker Compose Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  jqv2:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - LEGAL_WORKSPACE_ROOT=/app/data/legal_workspace
      - DRAFT_SYSTEM_PATH=/app/data/draft_system
      - WORKSPACE_BASE=/app/data/legal_workspace
      - FILE_STORE_PATH=/app/data/legal_workspace/files
    volumes:
      - jqv2_data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock  # For Docker runtime support
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - jqv2
    restart: unless-stopped

volumes:
  jqv2_data:
```

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tmux \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Create application directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend and build
COPY frontend/ ./frontend/
RUN cd frontend && npm ci && npm run build

# Copy application code
COPY . .

# Install application
RUN pip install -e .

# Create data directories
RUN mkdir -p /app/data/{legal_workspace,draft_system,logs}

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Start application
CMD ["python", "-m", "uvicorn", "openhands.server.listen:app", "--host", "0.0.0.0", "--port", "3000"]
```

### Deploy with Docker Compose

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f jqv2

# Scale services
docker-compose up -d --scale jqv2=3

# Update deployment
docker-compose pull
docker-compose up -d
```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS

1. **Create ECS Cluster**:
```bash
aws ecs create-cluster --cluster-name jqv2-cluster
```

2. **Create Task Definition**:
```json
{
  "family": "jqv2-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "jqv2",
      "image": "your-account.dkr.ecr.region.amazonaws.com/jqv2:latest",
      "portMappings": [
        {
          "containerPort": 3000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LEGAL_WORKSPACE_ROOT",
          "value": "/app/data/legal_workspace"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/jqv2",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

3. **Create Service**:
```bash
aws ecs create-service \
  --cluster jqv2-cluster \
  --service-name jqv2-service \
  --task-definition jqv2-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

### Kubernetes Deployment

#### Deployment Manifest

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jqv2
  labels:
    app: jqv2
spec:
  replicas: 3
  selector:
    matchLabels:
      app: jqv2
  template:
    metadata:
      labels:
        app: jqv2
    spec:
      containers:
      - name: jqv2
        image: jqv2:latest
        ports:
        - containerPort: 3000
        env:
        - name: LEGAL_WORKSPACE_ROOT
          value: "/app/data/legal_workspace"
        - name: DRAFT_SYSTEM_PATH
          value: "/app/data/draft_system"
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: jqv2-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: jqv2-service
spec:
  selector:
    app: jqv2
  ports:
  - protocol: TCP
    port: 80
    targetPort: 3000
  type: LoadBalancer
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: jqv2-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
```

Deploy to Kubernetes:

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods -l app=jqv2
kubectl get services jqv2-service
```

## Monitoring and Maintenance

### Health Checks

The application provides health check endpoints:

```bash
# Basic health check
curl http://localhost:3000/api/health

# Detailed system status
curl http://localhost:3000/api/legal/system/status
```

### Logging Configuration

Configure structured logging:

```python
# logging.conf
[loggers]
keys=root,openhands,legal

[handlers]
keys=console,file,syslog

[formatters]
keys=detailed,simple

[logger_root]
level=INFO
handlers=console,file

[logger_openhands]
level=INFO
handlers=file
qualname=openhands
propagate=0

[logger_legal]
level=INFO
handlers=file,syslog
qualname=openhands.server.legal
propagate=0

[handler_console]
class=StreamHandler
level=INFO
formatter=simple
args=(sys.stdout,)

[handler_file]
class=handlers.RotatingFileHandler
level=INFO
formatter=detailed
args=('/var/lib/jqv2/logs/app.log', 'a', 10485760, 5)

[handler_syslog]
class=handlers.SysLogHandler
level=WARNING
formatter=simple
args=(('localhost', 514),)

[formatter_simple]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_detailed]
format=%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s
```

### Backup Strategy

Implement automated backups:

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/var/backups/jqv2"
DATA_DIR="/var/lib/jqv2"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup legal workspace data
tar -czf "$BACKUP_DIR/legal_workspace_$DATE.tar.gz" -C "$DATA_DIR" legal_workspace

# Backup draft system
tar -czf "$BACKUP_DIR/draft_system_$DATE.tar.gz" -C "$DATA_DIR" draft_system

# Backup logs
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" -C "$DATA_DIR" logs

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Performance Monitoring

Set up monitoring with Prometheus and Grafana:

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'jqv2'
    static_configs:
      - targets: ['localhost:3000']
    metrics_path: '/api/metrics'
    scrape_interval: 5s
```

## Troubleshooting

### Common Issues

1. **tmux not found**:
```bash
# Install tmux
sudo apt install tmux  # Ubuntu
brew install tmux      # macOS
```

2. **Permission denied on workspace**:
```bash
# Fix permissions
sudo chown -R $USER:$USER /tmp/legal_workspace
chmod -R 755 /tmp/legal_workspace
```

3. **Port already in use**:
```bash
# Find process using port 3000
lsof -i :3000
# Kill process
kill -9 <PID>
```

4. **Frontend build fails**:
```bash
# Clear npm cache
npm cache clean --force
# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Log Analysis

Common log patterns to monitor:

```bash
# Check for runtime selection
grep "Legal case detected" /var/lib/jqv2/logs/app.log

# Monitor startup times
grep "startup completed" /var/lib/jqv2/logs/app.log

# Check for errors
grep "ERROR" /var/lib/jqv2/logs/app.log | tail -20
```

## Security Considerations

### Production Security Checklist

- [ ] Use HTTPS with valid SSL certificates
- [ ] Configure firewall rules
- [ ] Set up fail2ban for brute force protection
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Access logging and monitoring
- [ ] User authentication and authorization
- [ ] Network segmentation
- [ ] Regular security audits

### Environment Security

```bash
# Set secure file permissions
chmod 600 .env.production
chown openhands:openhands .env.production

# Secure workspace directories
chmod 750 /var/lib/jqv2/legal_workspace
chown -R openhands:openhands /var/lib/jqv2
```

This deployment guide provides comprehensive instructions for deploying JQv2 in various environments while maintaining security and performance best practices.
