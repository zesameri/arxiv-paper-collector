#!/bin/bash

# Database management script for ArXiv Paper Collector

set -e

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

show_help() {
    echo "Database Management Script for ArXiv Paper Collector"
    echo "=================================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  migrate          Run Django database migrations"
    echo "  makemigrations   Create new Django migrations"
    echo "  reset            Reset database (DANGER: destroys all data)"
    echo "  backup           Create database backup"
    echo "  restore [file]   Restore database from backup"
    echo "  shell            Open PostgreSQL shell"
    echo "  django-shell     Open Django shell"
    echo "  superuser        Create Django superuser"
    echo "  status           Show database status"
    echo ""
}

case "$1" in
    migrate)
        echo "🔄 Running Django migrations..."
        $DOCKER_COMPOSE exec backend python backend/manage.py migrate
        echo "✅ Migrations completed!"
        ;;
    
    makemigrations)
        echo "📝 Creating new migrations..."
        $DOCKER_COMPOSE exec backend python backend/manage.py makemigrations
        echo "✅ Migrations created!"
        ;;
    
    reset)
        echo "⚠️  WARNING: This will destroy ALL data in the database!"
        read -p "Are you sure? (type 'yes' to confirm): " confirm
        if [ "$confirm" = "yes" ]; then
            echo "🗑️  Stopping services..."
            $DOCKER_COMPOSE down
            echo "🗑️  Removing database volume..."
            docker volume rm arxiv-paper-collector_postgres_data 2>/dev/null || true
            echo "🚀 Starting fresh database..."
            $DOCKER_COMPOSE up -d db
            sleep 5
            echo "🔄 Running migrations..."
            $DOCKER_COMPOSE exec backend python backend/manage.py migrate
            echo "✅ Database reset completed!"
        else
            echo "❌ Database reset cancelled"
        fi
        ;;
    
    backup)
        timestamp=$(date +%Y%m%d_%H%M%S)
        backup_file="backup_${timestamp}.sql"
        echo "💾 Creating database backup: $backup_file"
        $DOCKER_COMPOSE exec db pg_dump -U postgres -d arxiv_papers > "$backup_file"
        echo "✅ Backup created: $backup_file"
        ;;
    
    restore)
        if [ -z "$2" ]; then
            echo "❌ Please specify backup file: $0 restore <backup_file>"
            exit 1
        fi
        if [ ! -f "$2" ]; then
            echo "❌ Backup file not found: $2"
            exit 1
        fi
        echo "🔄 Restoring database from: $2"
        cat "$2" | $DOCKER_COMPOSE exec -T db psql -U postgres -d arxiv_papers
        echo "✅ Database restored!"
        ;;
    
    shell)
        echo "🐘 Opening PostgreSQL shell..."
        $DOCKER_COMPOSE exec db psql -U postgres -d arxiv_papers
        ;;
    
    django-shell)
        echo "🐍 Opening Django shell..."
        $DOCKER_COMPOSE exec backend python backend/manage.py shell
        ;;
    
    superuser)
        echo "👤 Creating Django superuser..."
        $DOCKER_COMPOSE exec backend python backend/manage.py createsuperuser
        ;;
    
    status)
        echo "📊 Database Status:"
        echo "=================="
        $DOCKER_COMPOSE exec db psql -U postgres -d arxiv_papers -c "
            SELECT 
                'Papers' as table_name, 
                count(*) as count 
            FROM papers_paper
            UNION ALL
            SELECT 
                'Authors' as table_name, 
                count(*) as count 
            FROM papers_author
            UNION ALL
            SELECT 
                'Collaborations' as table_name, 
                count(*) as count 
            FROM papers_collaboration
            UNION ALL
            SELECT 
                'Collections' as table_name, 
                count(*) as count 
            FROM papers_collection;
        "
        ;;
    
    *)
        show_help
        ;;
esac 