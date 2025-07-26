# Docker Setup for ArXiv Paper Collector 🐳

This directory contains Docker configuration for running the ArXiv Paper Collector in both development and production environments.

## 📁 Structure

```
docker/
├── Dockerfile              # Multi-stage Docker image
├── nginx.conf              # Development Nginx config
├── nginx.prod.conf         # Production Nginx config
├── init-db.sql             # PostgreSQL initialization
├── env.development         # Development environment variables
├── env.production          # Production environment template
└── scripts/
    ├── start-dev.sh         # Start development environment
    └── manage-db.sh         # Database management utilities
```

## 🚀 Quick Start

### Development Environment

1. **Start everything:**
   ```bash
   ./docker/scripts/start-dev.sh
   ```

2. **Or manually:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - **API**: http://localhost:8000/api/
   - **Admin**: http://localhost:8000/admin/
   - **Database**: localhost:5432 (postgres/postgres)

### Production Deployment

1. **Copy and configure environment:**
   ```bash
   cp docker/env.production .env
   # Edit .env with your production values
   ```

2. **Deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml up --build -d
   ```

## 🔧 Services

### Development (`docker-compose.yml`)

| Service | Port | Description |
|---------|------|-------------|
| **backend** | 8000 | Django API with hot reload |
| **db** | 5432 | PostgreSQL 15 database |
| **redis** | 6379 | Redis cache |
| **nginx** | 80 | Reverse proxy (optional) |
| **frontend** | 3000 | React/Vue app (future) |

### Production (`docker-compose.prod.yml`)

| Service | Port | Description |
|---------|------|-------------|
| **backend** | 8080 | Django with Gunicorn |
| **nginx** | 80/443 | Production reverse proxy |

## 📝 Environment Variables

### Development

Copy `docker/env.development` to `.env` or set these variables:

```bash
DEBUG=True
SECRET_KEY=dev-secret-key
POSTGRES_DB=arxiv_papers
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
PUBMED_EMAIL=your-email@example.com
```

### Production

**Required variables:**

```bash
DEBUG=False
SECRET_KEY=your-super-secret-key
DATABASE_URL=postgresql://user:password@host:5432/database
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
GCP_PROJECT_ID=your-gcp-project
PUBMED_EMAIL=your-email@example.com
```

## 🛠️ Database Management

Use the database management script for common tasks:

```bash
# Run migrations
./docker/scripts/manage-db.sh migrate

# Create new migrations
./docker/scripts/manage-db.sh makemigrations

# Create superuser
./docker/scripts/manage-db.sh superuser

# View database status
./docker/scripts/manage-db.sh status

# Backup database
./docker/scripts/manage-db.sh backup

# Restore from backup
./docker/scripts/manage-db.sh restore backup_20231226_143022.sql

# Open PostgreSQL shell
./docker/scripts/manage-db.sh shell

# Open Django shell
./docker/scripts/manage-db.sh django-shell

# Reset database (DANGER!)
./docker/scripts/manage-db.sh reset
```

## 🎯 Common Development Tasks

### Collect Papers via API

```bash
# Start the development environment
./docker/scripts/start-dev.sh

# In another terminal, collect papers
curl -X POST http://localhost:8000/api/collect/authors/ \
  -H "Content-Type: application/json" \
  -d '{
    "authors": ["Drew Endy", "Christopher Voigt"],
    "max_papers": 20,
    "collection_name": "Synthetic Biology Pioneers"
  }'
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Execute Commands in Containers

```bash
# Django shell
docker-compose exec backend python backend/manage.py shell

# Database shell
docker-compose exec db psql -U postgres -d arxiv_papers

# Backend shell
docker-compose exec backend bash
```

## 🏗️ Building and Deployment

### Build Development Image

```bash
docker build -f docker/Dockerfile --target development -t paper-collector:dev .
```

### Build Production Image

```bash
docker build -f docker/Dockerfile --target production -t paper-collector:prod .
```

### Push to Registry

```bash
# Tag for Google Container Registry
docker tag paper-collector:prod gcr.io/YOUR_PROJECT_ID/paper-collector:latest

# Push to registry
docker push gcr.io/YOUR_PROJECT_ID/paper-collector:latest
```

## ☁️ Cloud Run Deployment

### 1. Build and Push Image

```bash
# Build for Cloud Run
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/paper-collector .

# Or use docker
docker build -f docker/Dockerfile --target production -t gcr.io/YOUR_PROJECT_ID/paper-collector .
docker push gcr.io/YOUR_PROJECT_ID/paper-collector
```

### 2. Deploy to Cloud Run

```bash
gcloud run deploy paper-collector \
  --image gcr.io/YOUR_PROJECT_ID/paper-collector \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --set-env-vars="DEBUG=False,DATABASE_URL=postgresql://..." \
  --max-instances 10
```

### 3. Set up Cloud SQL

```bash
# Create PostgreSQL instance
gcloud sql instances create paper-collector-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create arxiv_papers --instance=paper-collector-db

# Create user
gcloud sql users create paper-user --instance=paper-collector-db --password=secure-password
```

## 🔒 Security Considerations

### Development
- Default passwords are used (postgres/postgres)
- Debug mode is enabled
- CORS is open for local development

### Production
- Change all default passwords
- Use environment variables for secrets
- Enable SSL/TLS
- Configure proper CORS origins
- Use Cloud SQL with SSL
- Enable security headers in Nginx

## 🐛 Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Wait for database to be ready
./docker/scripts/manage-db.sh status
```

**Permission errors:**
```bash
# Make scripts executable
chmod +x docker/scripts/*.sh

# Fix volume permissions
docker-compose exec backend chown -R appuser:appuser /app
```

**Out of disk space:**
```bash
# Clean up Docker
docker system prune -a

# Remove unused volumes
docker volume prune
```

**Port conflicts:**
```bash
# Check what's using the port
lsof -i :8000

# Change ports in docker-compose.yml
```

### Performance Tuning

**PostgreSQL:**
- Adjust `shared_buffers` in `init-db.sql`
- Monitor query performance
- Consider connection pooling for production

**Django:**
- Enable caching with Redis
- Use database indexes appropriately
- Monitor memory usage

**Docker:**
- Use multi-stage builds to reduce image size
- Consider using Alpine images for smaller footprint
- Use Docker BuildKit for faster builds

## 📊 Monitoring

### Health Checks

All services include health checks:

```bash
# Check service health
docker-compose ps

# Manual health check
curl http://localhost:8000/api/stats/
```

### Logs and Metrics

```bash
# Export logs
docker-compose logs --no-color > app.log

# Monitor resource usage
docker stats

# Check container resource limits
docker-compose exec backend cat /sys/fs/cgroup/memory/memory.limit_in_bytes
```

## 🔄 Updates and Maintenance

### Update Dependencies

```bash
# Update Poetry dependencies
poetry update

# Rebuild containers
docker-compose build --no-cache
```

### Database Migrations

```bash
# Always backup before migrations
./docker/scripts/manage-db.sh backup

# Run migrations
./docker/scripts/manage-db.sh migrate
```

### Rolling Updates (Production)

```bash
# Build new image
docker build -f docker/Dockerfile --target production -t paper-collector:new .

# Update compose file with new image
# Then rolling update
docker-compose -f docker-compose.prod.yml up -d --no-deps backend
```

---

## 🆘 Need Help?

- Check the main project README.md
- Review Docker logs: `docker-compose logs`
- Check service health: `docker-compose ps`
- Open an issue on GitHub with logs and configuration details 