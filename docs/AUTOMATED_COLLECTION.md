# Automated Data Collection Setup

This guide explains how to set up automated Reddit data collection using cron jobs for the Health Misinformation Detection Platform.

## Overview

The automated collection system provides:
- ✅ **Duplicate handling** - Skips posts already in database
- ✅ **Database persistence** - Automatically saves to PostgreSQL/SQLite
- ✅ **Error recovery** - Continues collection even if individual subreddits fail
- ✅ **Comprehensive logging** - Detailed logs for monitoring and debugging
- ✅ **Rate limiting** - Respectful API usage within Reddit's limits
- ✅ **Health monitoring** - Tracks collection success and data freshness

## Quick Start

### 1. Test the Automated Script

Before setting up cron jobs, test the automated collection script manually:

```bash
# Navigate to project directory
cd /path/to/misinformation_gay_mens_Health

# Run automated collection
python scripts/automated_collection.py
```

### 2. Verify Database Integration

Check that data is being saved to the database:

```bash
# Check collection stats
python -c "
from src.data_persistence import DataPersistenceManager
dm = DataPersistenceManager()
stats = dm.get_collection_stats()
print('Database Stats:', stats)
"
```

### 3. Set Up Cron Job

Edit your crontab:
```bash
crontab -e
```

Add one of the collection schedules below.

## Recommended Collection Frequencies

### Every 6 Hours (4x daily)
**Best for active monitoring and research**
```bash
# Collect Reddit data every 6 hours
0 */6 * * * /usr/bin/python3 /path/to/misinformation_gay_mens_Health/scripts/automated_collection.py >> /path/to/misinformation_gay_mens_Health/logs/cron_output.log 2>&1
```

### Daily at 2 AM (1x daily) 
**Recommended for most use cases**
```bash
# Collect Reddit data daily at 2 AM
0 2 * * * /usr/bin/python3 /path/to/misinformation_gay_mens_Health/scripts/automated_collection.py >> /path/to/misinformation_gay_mens_Health/logs/cron_output.log 2>&1
```

### Twice Daily (2x daily)
**Good balance of freshness and API respect**
```bash
# Collect Reddit data twice daily (6 AM and 6 PM)
0 6,18 * * * /usr/bin/python3 /path/to/misinformation_gay_mens_Health/scripts/automated_collection.py >> /path/to/misinformation_gay_mens_Health/logs/cron_output.log 2>&1
```

### Weekly (Sundays at 3 AM)
**For maintenance/validation runs**
```bash
# Weekly full collection every Sunday at 3 AM
0 3 * * 0 /usr/bin/python3 /path/to/misinformation_gay_mens_Health/scripts/automated_collection.py >> /path/to/misinformation_gay_mens_Health/logs/cron_output.log 2>&1
```

## Advanced Cron Configuration

### With Environment Variables
If you need to set environment variables in the cron job:

```bash
# Load environment and run collection
0 2 * * * cd /path/to/misinformation_gay_mens_Health && /usr/bin/env -i HOME="$HOME" PATH="/usr/local/bin:/usr/bin:/bin" /usr/bin/python3 scripts/automated_collection.py >> logs/cron_output.log 2>&1
```

### With Virtual Environment
If using a Python virtual environment:

```bash
# Activate venv and run collection
0 2 * * * cd /path/to/misinformation_gay_mens_Health && source venv/bin/activate && python scripts/automated_collection.py >> logs/cron_output.log 2>&1
```

### Multiple Collection Types
You can run different collection strategies at different frequencies:

```bash
# Frequent targeted collection (every 4 hours)
0 */4 * * * /usr/bin/python3 /path/to/misinformation_gay_mens_Health/scripts/automated_collection.py >> /path/to/misinformation_gay_mens_Health/logs/cron_output.log 2>&1

# Weekly full deep collection with cleanup (Sundays at 1 AM)
0 1 * * 0 /usr/bin/python3 /path/to/misinformation_gay_mens_Health/scripts/automated_collection.py && /usr/bin/python3 -c "from src.data_persistence import DataPersistenceManager; DataPersistenceManager().cleanup_old_data(90)" >> /path/to/misinformation_gay_mens_Health/logs/cron_cleanup.log 2>&1
```

## Configuration Options

### Environment Variables (.env)

Make sure these are set in your `.env` file:

```bash
# Reddit API (required)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=MisinformationResearch/1.0

# Database (choose one)
DATABASE_URL=postgresql://user:password@localhost/misinformation_research
# OR for SQLite fallback:
# DATABASE_URL=sqlite:///data/misinformation.db

# Collection settings (optional)
MAX_POSTS_PER_SUBREDDIT=1000
DATA_COLLECTION_INTERVAL_HOURS=24
MIN_COMMENT_LENGTH=10
```

### Collection Limits

You can adjust collection intensity by modifying settings:

- `MAX_POSTS_PER_SUBREDDIT`: Max posts per subreddit per run (default: 1000)
- `DATA_COLLECTION_INTERVAL_HOURS`: Expected frequency (default: 24)
- Rate limiting: 2-second delays between subreddits, 0.1s between posts

## Monitoring and Logs

### Log Files

The automated collection creates several log files:

```bash
logs/
├── automated_collection.log    # Main collection logs (rotated weekly)
├── cron_output.log            # Cron job stdout/stderr
└── misinformation_analysis.log # General application logs
```

### Collection Reports

Detailed JSON reports are saved after each run:

```bash
data/reports/
├── collection_report_20250831_020000.json
├── collection_report_20250831_080000.json
└── ...
```

### Monitoring Commands

Check recent collection status:

```bash
# View last 50 lines of collection log
tail -50 logs/automated_collection.log

# Check database stats
python -c "
from src.data_persistence import DataPersistenceManager
import json
dm = DataPersistenceManager()
stats = dm.get_collection_stats()
print(json.dumps(stats, indent=2, default=str))
"

# View recent collection reports
ls -la data/reports/ | head -10
```

## Duplicate Handling Details

### How Duplicates Are Managed

1. **Database Level**: Unique constraints on `post_id` and `comment_id`
2. **Application Level**: Scraper checks existing posts before processing
3. **Upsert Logic**: Updates existing posts with new scores/metadata
4. **Skip Strategy**: Avoids re-processing unchanged content

### Expected Behavior

- **First run**: Collects all matching posts
- **Subsequent runs**: Only collects new posts since last run
- **Updates**: Existing posts get updated scores/comment counts
- **Performance**: Dramatically faster after initial collection

## Rate Limiting and API Respect

### Reddit API Limits

- **Requests per minute**: 60 (with OAuth)
- **Our rate limiting**: 0.1s between posts, 2s between subreddits
- **Daily collection**: Well within limits (~1000 requests per day)

### Recommended Frequencies

| Frequency | Use Case | API Impact | Data Freshness |
|-----------|----------|------------|----------------|
| Every 4 hours | Active research | ~6000 req/day | Very fresh |
| Every 6 hours | Standard monitoring | ~4000 req/day | Fresh |
| **Daily** | **Recommended** | **~1000 req/day** | **Good** |
| Weekly | Archive/validation | ~150 req/day | Stale |

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   ```bash
   # Check Reddit API credentials
   echo $REDDIT_CLIENT_ID
   echo $REDDIT_CLIENT_SECRET
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connection
   python -c "from src.data_persistence import DataPersistenceManager; print('DB OK' if DataPersistenceManager().get_collection_stats() else 'DB FAIL')"
   ```

3. **Permission Issues**
   ```bash
   # Make script executable
   chmod +x scripts/automated_collection.py
   
   # Check cron permissions
   ls -la /var/log/cron*
   ```

4. **Path Issues in Cron**
   ```bash
   # Use absolute paths in crontab
   /usr/bin/python3 /full/path/to/script
   ```

### Log Analysis

Check for collection issues:

```bash
# Search for errors in recent logs
grep -i "error\|failed\|exception" logs/automated_collection.log | tail -20

# Check collection success rate
grep "Collection cycle complete" logs/automated_collection.log | tail -10

# Monitor database growth
grep "Total in DB" logs/automated_collection.log | tail -5
```

## Performance Optimization

### Database Performance

- **PostgreSQL**: Recommended for production (better concurrent access)
- **SQLite**: Adequate for development (simpler setup)
- **Indexing**: Key fields are already indexed

### Collection Efficiency

- **Skip existing posts**: Enabled by default
- **Keyword filtering**: Only health-related content
- **Language detection**: Cached results
- **Bulk operations**: Database saves in batches

## Data Retention

### Automatic Cleanup

Add a weekly cleanup job to prevent unbounded growth:

```bash
# Clean up posts older than 90 days every Sunday at 1 AM
0 1 * * 0 /usr/bin/python3 -c "from src.data_persistence import DataPersistenceManager; DataPersistenceManager().cleanup_old_data(90)" >> /path/to/misinformation_gay_mens_Health/logs/cleanup.log 2>&1
```

### Manual Cleanup

```bash
# Remove posts older than 30 days
python -c "
from src.data_persistence import DataPersistenceManager
dm = DataPersistenceManager()
removed = dm.cleanup_old_data(30)
print(f'Removed {removed} old posts')
"
```

## Security Considerations

### API Key Security

- ✅ Never commit API keys to version control
- ✅ Use `.env` file for credentials
- ✅ Restrict Reddit app permissions to read-only
- ✅ Monitor API usage in Reddit app dashboard

### Data Privacy

- ✅ Only collect public Reddit data
- ✅ Follow Reddit's Terms of Service
- ✅ Implement data retention policies
- ✅ Anonymize user data for research

## Example Workflow

### Initial Setup

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your Reddit API credentials

# 2. Initialize database
python src/database_setup.py

# 3. Apply latest schema
alembic upgrade head

# 4. Test collection
python scripts/automated_collection.py

# 5. Set up cron job
crontab -e
# Add: 0 2 * * * /usr/bin/python3 /path/to/scripts/automated_collection.py
```

### Daily Monitoring

```bash
# Check today's collection
grep "$(date +%Y-%m-%d)" logs/automated_collection.log

# View database status
python -c "
from src.data_persistence import DataPersistenceManager
stats = DataPersistenceManager().get_collection_stats()
for k, v in stats.items():
    print(f'{k}: {v}')
"
```

## Integration with Research Workflow

### Data Flow

1. **Automated Collection** → `reddit_posts` & `reddit_comments` tables
2. **Manual Analysis** → `python main.py analyze --data-path recent`
3. **Human Annotation** → `python main.py annotate-enhanced --data-path recent`
4. **Network Analysis** → Automated based on annotations

### Research Pipeline

```bash
# Daily automated collection (via cron)
python scripts/automated_collection.py

# Weekly analysis (can also be automated)
python main.py analyze --data-path "$(ls data/raw_reddit_data_*.json | tail -1)"

# Manual annotation sessions
python main.py annotate-enhanced --data-path "$(ls data/raw_reddit_data_*.json | tail -1)"
```

This setup ensures continuous, ethical data collection while respecting Reddit's API limits and community guidelines.
