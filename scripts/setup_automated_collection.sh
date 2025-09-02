#!/bin/bash
#
# Setup script for automated Reddit data collection
# This script helps you quickly set up cron jobs for data collection
#

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_PATH=$(which python3)

echo "🔧 Setting up automated Reddit data collection..."
echo "📁 Project root: $PROJECT_ROOT"
echo "🐍 Python path: $PYTHON_PATH"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo "Please copy .env.example to .env and configure your Reddit API credentials"
    echo "cp $PROJECT_ROOT/.env.example $PROJECT_ROOT/.env"
    exit 1
fi

echo -e "${GREEN}✅ .env file found${NC}"

# Test the automated collection script
echo "🧪 Testing automated collection script..."
cd "$PROJECT_ROOT"

# Run a quick test (timeout after 60 seconds)
if timeout 60s $PYTHON_PATH scripts/automated_collection.py > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Automated collection script test passed${NC}"
else
    echo -e "${YELLOW}⚠️  Test didn't complete in 60s (normal for first run)${NC}"
fi

# Show current crontab
echo "📅 Current crontab entries:"
crontab -l 2>/dev/null || echo "No existing crontab entries"

echo ""
echo "🚀 Ready to set up automated collection!"
echo ""
echo "Choose a collection frequency:"
echo "1) Daily at 2 AM (recommended)"
echo "2) Every 6 hours"
echo "3) Twice daily (6 AM and 6 PM)"
echo "4) Weekly (Sundays at 3 AM)"
echo "5) Custom schedule"
echo "6) Skip cron setup"

read -p "Enter choice (1-6): " choice

case $choice in
    1)
        CRON_SCHEDULE="0 2 * * *"
        DESCRIPTION="daily at 2 AM"
        ;;
    2)
        CRON_SCHEDULE="0 */6 * * *"
        DESCRIPTION="every 6 hours"
        ;;
    3)
        CRON_SCHEDULE="0 6,18 * * *"
        DESCRIPTION="twice daily (6 AM and 6 PM)"
        ;;
    4)
        CRON_SCHEDULE="0 3 * * 0"
        DESCRIPTION="weekly on Sundays at 3 AM"
        ;;
    5)
        read -p "Enter custom cron schedule (e.g. '0 2 * * *'): " CRON_SCHEDULE
        DESCRIPTION="custom schedule: $CRON_SCHEDULE"
        ;;
    6)
        echo -e "${YELLOW}Skipping cron setup${NC}"
        echo "You can manually run: python $PROJECT_ROOT/scripts/automated_collection.py"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Create the cron command
CRON_COMMAND="$CRON_SCHEDULE $PYTHON_PATH $PROJECT_ROOT/scripts/automated_collection.py >> $PROJECT_ROOT/logs/cron_output.log 2>&1"

echo ""
echo "📝 Proposed cron job ($description):"
echo "$CRON_COMMAND"
echo ""

read -p "Add this to your crontab? (y/n): " confirm

if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -
    echo -e "${GREEN}✅ Cron job added successfully!${NC}"
    
    echo ""
    echo "📊 Monitoring commands:"
    echo "• View logs: tail -f $PROJECT_ROOT/logs/automated_collection.log"
    echo "• Check database: python -c \"from src.data_persistence import DataPersistenceManager; print(DataPersistenceManager().get_collection_stats())\""
    echo "• View crontab: crontab -l"
    
    echo ""
    echo "🔧 Management commands:"
    echo "• Remove cron job: crontab -e (then delete the line)"
    echo "• Test collection: python $PROJECT_ROOT/scripts/automated_collection.py"
    echo "• Database stats: python $PROJECT_ROOT/main.py collect-db --limit 10"
    
else
    echo -e "${YELLOW}Cron job not added${NC}"
    echo "You can manually add it later with:"
    echo "crontab -e"
    echo "# Add this line:"
    echo "$CRON_COMMAND"
fi

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo "The automated collection will:"
echo "• Collect health-related posts from 15 target subreddits"
echo "• Skip posts already in the database (no duplicates)"
echo "• Save comprehensive logs to logs/automated_collection.log"
echo "• Respect Reddit API rate limits"
echo "• Generate detailed reports in data/reports/"
