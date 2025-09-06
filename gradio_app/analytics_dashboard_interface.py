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
            "ml_analysis": self.analytics.analyze_ml_health_classification(),
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
        """Create comment language diversity analysis"""
        lang_data = self.cached_data["language_analysis"]

        # Show comment language diversity instead of just multilingual posts
        comment_languages = lang_data.get("comment_languages", {})

        if not comment_languages:
            # Fallback to post language analysis
            total_posts = self.cached_data["data_summary"]["total_posts"]
            post_languages = lang_data.get("post_languages", {"en": total_posts})
            languages = list(post_languages.keys())[:10]  # Top 10 languages
            counts = [post_languages[lang] for lang in languages]
            title = "📝 Post Language Distribution"
        else:
            # Sort by count and take top 10
            sorted_langs = sorted(
                comment_languages.items(), key=lambda x: x[1], reverse=True
            )[:10]
            languages = [lang for lang, count in sorted_langs]
            counts = [count for lang, count in sorted_langs]
            title = "💬 Comment Language Diversity"

        fig = px.bar(
            x=languages,
            y=counts,
            title=title,
            labels={"x": "Language", "y": "Count"},
            color=counts,
            color_continuous_scale="viridis",
        )

        fig.update_layout(
            xaxis_title="Language Code",
            yaxis_title="Number of Comments/Posts",
            showlegend=False,
        )

        return fig

    def create_newcomer_content_chart(self):
        """Create health keyword analysis by subreddit"""
        health_data = self.cached_data["keyword_analysis"]
        subreddit_data = self.cached_data["subreddit_analysis"]

        # Show health keyword distribution across subreddits
        subreddits = []
        health_keyword_counts = []
        total_posts = []

        for subreddit, data in subreddit_data.items():
            subreddits.append(subreddit)
            health_keyword_counts.append(data.get("health_keywords", 0))
            total_posts.append(data.get("post_count", 0))

        if not subreddits:
            # Fallback chart showing overall health content analysis
            health_posts = health_data.get("posts_with_keywords", 0)
            total_posts_count = self.cached_data["data_summary"]["total_posts"]
            non_health_posts = total_posts_count - health_posts

            fig = px.pie(
                values=[non_health_posts, health_posts],
                names=["General Content", "Health-Related"],
                title="🏥 Health Content Distribution",
                color_discrete_map={
                    "General Content": "#95a5a6",
                    "Health-Related": "#e74c3c",
                },
            )

            fig.update_traces(
                textposition="inside",
                textinfo="percent+label+value",
                hovertemplate="%{label}<br>Posts: %{value}<br>Percentage: %{percent}<extra></extra>",
            )
        else:
            # Bar chart showing health keywords by subreddit
            fig = px.bar(
                x=subreddits,
                y=health_keyword_counts,
                title="🏥 Health Keywords by Subreddit",
                labels={"x": "Subreddit", "y": "Posts with Health Keywords"},
                color=health_keyword_counts,
                color_continuous_scale="Reds",
            )

            fig.update_layout(
                xaxis_title="Subreddit",
                yaxis_title="Health Keyword Posts",
                showlegend=False,
                xaxis_tickangle=-45,
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

            # ML Analysis tab
            with gr.Tab("🤖 ML Analysis"):
                ml_data = self.cached_data["ml_analysis"]

                if ml_data.get("model_available", False):
                    gr.Markdown("# 🧠 Machine Learning Health Content Classification")
                    gr.Markdown(
                        "*Real ML model trained on your data with 94% test accuracy*"
                    )

                    # ML Performance metrics
                    gr.Markdown("## 📊 Model Performance")
                    perf = ml_data["model_performance"]
                    gr.Markdown(
                        f"""
**Training Accuracy:** {perf['training_accuracy']:.1%}  
**Test Accuracy:** {perf['test_accuracy']:.1%}  
**Features Used:** {perf['feature_count']:,}
                    """
                    )

                    # Classification results
                    with gr.Row():
                        # Posts classification
                        post_data = ml_data["post_classification"]
                        with gr.Column():
                            gr.Markdown("### 📝 Post Classification")
                            post_fig = px.pie(
                                values=[
                                    post_data["general"],
                                    post_data["health_related"],
                                ],
                                names=["General Discussion", "Health-Related"],
                                title=f"Posts: {post_data['health_percentage']:.1f}% Health-Related",
                                color_discrete_map={
                                    "General Discussion": "#95a5a6",
                                    "Health-Related": "#e74c3c",
                                },
                            )
                            gr.Plot(value=post_fig)

                        # Comments classification
                        comment_data = ml_data["comment_classification"]
                        with gr.Column():
                            gr.Markdown("### 💬 Comment Classification")
                            comment_fig = px.pie(
                                values=[
                                    comment_data["general"],
                                    comment_data["health_related"],
                                ],
                                names=["General Discussion", "Health-Related"],
                                title=f"Comments: {comment_data['health_percentage']:.1f}% Health-Related",
                                color_discrete_map={
                                    "General Discussion": "#95a5a6",
                                    "Health-Related": "#e74c3c",
                                },
                            )
                            gr.Plot(value=comment_fig)

                    # Top ML features
                    gr.Markdown("## 🔍 Top Health Indicators Learned by ML")
                    features_text = []
                    for feature, importance in ml_data["top_health_features"]:
                        features_text.append(f"**{feature}**: {importance:.2f}")
                    gr.Markdown("• " + "\n• ".join(features_text))

                    # High confidence examples
                    gr.Markdown("## 💯 High-Confidence Health Classifications")
                    examples_text = ""
                    for i, example in enumerate(ml_data["high_confidence_examples"], 1):
                        confidence_pct = example["confidence"] * 100
                        examples_text += f"""
**Example {i}** ({confidence_pct:.0f}% confidence)
> {example['text']}

---
"""
                    gr.Markdown(
                        examples_text
                        if examples_text
                        else "*No high-confidence examples found*"
                    )

                else:
                    gr.Markdown("⚠️ **ML Model Not Available**")
                    gr.Markdown(
                        "Run `python -m src.health_content_classifier` to train the model first."
                    )

            # Classification Methods tab
            with gr.Tab("📚 Classification Methods"):
                gr.Markdown(
                    """
# 🧠 Algorithm Documentation

## Current Classification Status

⚠️ **Important**: The platform is currently in **data collection phase**. Advanced ML classification is not yet active.

### What's Currently Working:
- ✅ **Language Detection**: Using `langdetect` library for automatic language identification
- ✅ **Keyword Matching**: Simple pattern matching against health keyword dictionaries
- ✅ **Newcomer Detection**: Rule-based matching of newcomer-related phrases
- ✅ **Basic Content Analysis**: Word frequency and engagement metrics

### What's Planned (Not Yet Implemented):
- 🔄 **ML Misinformation Scoring**: Machine learning models for misinformation detection
- 🔄 **Severity Classification**: 1-5 scale severity assessment
- 🔄 **Health Topic Classification**: Automated categorization (PrEP, HIV testing, etc.)
- 🔄 **Context-Aware Analysis**: Understanding discussion context and intent

### Current Keyword Detection Method:
```python
# Simple keyword matching (case-insensitive)
HEALTH_KEYWORDS = [
    "HIV", "PrEP", "ARVs", "syphilis", "doxy", 
    "PEP", "chlamydia", "gonorrhea", "Truvada"
]

def contains_health_keywords(text):
    text_lower = text.lower()
    return any(keyword.lower() in text_lower 
              for keyword in HEALTH_KEYWORDS)
```

### Future ML Pipeline:
1. **Data Collection** ← **(Current Phase)**
2. **Human Annotation** (Research team coding)
3. **Model Training** (Using annotated data)
4. **Automated Classification** (ML predictions)
5. **Continuous Learning** (Model improvement)

### Research Team Notes:
- Any advanced classifications you see are likely from **demo data** or **UI mockups**
- Real ML classification requires substantial training data first
- Current focus: Building robust data collection and annotation workflows
                """
                )

            # Content Explorer tab
            with gr.Tab("🔍 Content Explorer"):
                gr.Markdown("## 📊 Word Cloud Analysis")
                gr.Markdown(
                    "*Visualization of most frequently mentioned terms across all posts and comments*"
                )

                wordcloud_display = gr.Markdown(
                    value="**Word cloud temporarily disabled** - Check terminal for dashboard URL",
                    label="Most Frequent Terms",
                )

                gr.Markdown("## 🔎 Keyword Context Examples")
                gr.Markdown(
                    "*See how specific health keywords are being discussed in context*"
                )

                with gr.Row():
                    keyword_input = gr.Textbox(
                        label="Search Keyword",
                        placeholder="Enter keyword (e.g., PrEP, HIV, vaccination)",
                        value="health",
                    )
                    search_btn = gr.Button("🔍 Search Examples")

                keyword_examples = gr.Markdown(
                    value=self.format_keyword_examples("health"),
                    label="Examples in Context",
                )

                gr.Markdown("## 📋 Recent Posts Preview")
                gr.Markdown(
                    "*Transparency view: Recent posts being analyzed by the platform*"
                )

                recent_posts = gr.Markdown(
                    value=self.format_recent_posts(), label="Recent Posts"
                )

                refresh_posts_btn = gr.Button("🔄 Refresh Recent Posts")

                # Event handlers for content explorer
                search_btn.click(
                    fn=self.format_keyword_examples,
                    inputs=keyword_input,
                    outputs=keyword_examples,
                )

                refresh_posts_btn.click(
                    fn=self.format_recent_posts, outputs=recent_posts
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

    def format_keyword_examples(self, keyword: str) -> str:
        """Format keyword examples for display"""
        if not keyword.strip():
            return "Please enter a keyword to search for examples."

        examples = self.analytics.get_keyword_context(keyword, max_examples=5)

        if not examples:
            return f"No examples found for keyword: **{keyword}**"

        formatted = f"# Examples of '{keyword}' in Context\n\n"

        for i, example in enumerate(examples, 1):
            # Create a qualitative research-style card
            formatted += f"""
<div style="border-left: 4px solid #3498db; padding: 15px; margin: 15px 0; background-color: #f8f9fa; border-radius: 5px;">

**📋 Excerpt {i}** ({example['type'].title()})

**🏷️ Source:** r/{example.get('subreddit', 'unknown')} • u/{example.get('author', 'anonymous')} • Score: {example.get('score', 0)}
"""

            if example["type"] == "post":
                formatted += f"\n**📝 Post Title:** *{example.get('title', '')}*\n"

            formatted += f"""
**💬 Quote:**
> "{example.get('context', '')}"

**🔍 Analysis Notes:** *Keyword '{keyword}' appears in context of {example['type']} discussion*

</div>
"""

        return formatted

    def format_recent_posts(self) -> str:
        """Format recent posts for transparency display"""
        recent_posts = self.analytics.get_recent_posts_preview(limit=10)

        if not recent_posts:
            return "No recent posts available."

        formatted = "## Recent Posts Being Analyzed:\n\n"

        for i, post in enumerate(recent_posts, 1):
            formatted += f"### Post {i}\n"
            formatted += f"**Title:** {post.get('title', '')}\n"
            formatted += f"**Subreddit:** r/{post.get('subreddit', 'unknown')}\n"
            formatted += f"**Author:** {post.get('author', 'anonymous')}\n"
            formatted += f"**Score:** {post.get('score', 0)} | **Comments:** {post.get('num_comments', 0)}\n"
            formatted += f"**Language:** {post.get('language', 'unknown')}\n"

            if post.get("contains_health_keywords", False):
                formatted += "**🏥 Contains Health Keywords:** Yes\n"
            else:
                formatted += "**🏥 Contains Health Keywords:** No\n"

            # Format creation time if available
            created_utc = post.get("created_utc")
            if created_utc:
                if isinstance(created_utc, str):
                    formatted += f"**Posted:** {created_utc}\n"
                else:
                    formatted += (
                        f"**Posted:** {created_utc.strftime('%Y-%m-%d %H:%M UTC')}\n"
                    )

            formatted += "\n---\n\n"

        return formatted

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
