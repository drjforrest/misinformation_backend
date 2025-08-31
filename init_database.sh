#!/bin/bash

# Database initialization script for Health Misinformation Research Platform
# Sets up PostgreSQL with pgvector extension and runs initial migrations

set -e  # Exit on any error

echo "🚀 Initializing Health Misinformation Research Database..."
echo "=================================================="

# Check if PostgreSQL is running
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL not found. Please install PostgreSQL first:"
    echo "   brew install postgresql"
    echo "   brew services start postgresql"
    exit 1
fi

# Database configuration
DB_NAME="misinformation_research"
DB_USER="${DB_USER:-$(whoami)}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "📊 Database Configuration:"
echo "   • Database: $DB_NAME"
echo "   • User: $DB_USER"
echo "   • Host: $DB_HOST:$DB_PORT"
echo ""

# Check if database exists
if psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "🔍 Database '$DB_NAME' already exists."
    read -p "Do you want to recreate it? This will delete all existing data! (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Dropping existing database..."
        dropdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
    else
        echo "✅ Using existing database."
    fi
fi

# Create database if it doesn't exist
if ! psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo "🆕 Creating database '$DB_NAME'..."
    createdb -h $DB_HOST -p $DB_PORT -U $DB_USER $DB_NAME
    echo "✅ Database created successfully!"
fi

# Connect to database and enable pgvector extension
echo "🧬 Enabling pgvector extension..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS vector;"

if [ $? -eq 0 ]; then
    echo "✅ pgvector extension enabled!"
else
    echo "❌ Failed to enable pgvector extension. Make sure pgvector is installed:"
    echo "   brew install pgvector"
    exit 1
fi

# Update .env file with database URL
echo "⚙️  Updating .env configuration..."
ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
fi

# Update database URL in .env
DB_URL="postgresql://$DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
if grep -q "DATABASE_URL=" .env; then
    # Update existing line
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|DATABASE_URL=.*|DATABASE_URL=$DB_URL|" .env
    else
        # Linux
        sed -i "s|DATABASE_URL=.*|DATABASE_URL=$DB_URL|" .env
    fi
else
    # Add new line
    echo "DATABASE_URL=$DB_URL" >> .env
fi

echo "✅ Database URL updated in .env: $DB_URL"

# Initialize Alembic if not already done
if [ ! -f "alembic.ini" ]; then
    echo "🔧 Initializing Alembic..."
    alembic init alembic
fi

# Update alembic.ini with correct database URL
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|sqlalchemy.url = .*|sqlalchemy.url = $DB_URL|" alembic.ini
else
    # Linux
    sed -i "s|sqlalchemy.url = .*|sqlalchemy.url = $DB_URL|" alembic.ini
fi

# Generate initial migration
echo "📝 Generating initial database migration..."
alembic revision --autogenerate -m "Initial database schema with pgvector support"

# Run migrations
echo "🚀 Running database migrations..."
alembic upgrade head

# Verify pgvector is working
echo "🧪 Testing pgvector functionality..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "SELECT '[1,2,3]'::vector;"

if [ $? -eq 0 ]; then
    echo "✅ pgvector is working correctly!"
else
    echo "⚠️  pgvector test failed, but database is set up."
fi

echo ""
echo "🎉 Database initialization complete!"
echo "=================================================="
echo "📋 Next steps:"
echo "   1. Update your Reddit API credentials in .env"
echo "   2. Run: python proof_of_concept.py"
echo "   3. Or: python main.py demo --limit 50"
echo ""
echo "🔗 Database connection: $DB_URL"
echo "📁 View your data with: psql $DB_URL"
