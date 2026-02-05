#!/bin/bash
# Database initialization script.

set -e

COMPOSE_CMD="${COMPOSE_CMD:-docker-compose}"
DB_CONTAINER="${DB_CONTAINER:-procurement-ai-db}"
DB_USER="${DB_USER:-procurement}"
DB_NAME="${DB_NAME:-procurement}"

echo "Initializing Procurement AI database"

if ! $COMPOSE_CMD ps postgres | grep -q "Up"; then
    echo "PostgreSQL container is not running"
    echo "Starting PostgreSQL..."
    $COMPOSE_CMD up -d postgres
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
fi

echo "PostgreSQL is running"

echo "Running database migrations"
alembic upgrade head

echo "Database initialization complete"
echo ""
echo "Next steps:"
echo "  1. Setup API org: ./scripts/setup_api_test.sh"
echo "  2. Start server: ./scripts/start_web.sh"
