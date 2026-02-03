#!/bin/bash
# Database initialization script

set -e

echo "🚀 Initializing Procurement AI Database..."
echo ""

# Check if PostgreSQL container is running
if ! docker-compose ps postgres | grep -q "Up"; then
    echo "❌ PostgreSQL container is not running"
    echo "   Starting PostgreSQL..."
    docker-compose up -d postgres
    echo "   Waiting for PostgreSQL to be ready..."
    sleep 5
fi

echo "✓ PostgreSQL is running"

# Create database if it doesn't exist
echo ""
echo "📦 Creating database 'procurement_ai'..."
docker exec procurement-ai-db psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'procurement_ai'" | grep -q 1 || \
docker exec procurement-ai-db psql -U postgres -c "CREATE DATABASE procurement_ai;"

echo "✓ Database 'procurement_ai' created/verified"

# Run migrations
echo ""
echo "🔄 Running database migrations..."
alembic upgrade head

echo ""
echo "✅ Database initialization complete!"
echo ""
echo "Next steps:"
echo "  1. Seed data: python examples/seed_database.py"
echo "  2. Run example: python examples/database_usage.py"
