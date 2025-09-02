# 📊 Analytics Dashboard Documentation

## Overview

The Health Misinformation Research Analytics Dashboard provides comprehensive visualizations and insights from the collected Reddit data. It's designed for research teams, stakeholders, and decision-makers to understand patterns in health misinformation across different communities and languages.

## Features

### 🎯 Data Overview
- Total posts, comments, and unique authors
- Language detection statistics
- Health keyword coverage
- Newcomer-focused content analysis
- Multilingual content distribution

### 🌐 Language Analysis
- Interactive pie charts showing language distribution
- Multilingual vs. English-only content breakdown
- Language diversity insights
- Country flag indicators for visual clarity

### 🏥 Health Content Analysis
- Top health keywords mentioned across posts
- Frequency analysis with interactive bar charts
- Newcomer-specific content identification
- Content categorization insights

### 📱 Platform Analysis
- Subreddit activity overview
- Detailed statistics tables
- Engagement metrics by community
- Language diversity per subreddit

### 🔬 Research Recommendations
- Data-driven insights for research teams
- Actionable recommendations categorized by timeframe
- Strategic guidance for intervention development

## Getting Started

### Prerequisites
```bash
# Ensure you have the required dependencies installed
pip install -r requirements.txt

# Make sure you have data collected in your database
python -m src.data_collector
```

### Launching the Dashboard

#### Option 1: Analytics Dashboard Only
```bash
python launch_dashboard.py --mode analytics
```

#### Option 2: Both Interfaces
```bash
python launch_dashboard.py --mode both
```

#### Option 3: With Public Sharing
```bash
python launch_dashboard.py --mode analytics --share
```

### Direct Launch
```bash
python gradio_app/analytics_dashboard_interface.py
```

## Dashboard Tabs

### 📊 Overview Tab
- **Data Summary**: High-level statistics about your dataset
- **Research Insights**: Automatically generated insights based on data patterns
- **Quick Metrics**: Key performance indicators for your research

### 🌐 Language Analysis Tab
- **Language Distribution**: Pie chart showing language prevalence
- **Multilingual Content**: Analysis of translated vs. original content
- **Language Insights**: Targeted recommendations for multilingual outreach

### 🏥 Health Content Tab
- **Health Keywords Chart**: Top 15 most mentioned health-related terms
- **Newcomer Content**: Analysis of immigrant/newcomer-focused discussions
- **Content Insights**: Patterns in health discussions across communities

### 📱 Platform Analysis Tab
- **Subreddit Activity**: Bar chart of posts per community
- **Detailed Statistics Table**: Comprehensive metrics by subreddit
- **Engagement Insights**: Community engagement patterns and recommendations

### 🔬 Research Recommendations Tab
- **Immediate Actions**: Steps you can take right now
- **Medium-term Goals**: Strategic initiatives for the next 3-6 months
- **Long-term Research**: Vision for comprehensive misinformation research

## Key Visualizations

### Language Distribution Chart
```python
# Creates interactive pie chart with country flags
- Shows percentage of posts by detected language
- Includes hover information with exact counts
- Color-coded for easy identification
```

### Health Keywords Analysis
```python
# Horizontal bar chart of most mentioned health terms
- Top 15 keywords by frequency
- Color gradient based on mention count
- Interactive hover details
```

### Subreddit Activity Overview
```python
# Bar chart showing post counts by community
- Sorted by activity level
- Color-coded by volume
- Click-through for detailed analysis
```

## Export Functionality

### Analytics Report Export
The dashboard can export comprehensive JSON reports containing:

```json
{
  "metadata": {
    "generated_at": "timestamp",
    "total_posts": number,
    "analysis_version": "string"
  },
  "language_analysis": {...},
  "keyword_analysis": {...},
  "subreddit_analysis": {...},
  "temporal_analysis": {...},
  "insights": {...}
}
```

### Usage
1. Click the "📊 Export Report" button
2. Report saves to `data/analytics_report_YYYYMMDD_HHMMSS.json`
3. Status confirmation appears in the interface

## Data Refresh

### Manual Refresh
- Click the "🔄 Refresh Data" button to reload all analytics
- Useful when new data has been collected
- Updates all charts and insights automatically

### Automatic Refresh
The dashboard refreshes data on initialization, ensuring you always see current insights.

## Architecture

### Components
```
AnalyticsDashboardInterface
├── HealthMisinformationAnalytics (data processing)
├── Plotly Charts (visualizations)
├── Gradio Interface (web UI)
└── Export Functions (reporting)
```

### Data Flow
1. **Data Loading**: Connects to database and loads posts/comments
2. **Analysis**: Processes data through various analytical functions
3. **Visualization**: Creates interactive charts using Plotly
4. **Display**: Renders in Gradio web interface
5. **Export**: Generates JSON reports for external use

## Customization

### Adding New Visualizations
1. Create method in `AnalyticsDashboardInterface`
2. Return Plotly figure object
3. Add to dashboard tabs in `create_dashboard()`
4. Include in refresh function

### Modifying Insights
Edit the `generate_insights()` method in `HealthMisinformationAnalytics` to add custom insight categories or modify existing ones.

### Styling
Modify the CSS in the `gr.Blocks()` constructor to customize appearance:
```python
css="""
.gradio-container {max-width: 1200px !important}
.plot-container {height: 500px !important}
"""
```

## Troubleshooting

### Common Issues

#### Dashboard Won't Load
```bash
# Check if database is accessible
python -c "from src.analytics_dashboard import HealthMisinformationAnalytics; h = HealthMisinformationAnalytics(); print(h.load_data())"
```

#### Empty Visualizations
- Ensure data exists in database
- Check database connection settings in `config/settings.py`
- Verify data collection has completed

#### Port Conflicts
```bash
# Dashboard uses port 7862 by default
# Change in config/settings.py or modify launch script
```

### Memory Issues
For large datasets:
- Consider implementing data pagination
- Add data filtering options
- Use sampling for visualization

## Contributing

### Adding New Analytics
1. Add method to `HealthMisinformationAnalytics`
2. Create corresponding visualization method
3. Update dashboard interface
4. Add documentation

### Improving Visualizations
- Use consistent color schemes
- Ensure accessibility (color-blind friendly)
- Add informative hover text
- Include clear axis labels

## Integration

### With Annotation Interface
The analytics dashboard complements the annotation interface by providing:
- Context for posts being annotated
- Population-level patterns to inform annotation priorities
- Progress tracking for annotation efforts

### With External Tools
Export functionality allows integration with:
- R/Python analysis scripts
- Academic paper generation
- Presentation tools
- Other research platforms

## Performance Considerations

### Large Datasets
- Dashboard loads data on startup (may take time for large datasets)
- Consider implementing lazy loading for very large collections
- Use database indexing for faster queries

### Refresh Frequency
- Manual refresh prevents unnecessary database hits
- Consider caching frequently accessed data
- Implement incremental updates for real-time dashboards

## Future Enhancements

### Planned Features
- Real-time data streaming
- Advanced filtering options
- Custom date range selection
- Comparative analysis tools
- Machine learning model integration
- Collaborative annotation metrics

### API Integration
- REST API for external access
- Webhook support for automated updates
- Integration with academic databases
- Social media platform APIs

---

For additional support or feature requests, please refer to the main project documentation or open an issue in the project repository.
