#!/usr/bin/env python3
"""
Research-Grade Analytics Interface for Health Misinformation Detection
Comprehensive investigational features for research teams
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import gradio as gr
from loguru import logger

from config.settings import Config
from src.data_persistence import DataPersistenceManager
from src.database_models import RedditPost, RedditComment, HumanAnnotation
from src.analytics_dashboard import HealthMisinformationAnalytics
from src.network_analysis import NetworkAnalyzer
from src.translation_service import get_translation_service


class ResearchAnalyticsInterface:
    """
    Research-grade interface with comprehensive investigational features
    """

    def __init__(self):
        self.db_manager = DataPersistenceManager()
        self.analytics = HealthMisinformationAnalytics()
        self.network_analyzer = NetworkAnalyzer()
        self.translation_service = get_translation_service()

        # Load data
        self.analytics.load_data()

    def get_data_overview(self) -> Tuple[str, dict]:
        """Get comprehensive data overview with statistics"""
        with self.db_manager.get_session() as session:
            # Basic counts
            total_posts = session.query(RedditPost).count()
            total_comments = session.query(RedditComment).count()
            total_annotations = session.query(HumanAnnotation).count()

            # Language distribution
            language_dist = (
                session.query(
                    RedditPost.language, session.func.count(RedditPost.language)
                )
                .group_by(RedditPost.language)
                .all()
            )

            # Subreddit distribution
            subreddit_dist = (
                session.query(
                    RedditPost.subreddit, session.func.count(RedditPost.subreddit)
                )
                .group_by(RedditPost.subreddit)
                .all()
            )

            # Time-based analysis
            recent_posts = (
                session.query(RedditPost)
                .filter(RedditPost.created_utc >= datetime.now() - timedelta(days=7))
                .count()
            )

            # Health keyword posts
            keyword_posts = (
                session.query(RedditPost)
                .filter(RedditPost.contains_health_keywords == True)
                .count()
            )

            # Newcomer-related posts
            newcomer_posts = (
                session.query(RedditPost)
                .filter(RedditPost.is_newcomer_related == True)
                .count()
            )

        overview_text = f"""
        ## 📊 Research Data Overview
        
        **Core Statistics:**
        - **Posts:** {total_posts:,} total
        - **Comments:** {total_comments:,} total  
        - **Annotations:** {total_annotations:,} total
        - **Recent Activity:** {recent_posts:,} posts in last 7 days
        
        **Content Analysis:**
        - **Health Keywords:** {keyword_posts:,} posts ({keyword_posts/max(total_posts,1)*100:.1f}%)
        - **Newcomer-Related:** {newcomer_posts:,} posts ({newcomer_posts/max(total_posts,1)*100:.1f}%)
        
        **Language Distribution:**
        {chr(10).join([f"- **{lang or 'Unknown'}:** {count:,} posts" for lang, count in language_dist])}
        
        **Subreddit Distribution:**
        {chr(10).join([f"- **r/{sub}:** {count:,} posts" for sub, count in subreddit_dist[:10]])}
        """

        # Create visualization data
        vis_data = {
            "language_dist": dict(language_dist),
            "subreddit_dist": dict(subreddit_dist),
            "basic_stats": {
                "total_posts": total_posts,
                "total_comments": total_comments,
                "keyword_posts": keyword_posts,
                "newcomer_posts": newcomer_posts,
            },
        }

        return overview_text, vis_data

    def create_temporal_analysis(self) -> go.Figure:
        """Create temporal analysis visualization"""
        with self.db_manager.get_session() as session:
            # Query posts by day
            posts_by_date = (
                session.query(
                    session.func.date(RedditPost.created_utc).label("date"),
                    session.func.count(RedditPost.id).label("count"),
                )
                .group_by(session.func.date(RedditPost.created_utc))
                .order_by("date")
                .all()
            )

            if not posts_by_date:
                return go.Figure().add_annotation(
                    text="No temporal data available",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                )

            dates = [row.date for row in posts_by_date]
            counts = [row.count for row in posts_by_date]

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=dates, y=counts, mode="lines+markers", name="Posts per Day"
                )
            )
            fig.update_layout(
                title="Post Volume Over Time",
                xaxis_title="Date",
                yaxis_title="Number of Posts",
            )

            return fig

    def create_network_visualization(
        self, subreddit_filter: Optional[str] = None
    ) -> go.Figure:
        """Create network analysis visualization"""
        try:
            # Build network based on user interactions
            network_data = self.network_analyzer.build_user_network(subreddit_filter)

            if not network_data.get("nodes"):
                return go.Figure().add_annotation(
                    text="No network data available",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                )

            # Create network visualization
            return self.network_analyzer.visualize_network(network_data)

        except Exception as e:
            logger.error(f"Network visualization error: {e}")
            return go.Figure().add_annotation(
                text=f"Network error: {str(e)}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
            )

    def search_posts_advanced(
        self,
        query: str,
        subreddit: str = "",
        language: str = "",
        date_from: str = "",
        date_to: str = "",
        has_keywords: bool = False,
        min_score: int = 0,
    ) -> str:
        """Advanced post search with multiple filters"""

        with self.db_manager.get_session() as session:
            # Start with base query
            posts_query = session.query(RedditPost)

            # Apply filters
            if query.strip():
                posts_query = posts_query.filter(
                    (RedditPost.title.ilike(f"%{query}%"))
                    | (RedditPost.selftext.ilike(f"%{query}%"))
                )

            if subreddit.strip():
                posts_query = posts_query.filter(
                    RedditPost.subreddit == subreddit.strip()
                )

            if language.strip():
                posts_query = posts_query.filter(
                    RedditPost.language == language.strip()
                )

            if has_keywords:
                posts_query = posts_query.filter(
                    RedditPost.contains_health_keywords == True
                )

            if min_score > 0:
                posts_query = posts_query.filter(RedditPost.score >= min_score)

            # Date filtering
            if date_from:
                try:
                    from_date = datetime.strptime(date_from, "%Y-%m-%d")
                    posts_query = posts_query.filter(
                        RedditPost.created_utc >= from_date
                    )
                except ValueError:
                    pass

            if date_to:
                try:
                    to_date = datetime.strptime(date_to, "%Y-%m-%d")
                    posts_query = posts_query.filter(RedditPost.created_utc <= to_date)
                except ValueError:
                    pass

            # Execute query
            results = (
                posts_query.order_by(RedditPost.created_utc.desc()).limit(50).all()
            )

            if not results:
                return "No posts found matching your criteria."

            # Format results
            results_text = f"## 🔍 Search Results ({len(results)} posts found)\n\n"

            for i, post in enumerate(results, 1):
                language_info = f" [{post.language}]" if post.language else ""
                keyword_info = " 🔑" if post.contains_health_keywords else ""
                newcomer_info = " 👥" if post.is_newcomer_related else ""

                results_text += f"""
**{i}. r/{post.subreddit}** - {post.score} points{language_info}{keyword_info}{newcomer_info}
*{post.title}*
{post.selftext[:200]}{'...' if len(post.selftext or '') > 200 else ''}
*Posted: {post.created_utc.strftime('%Y-%m-%d %H:%M')}*

---
"""

            return results_text

    def analyze_misinformation_patterns(self) -> Tuple[str, go.Figure]:
        """Analyze patterns in misinformation spread"""
        with self.db_manager.get_session() as session:
            # Get posts with human annotations
            annotated_posts = (
                session.query(RedditPost, HumanAnnotation)
                .join(HumanAnnotation, RedditPost.post_id == HumanAnnotation.post_id)
                .filter(HumanAnnotation.category != "accurate")
                .all()
            )

            if not annotated_posts:
                return (
                    "No misinformation patterns found in annotated data.",
                    go.Figure(),
                )

            # Analyze patterns
            patterns = {
                "by_subreddit": {},
                "by_language": {},
                "by_topic": {},
                "by_severity": {},
            }

            for post, annotation in annotated_posts:
                # By subreddit
                patterns["by_subreddit"][post.subreddit] = (
                    patterns["by_subreddit"].get(post.subreddit, 0) + 1
                )

                # By language
                lang = post.language or "unknown"
                patterns["by_language"][lang] = patterns["by_language"].get(lang, 0) + 1

                # By health topic
                topic = getattr(annotation, "health_topic", "general")
                patterns["by_topic"][topic] = patterns["by_topic"].get(topic, 0) + 1

                # By severity
                severity = getattr(annotation, "severity_level", 1)
                patterns["by_severity"][f"Level {severity}"] = (
                    patterns["by_severity"].get(f"Level {severity}", 0) + 1
                )

            # Create analysis text
            analysis_text = f"""
## 🚨 Misinformation Pattern Analysis

**Distribution by Platform:**
{chr(10).join([f"- **r/{sub}:** {count} cases" for sub, count in sorted(patterns['by_subreddit'].items(), key=lambda x: x[1], reverse=True)])}

**Distribution by Language:**
{chr(10).join([f"- **{lang}:** {count} cases" for lang, count in sorted(patterns['by_language'].items(), key=lambda x: x[1], reverse=True)])}

**Health Topics Affected:**
{chr(10).join([f"- **{topic}:** {count} cases" for topic, count in sorted(patterns['by_topic'].items(), key=lambda x: x[1], reverse=True)])}

**Severity Distribution:**
{chr(10).join([f"- **{sev}:** {count} cases" for sev, count in sorted(patterns['by_severity'].items(), key=lambda x: x[1], reverse=True)])}
"""

            # Create visualization
            fig = make_subplots(
                rows=2,
                cols=2,
                subplot_titles=(
                    "By Subreddit",
                    "By Language",
                    "By Topic",
                    "By Severity",
                ),
                specs=[
                    [{"type": "bar"}, {"type": "pie"}],
                    [{"type": "bar"}, {"type": "pie"}],
                ],
            )

            # Subreddit distribution
            subs, sub_counts = zip(
                *sorted(
                    patterns["by_subreddit"].items(), key=lambda x: x[1], reverse=True
                )
            )
            fig.add_trace(
                go.Bar(x=list(subs), y=list(sub_counts), name="Subreddits"),
                row=1,
                col=1,
            )

            # Language distribution
            langs, lang_counts = zip(*patterns["by_language"].items())
            fig.add_trace(
                go.Pie(labels=list(langs), values=list(lang_counts), name="Languages"),
                row=1,
                col=2,
            )

            # Topic distribution
            topics, topic_counts = zip(
                *sorted(patterns["by_topic"].items(), key=lambda x: x[1], reverse=True)
            )
            fig.add_trace(
                go.Bar(x=list(topics), y=list(topic_counts), name="Topics"),
                row=2,
                col=1,
            )

            # Severity distribution
            sevs, sev_counts = zip(*patterns["by_severity"].items())
            fig.add_trace(
                go.Pie(labels=list(sevs), values=list(sev_counts), name="Severity"),
                row=2,
                col=2,
            )

            fig.update_layout(
                title_text="Misinformation Distribution Analysis", showlegend=False
            )

            return analysis_text, fig

    def generate_intervention_recommendations(self, subreddit: str = "") -> str:
        """Generate evidence-based intervention recommendations"""

        with self.db_manager.get_session() as session:
            query = session.query(RedditPost, HumanAnnotation).join(
                HumanAnnotation, RedditPost.post_id == HumanAnnotation.post_id
            )

            if subreddit.strip():
                query = query.filter(RedditPost.subreddit == subreddit.strip())

            annotated_posts = query.all()

            if not annotated_posts:
                return "No data available for generating recommendations."

            # Analyze intervention needs
            high_priority = []
            educational_needs = []
            community_specific = {}

            for post, annotation in annotated_posts:
                severity = getattr(annotation, "severity_level", 1)
                target_community = getattr(annotation, "target_community", "general")
                health_topic = getattr(annotation, "health_topic", "general")

                if severity >= 4:  # High severity
                    high_priority.append(
                        {
                            "post_id": post.post_id,
                            "subreddit": post.subreddit,
                            "topic": health_topic,
                            "community": target_community,
                        }
                    )

                if "question" in post.title.lower():
                    educational_needs.append(health_topic)

                if target_community != "general":
                    if target_community not in community_specific:
                        community_specific[target_community] = []
                    community_specific[target_community].append(health_topic)

            recommendations = f"""
## 🎯 Evidence-Based Intervention Recommendations

### Immediate Action Required ({len(high_priority)} cases)
"""

            if high_priority:
                for item in high_priority[:5]:  # Top 5 priorities
                    recommendations += f"- **r/{item['subreddit']}**: {item['topic']} misinformation affecting {item['community']} community\n"

            recommendations += f"""

### Educational Resource Needs
**Top Topics Needing Clarification:**
{chr(10).join([f"- {topic}" for topic in list(set(educational_needs))[:10]])}

### Community-Specific Interventions
"""

            for community, topics in community_specific.items():
                top_topics = list(set(topics))[:3]
                recommendations += (
                    f"- **{community}**: Focus on {', '.join(top_topics)}\n"
                )

            recommendations += f"""

### Platform-Specific Strategies
**Recommended Actions:**
- Partner with r/{subreddit if subreddit else 'target'} moderators for pinned educational content
- Develop culturally-appropriate fact-checking resources
- Implement community-led peer education programs
- Create multilingual intervention materials

### Monitoring Priorities
- Track intervention effectiveness through engagement metrics
- Monitor for new misinformation variants
- Assess community sentiment changes
"""

            return recommendations

    def create_interface(self):
        """Create the research analytics interface"""

        with gr.Blocks(
            title="Health Misinformation Research Analytics", theme=gr.themes.Soft()
        ) as interface:

            gr.HTML("<h1>🔬 Health Misinformation Research Analytics Platform</h1>")
            gr.HTML(
                "<p>Comprehensive investigational tools for research teams analyzing health misinformation in immigrant communities.</p>"
            )

            with gr.Tabs():
                # Data Overview Tab
                with gr.Tab("📊 Data Overview"):
                    with gr.Row():
                        overview_text = gr.Markdown()
                        temporal_plot = gr.Plot()

                    refresh_btn = gr.Button("🔄 Refresh Overview", variant="primary")
                    refresh_btn.click(
                        lambda: (
                            self.get_data_overview()[0],
                            self.create_temporal_analysis(),
                        ),
                        outputs=[overview_text, temporal_plot],
                    )

                # Advanced Search Tab
                with gr.Tab("🔍 Advanced Search"):
                    with gr.Row():
                        with gr.Column():
                            search_query = gr.Textbox(
                                label="Search Query",
                                placeholder="Enter keywords to search in titles and content",
                            )
                            subreddit_filter = gr.Textbox(
                                label="Subreddit Filter", placeholder="e.g., askgaybros"
                            )
                            language_filter = gr.Textbox(
                                label="Language Filter", placeholder="e.g., en, es, tl"
                            )
                        with gr.Column():
                            date_from = gr.Textbox(
                                label="Date From (YYYY-MM-DD)", placeholder="2023-01-01"
                            )
                            date_to = gr.Textbox(
                                label="Date To (YYYY-MM-DD)", placeholder="2023-12-31"
                            )
                            has_keywords = gr.Checkbox(label="Has Health Keywords Only")
                            min_score = gr.Slider(
                                0, 1000, value=0, label="Minimum Score"
                            )

                    search_btn = gr.Button("🔍 Search Posts", variant="primary")
                    search_results = gr.Markdown()

                    search_btn.click(
                        self.search_posts_advanced,
                        inputs=[
                            search_query,
                            subreddit_filter,
                            language_filter,
                            date_from,
                            date_to,
                            has_keywords,
                            min_score,
                        ],
                        outputs=search_results,
                    )

                # Network Analysis Tab
                with gr.Tab("🕸️ Network Analysis"):
                    with gr.Row():
                        network_subreddit = gr.Textbox(
                            label="Subreddit Filter (optional)",
                            placeholder="Leave empty for all subreddits",
                        )
                        network_btn = gr.Button("🕸️ Generate Network", variant="primary")

                    network_plot = gr.Plot()

                    network_btn.click(
                        self.create_network_visualization,
                        inputs=network_subreddit,
                        outputs=network_plot,
                    )

                # Misinformation Patterns Tab
                with gr.Tab("🚨 Misinformation Analysis"):
                    analyze_btn = gr.Button("🚨 Analyze Patterns", variant="primary")

                    with gr.Row():
                        patterns_text = gr.Markdown()
                        patterns_plot = gr.Plot()

                    analyze_btn.click(
                        self.analyze_misinformation_patterns,
                        outputs=[patterns_text, patterns_plot],
                    )

                # Intervention Planning Tab
                with gr.Tab("🎯 Intervention Planning"):
                    intervention_subreddit = gr.Textbox(
                        label="Focus Subreddit (optional)",
                        placeholder="Leave empty for all subreddits",
                    )
                    intervention_btn = gr.Button(
                        "🎯 Generate Recommendations", variant="primary"
                    )
                    intervention_text = gr.Markdown()

                    intervention_btn.click(
                        self.generate_intervention_recommendations,
                        inputs=intervention_subreddit,
                        outputs=intervention_text,
                    )

                # Export Data Tab
                with gr.Tab("💾 Export & Reports"):
                    gr.HTML("<h3>Data Export Options</h3>")

                    with gr.Row():
                        export_format = gr.Radio(
                            ["CSV", "JSON", "Excel"], value="CSV", label="Export Format"
                        )
                        date_range = gr.Radio(
                            ["Last 7 days", "Last 30 days", "All data"],
                            value="Last 30 days",
                            label="Date Range",
                        )

                    export_btn = gr.Button("💾 Export Data", variant="primary")
                    export_status = gr.Textbox(label="Export Status", interactive=False)

                    # Note: Export functionality would need additional implementation
                    export_btn.click(
                        lambda fmt, rng: f"Export in {fmt} format for {rng} - Feature coming soon!",
                        inputs=[export_format, date_range],
                        outputs=export_status,
                    )

            # Initialize with overview data
            interface.load(
                lambda: (self.get_data_overview()[0], self.create_temporal_analysis()),
                outputs=[overview_text, temporal_plot],
            )

        return interface


def launch_research_interface():
    """Launch the research analytics interface"""
    logger.info("Launching Research Analytics Interface...")

    interface = ResearchAnalyticsInterface()
    app = interface.create_interface()

    app.launch(
        server_name="0.0.0.0",
        server_port=7861,  # Different port from annotation interface
        share=Config.GRADIO_SHARE,
        show_error=True,
    )


if __name__ == "__main__":
    launch_research_interface()
