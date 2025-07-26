#!/bin/bash

# ArXiv Paper Collector - Google Cloud Deployment Script

set -e

PROJECT_ID="zesameri"
SERVICE_NAME="arxiv-paper-collector"
REGION="us-central1"
DB_INSTANCE_NAME="arxiv-papers-db"
DB_NAME="arxiv_papers"
DB_USER="postgres"

echo "🚀 Deploying ArXiv Paper Collector to Google Cloud"
echo "=================================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Set project
echo "📋 Setting up project configuration..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔌 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    sql-component.googleapis.com \
    sqladmin.googleapis.com \
    artifactregistry.googleapis.com

# Create Cloud SQL instance (if it doesn't exist)
echo "🗄️  Setting up Cloud SQL PostgreSQL..."
if ! gcloud sql instances describe $DB_INSTANCE_NAME --quiet 2>/dev/null; then
    echo "Creating new Cloud SQL instance..."
    gcloud sql instances create $DB_INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-size=10GB \
        --storage-type=SSD \
        --no-backup
    
    echo "Creating database..."
    gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME
    
    echo "Setting database password..."
    echo "Please set a password for the database user:"
    gcloud sql users set-password $DB_USER --instance=$DB_INSTANCE_NAME --prompt-for-password
else
    echo "Cloud SQL instance already exists: $DB_INSTANCE_NAME"
fi

# Get database connection string
echo "📡 Getting database connection info..."
CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE_NAME --format="value(connectionName)")
echo "Connection name: $CONNECTION_NAME"

# Build and deploy to Cloud Run
echo "🏗️  Building and deploying to Cloud Run..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME --file docker/Dockerfile .

# Generate random secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 2Gi \
    --cpu 2 \
    --set-env-vars="
DEBUG=False,
SECRET_KEY=$SECRET_KEY,
ALLOWED_HOSTS=*,
PUBMED_EMAIL=your-email@example.com
" \
    --set-secrets="DATABASE_PASSWORD=db-password:latest" \
    --update-env-vars="DATABASE_URL=postgresql://$DB_USER:\$DATABASE_PASSWORD@//cloudsql/$CONNECTION_NAME/$DB_NAME" \
    --add-cloudsql-instances $CONNECTION_NAME \
    --max-instances 10

# Run migrations
echo "🔄 Running database migrations..."
gcloud run jobs create migrate-job \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
    --region $REGION \
    --set-env-vars="
DEBUG=False,
DATABASE_URL=postgresql://$DB_USER:PASSWORD@//cloudsql/$CONNECTION_NAME/$DB_NAME
" \
    --add-cloudsql-instances $CONNECTION_NAME \
    --command python,backend/manage.py,migrate

echo ""
echo "🎉 Deployment Complete!"
echo "======================="

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)")
echo "🌐 Your ArXiv Paper Collector is live at:"
echo "   $SERVICE_URL"
echo ""
echo "📋 Next steps:"
echo "1. Update the DATABASE_URL with the actual password"
echo "2. Set your PUBMED_EMAIL in the environment variables"
echo "3. Create a superuser: gcloud run jobs execute migrate-job --region=$REGION"
echo "4. Visit $SERVICE_URL/admin to access Django admin"
echo "5. Use $SERVICE_URL/api/ for the REST API"
echo ""
echo "💡 Useful commands:"
echo "   View logs: gcloud run services logs read $SERVICE_NAME --region=$REGION"
echo "   Update env: gcloud run services update $SERVICE_NAME --region=$REGION --set-env-vars=KEY=VALUE"
echo "   Scale down: gcloud run services update $SERVICE_NAME --region=$REGION --max-instances=0" 