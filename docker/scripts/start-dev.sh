#!/bin/bash

# Start development environment with Docker Compose

set -e

echo "🔬 Starting ArXiv Paper Collector Development Environment"
echo "========================================================"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    if ! command -v docker &> /dev/null; then
        echo "❌ Docker is not installed"
        exit 1
    fi
    # Use docker compose (newer syntax)
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# Stop any existing containers
echo "🧹 Stopping existing containers..."
$DOCKER_COMPOSE down

# Build and start services
echo "🏗️  Building and starting services..."
$DOCKER_COMPOSE up --build -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until $DOCKER_COMPOSE exec db pg_isready -U postgres; do
    echo "  Database is unavailable - sleeping"
    sleep 2
done
echo "✅ Database is ready!"

# Start backend
echo "🚀 Starting backend..."
$DOCKER_COMPOSE up --build backend

echo "🎉 Development environment is ready!"
echo ""
echo "📍 Available endpoints:"
echo "  • Backend API: http://localhost:8000/api/"
echo "  • Django Admin: http://localhost:8000/admin/"
echo "  • Database: localhost:5432 (postgres/postgres)"
echo "  • Redis: localhost:6379"
echo ""
echo "🔧 Useful commands:"
echo "  • View logs: $DOCKER_COMPOSE logs -f backend"
echo "  • Run migrations: $DOCKER_COMPOSE exec backend python backend/manage.py migrate"
echo "  • Create superuser: $DOCKER_COMPOSE exec backend python backend/manage.py createsuperuser"
echo "  • Stop everything: $DOCKER_COMPOSE down" 