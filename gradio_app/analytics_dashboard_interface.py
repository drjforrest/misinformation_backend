#!/usr/bin/env python3
"""
Gradio Dashboard Interface for Health Misinformation Research Analytics
Provides interactive visualizations and insights for research teams
"""

import gradio as gr
import plotly.express as px
from datetime import datetime
from typing import Tuple

from src.analytics_dashboard import HealthMisinformationAnalytics
from config.settings import Config


class AnalyticsDashboardInterface:
    """Interactive dashboard for health misinformation research analytics"""

    def __init__(self):
        self.analytics = HealthMisinformationAnalytics()
        self.cached_data = {}
        self.refresh_data()

    def refresh_data(self):
        """Refresh analytics data"""
        self.cached_data = {
            "data_summary": self.analytics.load_data(),
            "language_analysis": self.analytics.analyze_language_distribution(),
            "keyword_analysis": self.analytics.analyze_health_keywords(),
            "subreddit_analysis": self.analytics.analyze_subreddit_patterns(),
            "temporal_analysis": self.analytics.analyze_temporal_patterns(),
            "newcomer_analysis": self.analytics.analyze_newcomer_content(),
            "insights": self.analytics.generate_insights(),
        }

    def create_overview_stats(self) -> str:
        """Create overview statistics display"""
        data = self.cached_data["data_summary"]
        lang_data = self.cached_data["language_analysis"]
        keyword_data = self.cached_data["keyword_analysis"]
        newcomer_data = self.cached_data["newcomer_analysis"]

        overview = f"""
# 📊 Health Misinformation Research Dashboard

## 🎯 Data Overview
- **Total Posts Collected:** {data['total_posts']:,}
- **Total Comments:** {data['total_comments']:,} 
- **Unique Authors:** {data['unique_authors']:,}
- **Languages Detected:** {lang_data['total_languages']}
- **Posts with Health Keywords:** {keyword_data['posts_with_keywords']} ({keyword_data['keyword_coverage']:.1f}%)
- **Newcomer-Focused Posts:** {newcomer_data['total_newcomer_posts']} ({newcomer_data['percentage_newcomer']:.1f}%)
- **Multilingual Content:** {lang_data['multilingual_posts']} posts ({lang_data['multilingual_percentage']:.1f}%)

---
"""
        return overview

    def create_insights_display(self) -> str:
        """Create insights display for research teams"""
        insights = self.cached_data["insights"]

        insights_text = "# 🔍 Research Insights & Recommendations\n\n"

        for category, insight_list in insights.items():
            if insight_list:
                category_title = category.replace("_", " ").title()
                insights_text += f"## {category_title}\n"
                for insight in insight_list:
                    insights_text += f"- {insight}\n"
                insights_text += "\n"

        return insights_text

    def create_language_distribution_chart(self):
        """Create language distribution visualization"""
        lang_data = self.cached_data["language_analysis"]

        if not lang_data["post_languages"]:
            return None

        # Create pie chart with country flags
        language_labels = []
        language_flags = {
            "en": "🇺🇸 English",
            "tl": "🇵🇭 Tagalog",
            "zh-CN": "🇨🇳 Chinese (S)",
            "zh-TW": "🇹🇼 Chinese (T)",
            "pa": "🇮🇳 Punjabi",
            "es": "🇪🇸 Spanish",
            "fr": "🇫🇷 French",
            "unknown": "❓ Unknown",
        }

        for lang in lang_data["post_languages"].keys():
            language_labels.append(language_flags.get(lang, f"{lang.upper()}"))

        fig = px.pie(
            values=list(lang_data["post_languages"].values()),
            names=language_labels,
            title="📊 Posts by Language Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3,
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="%{label}<br>Posts: %{value}<br>Percentage: %{percent}<extra></extra>",
        )

        fig.update_layout(font_size=12, title_font_size=16, showlegend=True)

        return fig

    def create_health_keywords_chart(self):
        """Create health keywords visualization"""
        keyword_data = self.cached_data["keyword_analysis"]

        if not keyword_data["keyword_counts"]:
            return None

        # Top 15 keywords
        top_keywords = dict(
            sorted(
                keyword_data["keyword_counts"].items(), key=lambda x: x[1], reverse=True
            )[:15]
        )

        fig = px.bar(
            x=list(top_keywords.values()),
            y=list(top_keywords.keys()),
            orientation="h",
            title="🏥 Most Mentioned Health Keywords",
            labels={"x": "Frequency", "y": "Keywords"},
            color=list(top_keywords.values()),
            color_continuous_scale="Viridis",
        )

        fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
            font_size=11,
            title_font_size=16,
            height=500,
        )

        fig.update_traces(hovertemplate="%{y}<br>Mentions: %{x}<extra></extra>")

        return fig

    def create_subreddit_analysis_chart(self):
        """Create subreddit analysis visualization"""
        subreddit_data = self.cached_data["subreddit_analysis"]

        if not subreddit_data:
            return None

        # Prepare data
        subs = list(subreddit_data.keys())
        post_counts = [data["post_count"] for data in subreddit_data.values()]
        health_keywords = [data["health_keywords"] for data in subreddit_data.values()]
        newcomer_posts = [data["newcomer_posts"] for data in subreddit_data.values()]
        language_diversity = [
            data["language_diversity"] for data in subreddit_data.values()
        ]

        # Create subplots
        fig = px.bar(
            x=subs,
            y=post_counts,
            title="📋 Subreddit Activity Overview",
            labels={"x": "Subreddit", "y": "Number of Posts"},
            color=post_counts,
            color_continuous_scale="Blues",
        )

        fig.update_layout(font_size=11, title_font_size=16, xaxis_tickangle=-45)

        fig.update_traces(hovertemplate="r/%{x}<br>Posts: %{y}<extra></extra>")

        return fig

    def create_multilingual_content_chart(self):
        """Create multilingual content analysis"""
        lang_data = self.cached_data["language_analysis"]

        multilingual_posts = lang_data["multilingual_posts"]
        total_posts = self.cached_data["data_summary"]["total_posts"]
        english_only = total_posts - multilingual_posts

        if multilingual_posts == 0:
            return None

        fig = px.pie(
            values=[english_only, multilingual_posts],
            names=["English Only", "Multilingual/Translated"],
            title="🌐 Content Language Composition",
            color_discrete_map={
                "English Only": "#3498db",
                "Multilingual/Translated": "#e74c3c",
            },
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label+value",
            hovertemplate="%{label}<br>Posts: %{value}<br>Percentage: %{percent}<extra></extra>",
        )

        return fig

    def create_newcomer_content_chart(self):
        """Create newcomer content analysis"""
        newcomer_data = self.cached_data["newcomer_analysis"]
        total_posts = self.cached_data["data_summary"]["total_posts"]

        if newcomer_data["total_newcomer_posts"] == 0:
            return None

        newcomer_count = newcomer_data["total_newcomer_posts"]
        general_count = total_posts - newcomer_count

        fig = px.pie(
            values=[general_count, newcomer_count],
            names=["General Content", "Newcomer-Focused"],
            title="🆕 Newcomer-Related Content",
            color_discrete_map={
                "General Content": "#95a5a6",
                "Newcomer-Focused": "#2ecc71",
            },
        )

        fig.update_traces(
            textposition="inside",
            textinfo="percent+label+value",
            hovertemplate="%{label}<br>Posts: %{value}<br>Percentage: %{percent}<extra></extra>",
        )

        return fig

    def create_detailed_stats_table(self) -> str:
        """Create detailed statistics table"""
        subreddit_data = self.cached_data["subreddit_analysis"]

        if not subreddit_data:
            return "No subreddit data available"

        table_md = """
# 📈 Detailed Subreddit Statistics

| Subreddit | Posts | Comments | Languages | Health Keywords | Newcomer Posts | Avg Score | Language Diversity |
|-----------|--------|----------|-----------|-----------------|----------------|-----------|-------------------|
"""

        for sub, data in sorted(
            subreddit_data.items(), key=lambda x: x[1]["post_count"], reverse=True
        ):
            languages_str = ", ".join(data["languages"][:3])  # Show top 3 languages
            if len(data["languages"]) > 3:
                languages_str += f" (+{len(data['languages'])-3} more)"

            table_md += f"| r/{sub} | {data['post_count']} | {data['comment_count']} | {languages_str} | {data['health_keywords']} | {data['newcomer_posts']} | {data['avg_score']:.1f} | {data['language_diversity']} |\n"

        return table_md

    def export_report(self) -> Tuple[str, str]:
        """Export comprehensive analytics report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"data/analytics_report_{timestamp}.json"

        report = self.analytics.export_analytics_report(output_path)

        return f"✅ Report exported successfully to {output_path}", output_path

    def create_dashboard(self):
        """Create the main dashboard interface"""

        with gr.Blocks(
            title="Health Misinformation Research Dashboard",
            theme=gr.themes.Soft(),
            css="""
            .gradio-container {max-width: 1200px !important}
            .plot-container {height: 500px !important}
            """,
        ) as dashboard:

            gr.Markdown("# 🏥 Health Misinformation Research Analytics Dashboard")
            gr.Markdown("*Comprehensive insights for research teams and stakeholders*")

            with gr.Row():
                refresh_btn = gr.Button("🔄 Refresh Data", variant="secondary")
                export_btn = gr.Button("📊 Export Report", variant="primary")

            with gr.Row():
                export_status = gr.Textbox(label="Export Status", interactive=False)

            # Overview tab
            with gr.Tab("📊 Overview"):
                overview_stats = gr.Markdown(value=self.create_overview_stats())
                insights_display = gr.Markdown(value=self.create_insights_display())

            # Language Analysis tab
            with gr.Tab("🌐 Language Analysis"):
                with gr.Row():
                    with gr.Column():
                        language_chart = gr.Plot(
                            value=self.create_language_distribution_chart()
                        )
                    with gr.Column():
                        multilingual_chart = gr.Plot(
                            value=self.create_multilingual_content_chart()
                        )

                gr.Markdown("## 💡 Language Insights")
                lang_insights = gr.Markdown(
                    value="\\n".join(
                        [
                            f"- {insight}"
                            for insight in self.cached_data["insights"][
                                "language_insights"
                            ]
                        ]
                    )
                )

            # Health Content Analysis tab
            with gr.Tab("🏥 Health Content"):
                health_keywords_chart = gr.Plot(
                    value=self.create_health_keywords_chart()
                )

                with gr.Row():
                    newcomer_chart = gr.Plot(value=self.create_newcomer_content_chart())

                gr.Markdown("## 💡 Content Insights")
                content_insights = gr.Markdown(
                    value="\\n".join(
                        [
                            f"- {insight}"
                            for insight in self.cached_data["insights"][
                                "content_insights"
                            ]
                        ]
                    )
                )

            # Platform Analysis tab
            with gr.Tab("📱 Platform Analysis"):
                subreddit_chart = gr.Plot(value=self.create_subreddit_analysis_chart())

                detailed_table = gr.Markdown(value=self.create_detailed_stats_table())

                gr.Markdown("## 💡 Engagement Insights")
                engagement_insights = gr.Markdown(
                    value="\\n".join(
                        [
                            f"- {insight}"
                            for insight in self.cached_data["insights"][
                                "engagement_insights"
                            ]
                        ]
                    )
                )

            # Research Recommendations tab
            with gr.Tab("🔬 Research Recommendations"):
                gr.Markdown("## 🎯 Next Steps for Research Team")
                research_recommendations = gr.Markdown(
                    value="\\n".join(
                        [
                            f"- {rec}"
                            for rec in self.cached_data["insights"][
                                "research_recommendations"
                            ]
                        ]
                    )
                )

                gr.Markdown(
                    """
## 📋 Recommended Actions

### Immediate Actions:
1. **Expand Multilingual Coverage**: Based on language distribution, consider targeting specific language communities
2. **Enhance Keyword Detection**: Update health keyword dictionaries based on frequently mentioned terms
3. **Focus High-Impact Subreddits**: Prioritize monitoring subreddits with highest health keyword density

### Medium-term Goals:
1. **Develop Language-Specific Models**: Create targeted misinformation detection for non-English content
2. **Community Partnerships**: Establish connections with immigrant community organizations
3. **Intervention Strategy**: Design community-specific health information campaigns

### Long-term Research:
1. **Longitudinal Studies**: Track misinformation patterns over time
2. **Cross-platform Analysis**: Expand beyond Reddit to other social platforms
3. **Effectiveness Measurement**: Develop metrics to assess intervention success
                """
                )

            # Event handlers
            def refresh_dashboard():
                self.refresh_data()
                return [
                    self.create_overview_stats(),
                    self.create_insights_display(),
                    self.create_language_distribution_chart(),
                    self.create_multilingual_content_chart(),
                    self.create_health_keywords_chart(),
                    self.create_newcomer_content_chart(),
                    self.create_subreddit_analysis_chart(),
                    self.create_detailed_stats_table(),
                    "\\n".join(
                        [
                            f"- {insight}"
                            for insight in self.cached_data["insights"][
                                "language_insights"
                            ]
                        ]
                    ),
                    "\\n".join(
                        [
                            f"- {insight}"
                            for insight in self.cached_data["insights"][
                                "content_insights"
                            ]
                        ]
                    ),
                    "\\n".join(
                        [
                            f"- {insight}"
                            for insight in self.cached_data["insights"][
                                "engagement_insights"
                            ]
                        ]
                    ),
                    "\\n".join(
                        [
                            f"- {rec}"
                            for rec in self.cached_data["insights"][
                                "research_recommendations"
                            ]
                        ]
                    ),
                ]

            refresh_btn.click(
                fn=refresh_dashboard,
                outputs=[
                    overview_stats,
                    insights_display,
                    language_chart,
                    multilingual_chart,
                    health_keywords_chart,
                    newcomer_chart,
                    subreddit_chart,
                    detailed_table,
                    lang_insights,
                    content_insights,
                    engagement_insights,
                    research_recommendations,
                ],
            )

            export_btn.click(fn=self.export_report, outputs=[export_status])

        return dashboard

    def launch(self, share: bool = False):
        """Launch the analytics dashboard"""
        dashboard = self.create_dashboard()
        dashboard.launch(
            share=share,
            server_port=Config.GRADIO_PORT + 2,  # Use different port
            server_name="0.0.0.0" if share else "127.0.0.1",
        )


if __name__ == "__main__":
    # Launch the analytics dashboard
    dashboard = AnalyticsDashboardInterface()
    dashboard.launch(share=False)
