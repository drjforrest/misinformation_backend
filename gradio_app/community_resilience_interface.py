#!/usr/bin/env python3
"""
Community Resilience & Social Capital Analysis Interface
Research platform for understanding supportive digital health ecosystems
"""

from typing import Dict, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from collections import defaultdict

import gradio as gr
from loguru import logger

from config.settings import Config
from src.data_persistence import DataPersistenceManager
from src.database_models import RedditPost, RedditComment
from src.network_analysis import NetworkAnalyzer
from src.translation_service import get_translation_service
from src.health_info_quality import HealthInfoQualityAnalyzer


class CommunityResilienceAnalyzer:
    """
    Analyzer for community resilience and social capital in digital health communities
    """

    def __init__(self):
        self.db_manager = DataPersistenceManager()
        self.network_analyzer = NetworkAnalyzer()
        self.translation_service = get_translation_service()
        self.quality_analyzer = HealthInfoQualityAnalyzer()

        # Resilience indicators
        self.support_keywords = [
            "help",
            "support",
            "advice",
            "experience",
            "recommend",
            "suggest",
            "thank",
            "appreciate",
            "grateful",
            "hope",
            "encourage",
            "share",
        ]

        self.health_seeking_keywords = [
            "question",
            "ask",
            "wonder",
            "confused",
            "worried",
            "concerned",
            "should i",
            "what if",
            "how to",
            "where can",
            "anyone else",
        ]

        self.knowledge_sharing_keywords = [
            "in my experience",
            "what worked for me",
            "i learned",
            "fyi",
            "resource",
            "link",
            "study",
            "research",
            "doctor said",
            "clinic",
        ]

        self.cultural_bridge_keywords = [
            "back home",
            "in my country",
            "cultural",
            "family",
            "traditional",
            "newcomer",
            "immigrant",
            "community",
            "understand",
        ]

    def calculate_support_metrics(self) -> Dict:
        """Calculate community support and resilience metrics"""
        with self.db_manager.get_session() as session:
            # Get all posts and comments
            posts = session.query(RedditPost).all()
            comments = session.query(RedditComment).all()

            metrics = {
                "total_posts": len(posts),
                "total_comments": len(comments),
                "support_posts": 0,
                "help_seeking_posts": 0,
                "knowledge_sharing_posts": 0,
                "cultural_bridge_posts": 0,
                "response_rate": 0,
                "avg_response_time_hours": 0,
                "peer_support_ratio": 0,
                "community_engagement_score": 0,
            }

            if not posts:
                return metrics

            # Analyze posts
            for post in posts:
                full_text = (post.title + " " + (post.selftext or "")).lower()

                # Support indicators
                if any(keyword in full_text for keyword in self.support_keywords):
                    metrics["support_posts"] += 1

                # Help-seeking behavior
                if any(
                    keyword in full_text for keyword in self.health_seeking_keywords
                ):
                    metrics["help_seeking_posts"] += 1

                # Knowledge sharing
                if any(
                    keyword in full_text for keyword in self.knowledge_sharing_keywords
                ):
                    metrics["knowledge_sharing_posts"] += 1

                # Cultural bridging
                if any(
                    keyword in full_text for keyword in self.cultural_bridge_keywords
                ):
                    metrics["cultural_bridge_posts"] += 1

            # Calculate derived metrics
            metrics["response_rate"] = (
                metrics["total_comments"] / max(metrics["total_posts"], 1)
            ) * 100
            metrics["peer_support_ratio"] = (
                metrics["support_posts"] / max(metrics["total_posts"], 1)
            ) * 100

            # Community engagement score (composite metric)
            engagement_factors = [
                metrics["response_rate"] / 100,  # Normalize to 0-1
                metrics["peer_support_ratio"] / 100,
                (metrics["help_seeking_posts"] / max(metrics["total_posts"], 1)),
                (metrics["knowledge_sharing_posts"] / max(metrics["total_posts"], 1)),
            ]
            metrics["community_engagement_score"] = np.mean(engagement_factors) * 100

            return metrics

    def analyze_peer_support_patterns(self) -> Tuple[str, go.Figure]:
        """Analyze patterns of peer support within communities"""
        with self.db_manager.get_session() as session:
            posts = session.query(RedditPost).all()
            comments = session.query(RedditComment).all()

            if not posts or not comments:
                return "No data available for peer support analysis.", go.Figure()

            # Build support interaction data
            support_data = defaultdict(lambda: defaultdict(int))
            help_seekers = set()
            helpers = set()

            # Identify help-seeking posts
            for post in posts:
                full_text = (post.title + " " + (post.selftext or "")).lower()
                if any(
                    keyword in full_text for keyword in self.health_seeking_keywords
                ):
                    help_seekers.add(post.author)

                    # Find responses to this post
                    post_comments = [c for c in comments if c.post_id == post.post_id]
                    for comment in post_comments:
                        if comment.author and comment.author != post.author:
                            helpers.add(comment.author)
                            support_data[post.subreddit]["responses"] += 1

                            # Check if response contains supportive language
                            comment_text = comment.body.lower() if comment.body else ""
                            if any(
                                keyword in comment_text
                                for keyword in self.support_keywords
                            ):
                                support_data[post.subreddit][
                                    "supportive_responses"
                                ] += 1

            # Create analysis text
            analysis_text = f"""
## 🤝 Peer Support Pattern Analysis

**Community Support Overview:**
- **Help Seekers:** {len(help_seekers)} unique users posting questions/concerns
- **Helpers:** {len(helpers)} unique users providing responses
- **Helper-to-Seeker Ratio:** {len(helpers)/max(len(help_seekers), 1):.2f}

**Support by Community:**
"""

            for subreddit, data in support_data.items():
                support_rate = (
                    data["supportive_responses"] / max(data["responses"], 1)
                ) * 100
                analysis_text += f"- **r/{subreddit}:** {data['responses']} responses, {support_rate:.1f}% supportive\n"

            # Create visualization
            if support_data:
                subreddits = list(support_data.keys())
                responses = [support_data[sub]["responses"] for sub in subreddits]
                supportive = [
                    support_data[sub]["supportive_responses"] for sub in subreddits
                ]

                fig = go.Figure(
                    data=[
                        go.Bar(name="Total Responses", x=subreddits, y=responses),
                        go.Bar(name="Supportive Responses", x=subreddits, y=supportive),
                    ]
                )
                fig.update_layout(
                    title="Community Response Patterns",
                    xaxis_title="Subreddit",
                    yaxis_title="Number of Responses",
                    barmode="group",
                )
            else:
                fig = go.Figure().add_annotation(
                    text="No support patterns detected",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                )

            return analysis_text, fig

    def analyze_knowledge_brokers(self) -> Tuple[str, go.Figure]:
        """Identify and analyze knowledge brokers in the community"""
        with self.db_manager.get_session() as session:
            posts = session.query(RedditPost).all()
            comments = session.query(RedditComment).all()

            if not posts and not comments:
                return "No data available for knowledge broker analysis.", go.Figure()

            # Calculate user engagement metrics
            user_metrics = defaultdict(
                lambda: {
                    "posts": 0,
                    "comments": 0,
                    "knowledge_shares": 0,
                    "support_given": 0,
                    "subreddits": set(),
                    "total_score": 0,
                }
            )

            # Analyze posts
            for post in posts:
                if not post.author or post.author == "[deleted]":
                    continue

                user_metrics[post.author]["posts"] += 1
                user_metrics[post.author]["subreddits"].add(post.subreddit)
                user_metrics[post.author]["total_score"] += post.score or 0

                full_text = (post.title + " " + (post.selftext or "")).lower()
                if any(
                    keyword in full_text for keyword in self.knowledge_sharing_keywords
                ):
                    user_metrics[post.author]["knowledge_shares"] += 1
                if any(keyword in full_text for keyword in self.support_keywords):
                    user_metrics[post.author]["support_given"] += 1

            # Analyze comments
            for comment in comments:
                if not comment.author or comment.author == "[deleted]":
                    continue

                user_metrics[comment.author]["comments"] += 1
                user_metrics[comment.author]["total_score"] += comment.score or 0

                comment_text = comment.body.lower() if comment.body else ""
                if any(
                    keyword in comment_text
                    for keyword in self.knowledge_sharing_keywords
                ):
                    user_metrics[comment.author]["knowledge_shares"] += 1
                if any(keyword in comment_text for keyword in self.support_keywords):
                    user_metrics[comment.author]["support_given"] += 1

            # Calculate broker scores
            broker_scores = []
            for user, metrics in user_metrics.items():
                total_activity = metrics["posts"] + metrics["comments"]
                if total_activity >= 3:  # Minimum activity threshold
                    broker_score = (
                        metrics["knowledge_shares"]
                        * 3  # Weight knowledge sharing heavily
                        + metrics["support_given"] * 2  # Weight support giving
                        + len(metrics["subreddits"]) * 1.5  # Cross-community activity
                        + min(metrics["total_score"], 100)
                        / 100  # Normalized community approval
                    ) / total_activity  # Normalize by activity level

                    broker_scores.append(
                        {
                            "user": user,
                            "score": broker_score,
                            "knowledge_shares": metrics["knowledge_shares"],
                            "support_given": metrics["support_given"],
                            "communities": len(metrics["subreddits"]),
                            "total_activity": total_activity,
                            "avg_score": metrics["total_score"]
                            / max(total_activity, 1),
                        }
                    )

            # Sort by broker score
            broker_scores.sort(key=lambda x: x["score"], reverse=True)
            top_brokers = broker_scores[:10]

            # Create analysis text
            analysis_text = """
## 🌟 Knowledge Broker Analysis

**Top Community Knowledge Brokers:**
*Users who consistently share knowledge and provide support across communities*

"""

            for i, broker in enumerate(top_brokers, 1):
                analysis_text += f"""
**{i}. {broker['user'][:20]}{'...' if len(broker['user']) > 20 else ''}**
- Broker Score: {broker['score']:.2f}
- Knowledge Shares: {broker['knowledge_shares']}
- Support Given: {broker['support_given']}
- Active Communities: {broker['communities']}
- Total Activity: {broker['total_activity']} posts/comments
- Avg Community Score: {broker['avg_score']:.1f}
"""

            # Create visualization
            if top_brokers:
                users = [
                    (
                        broker["user"][:15] + "..."
                        if len(broker["user"]) > 15
                        else broker["user"]
                    )
                    for broker in top_brokers
                ]
                scores = [broker["score"] for broker in top_brokers]
                knowledge_shares = [
                    broker["knowledge_shares"] for broker in top_brokers
                ]
                support_given = [broker["support_given"] for broker in top_brokers]

                fig = make_subplots(
                    rows=1,
                    cols=2,
                    subplot_titles=("Broker Scores", "Activity Breakdown"),
                    specs=[[{"type": "bar"}, {"type": "bar"}]],
                )

                fig.add_trace(
                    go.Bar(x=users, y=scores, name="Broker Score"), row=1, col=1
                )

                fig.add_trace(
                    go.Bar(x=users, y=knowledge_shares, name="Knowledge Shares"),
                    row=1,
                    col=2,
                )
                fig.add_trace(
                    go.Bar(x=users, y=support_given, name="Support Given"), row=1, col=2
                )

                fig.update_layout(
                    title="Community Knowledge Brokers", showlegend=True, height=500
                )
                fig.update_xaxes(tickangle=45)

            else:
                fig = go.Figure().add_annotation(
                    text="No knowledge brokers identified",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                )

            return analysis_text, fig

    def analyze_cultural_adaptation(self) -> Tuple[str, go.Figure]:
        """Analyze how health information gets culturally adapted within communities"""
        with self.db_manager.get_session() as session:
            posts = session.query(RedditPost).all()
            comments = session.query(RedditComment).all()

            if not posts:
                return (
                    "No data available for cultural adaptation analysis.",
                    go.Figure(),
                )

            # Identify culturally-relevant content
            cultural_content = defaultdict(list)
            language_adaptation = defaultdict(int)

            all_content = posts + comments
            for item in all_content:
                if hasattr(item, "title"):  # Post
                    text = (item.title + " " + (item.selftext or "")).lower()
                    content_type = "post"
                else:  # Comment
                    text = (item.body or "").lower()
                    content_type = "comment"

                # Check for cultural bridging language
                cultural_indicators = []
                for keyword in self.cultural_bridge_keywords:
                    if keyword in text:
                        cultural_indicators.append(keyword)

                if cultural_indicators:
                    subreddit = getattr(item, "subreddit", "unknown")
                    cultural_content[subreddit].append(
                        {
                            "type": content_type,
                            "author": getattr(item, "author", "unknown"),
                            "text": text[:200] + "..." if len(text) > 200 else text,
                            "indicators": cultural_indicators,
                            "language": getattr(item, "language", "en"),
                        }
                    )

                # Track language diversity
                if hasattr(item, "language") and item.language:
                    language_adaptation[item.language] += 1

            # Create analysis text
            analysis_text = """
## 🌍 Cultural Adaptation Analysis

**Language Diversity:**
"""
            for lang, count in sorted(
                language_adaptation.items(), key=lambda x: x[1], reverse=True
            ):
                lang_name = {
                    "en": "English",
                    "es": "Spanish",
                    "tl": "Tagalog",
                    "zh-CN": "Chinese (Simplified)",
                    "fr": "French",
                    "pa": "Punjabi",
                }.get(lang, lang.upper())
                analysis_text += f"- **{lang_name}:** {count} posts/comments\n"

            analysis_text += """

**Cultural Bridging by Community:**
"""

            for subreddit, content_list in cultural_content.items():
                analysis_text += f"\n**r/{subreddit}:** {len(content_list)} culturally-relevant posts/comments\n"

                # Show examples
                for item in content_list[:3]:  # Top 3 examples
                    indicators_str = ", ".join(item["indicators"])
                    analysis_text += f"  - *{item['text'][:100]}...* (indicators: {indicators_str})\n"

            # Create visualization
            if cultural_content:
                subreddits = list(cultural_content.keys())
                counts = [len(cultural_content[sub]) for sub in subreddits]

                # Language distribution
                languages = list(language_adaptation.keys())
                lang_counts = list(language_adaptation.values())

                fig = make_subplots(
                    rows=1,
                    cols=2,
                    subplot_titles=(
                        "Cultural Content by Community",
                        "Language Distribution",
                    ),
                    specs=[[{"type": "bar"}, {"type": "pie"}]],
                )

                fig.add_trace(
                    go.Bar(x=subreddits, y=counts, name="Cultural Content"),
                    row=1,
                    col=1,
                )

                fig.add_trace(
                    go.Pie(labels=languages, values=lang_counts, name="Languages"),
                    row=1,
                    col=2,
                )

                fig.update_layout(
                    title="Cultural Adaptation Patterns", showlegend=False
                )
            else:
                fig = go.Figure().add_annotation(
                    text="No cultural adaptation patterns detected",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                )

            return analysis_text, fig

    def generate_resilience_report(self) -> str:
        """Generate comprehensive community resilience report"""
        metrics = self.calculate_support_metrics()

        # Resilience level assessment
        engagement_score = metrics["community_engagement_score"]
        if engagement_score >= 80:
            resilience_level = "Very High"
            resilience_color = "🟢"
        elif engagement_score >= 60:
            resilience_level = "High"
            resilience_color = "🟡"
        elif engagement_score >= 40:
            resilience_level = "Moderate"
            resilience_color = "🟠"
        else:
            resilience_level = "Developing"
            resilience_color = "🔴"

        report = f"""
# 🏥 Community Health Resilience Report

## Overall Assessment
{resilience_color} **Resilience Level: {resilience_level}**
**Community Engagement Score: {engagement_score:.1f}/100**

## Key Metrics

### Community Activity
- **Total Posts:** {metrics['total_posts']:,}
- **Total Comments:** {metrics['total_comments']:,}
- **Response Rate:** {metrics['response_rate']:.1f}% (comments per post)

### Support Dynamics
- **Support-Oriented Posts:** {metrics['support_posts']:,} ({metrics['peer_support_ratio']:.1f}%)
- **Help-Seeking Posts:** {metrics['help_seeking_posts']:,}
- **Knowledge-Sharing Posts:** {metrics['knowledge_sharing_posts']:,}
- **Cultural Bridge Posts:** {metrics['cultural_bridge_posts']:,}

## Resilience Indicators

### ✅ Strengths Identified
"""

        # Identify strengths
        if metrics["peer_support_ratio"] > 20:
            report += (
                "- **High Peer Support Culture** - Community actively helps members\n"
            )
        if metrics["response_rate"] > 150:
            report += "- **Active Engagement** - Posts consistently receive multiple responses\n"
        if metrics["help_seeking_posts"] > 0:
            report += "- **Safe Space for Vulnerability** - Members feel comfortable asking for help\n"
        if metrics["cultural_bridge_posts"] > 0:
            report += "- **Cultural Competence** - Community bridges cultural health knowledge\n"

        report += """

### 📊 Policy & Research Implications

**For Public Health:**
- This community demonstrates strong peer support networks
- Members actively share health knowledge and experiences
- Cultural adaptation of health information occurs naturally

**For Community Health Programs:**
- Partner with existing knowledge brokers for health promotion
- Amplify successful peer support patterns
- Support cultural bridging of health information

**For Healthcare Providers:**
- Recognize community wisdom and peer support value
- Develop culturally-responsive resources based on community patterns
- Consider community leaders as health promotion partners
"""

        return report


class CommunityResilienceInterface:
    """
    Interface for Community Resilience & Social Capital Analysis
    """

    def __init__(self):
        self.analyzer = CommunityResilienceAnalyzer()

    def create_interface(self):
        """Create the community resilience analysis interface"""

        with gr.Blocks(
            title="Community Resilience & Social Capital Analysis",
            theme=gr.themes.Soft(),
        ) as interface:

            gr.HTML("<h1>🤝 Community Resilience & Social Capital Analysis</h1>")
            gr.HTML(
                "<p>Understanding supportive digital health ecosystems in immigrant communities</p>"
            )

            with gr.Tabs():
                # Community Overview Tab
                with gr.Tab("🏥 Resilience Overview"):
                    overview_btn = gr.Button(
                        "📊 Generate Resilience Report", variant="primary"
                    )
                    resilience_report = gr.Markdown()

                    overview_btn.click(
                        self.analyzer.generate_resilience_report,
                        outputs=resilience_report,
                    )

                # Peer Support Analysis Tab
                with gr.Tab("🤝 Peer Support Patterns"):
                    support_btn = gr.Button(
                        "🤝 Analyze Peer Support", variant="primary"
                    )

                    with gr.Row():
                        support_analysis = gr.Markdown()
                        support_plot = gr.Plot()

                    support_btn.click(
                        self.analyzer.analyze_peer_support_patterns,
                        outputs=[support_analysis, support_plot],
                    )

                # Knowledge Brokers Tab
                with gr.Tab("🌟 Knowledge Brokers"):
                    brokers_btn = gr.Button(
                        "🌟 Identify Knowledge Brokers", variant="primary"
                    )

                    with gr.Row():
                        brokers_analysis = gr.Markdown()
                        brokers_plot = gr.Plot()

                    brokers_btn.click(
                        self.analyzer.analyze_knowledge_brokers,
                        outputs=[brokers_analysis, brokers_plot],
                    )

                # Cultural Adaptation Tab
                with gr.Tab("🌍 Cultural Adaptation"):
                    cultural_btn = gr.Button(
                        "🌍 Analyze Cultural Adaptation", variant="primary"
                    )

                    with gr.Row():
                        cultural_analysis = gr.Markdown()
                        cultural_plot = gr.Plot()

                    cultural_btn.click(
                        self.analyzer.analyze_cultural_adaptation,
                        outputs=[cultural_analysis, cultural_plot],
                    )

                # Health Information Quality Tab
                with gr.Tab("💡 Information Quality"):
                    with gr.Row():
                        quality_community = gr.Textbox(
                            label="Focus Community (optional)",
                            placeholder="e.g., askgaybros",
                        )
                        quality_btn = gr.Button(
                            "💡 Analyze Information Quality", variant="primary"
                        )

                    quality_analysis = gr.Markdown()
                    quality_suggestions = gr.Markdown()

                    def analyze_info_quality(community):
                        analysis = self.analyzer.quality_analyzer.analyze_community_info_quality(
                            community if community.strip() else None
                        )
                        suggestions = self.analyzer.quality_analyzer.generate_quality_improvement_suggestions(
                            community if community.strip() else None
                        )

                        if "error" in analysis:
                            return analysis["error"], "No suggestions available"

                        # Format analysis
                        overall = analysis["overall_stats"]
                        community_data = analysis["community_quality"]

                        analysis_text = f"""
## 💡 Health Information Quality Analysis

**Overall Quality Metrics:**
- **Posts Analyzed:** {overall['total_posts']:,}
- **Average Quality Score:** {overall['avg_quality']:.2f}/1.0
- **Average Helpfulness:** {overall['avg_helpfulness']:.2f}/1.0

**Quality by Community:**
"""
                        for comm, stats in community_data.items():
                            quality_level = (
                                "High"
                                if stats["avg_quality"] > 0.7
                                else (
                                    "Medium"
                                    if stats["avg_quality"] > 0.3
                                    else "Developing"
                                )
                            )
                            analysis_text += f"""
**r/{comm}:**
- Quality Level: {quality_level} ({stats['avg_quality']:.2f})
- Posts Analyzed: {stats['posts_analyzed']}
- High Quality: {stats['high_quality_posts']} posts
- Medium Quality: {stats['medium_quality_posts']} posts
- Needs Support: {stats['low_quality_posts']} posts
"""

                        suggestions_text = (
                            "## 🎯 Quality Enhancement Suggestions\n\n"
                            + "\n".join(suggestions)
                        )

                        return analysis_text, suggestions_text

                    quality_btn.click(
                        analyze_info_quality,
                        inputs=quality_community,
                        outputs=[quality_analysis, quality_suggestions],
                    )

                # Network Analysis Tab
                with gr.Tab("🕸️ Social Capital Networks"):
                    with gr.Row():
                        network_subreddit = gr.Textbox(
                            label="Focus Community (optional)",
                            placeholder="e.g., askgaybros",
                        )
                        network_btn = gr.Button(
                            "🕸️ Analyze Social Networks", variant="primary"
                        )

                    network_plot = gr.Plot()

                    network_btn.click(
                        self.analyzer.network_analyzer.create_network_visualization,
                        inputs=network_subreddit,
                        outputs=network_plot,
                    )

                # Research Insights Tab
                with gr.Tab("📈 Research Insights"):
                    gr.HTML(
                        """
                    <h3>Research Framework: Community Resilience Theory</h3>
                    <p>This analysis framework draws from:</p>
                    <ul>
                        <li><strong>Social Capital Theory:</strong> Measuring bonding, bridging, and linking social capital</li>
                        <li><strong>Community Resilience:</strong> Capacity to adapt and thrive despite challenges</li>
                        <li><strong>Digital Health Ecosystems:</strong> How online communities support health behaviors</li>
                        <li><strong>Cultural Health Capital:</strong> Community-specific health knowledge and practices</li>
                    </ul>
                    
                    <h4>Key Research Applications:</h4>
                    <ul>
                        <li>Public health intervention design</li>
                        <li>Community-based participatory research</li>
                        <li>Health equity policy development</li>
                        <li>Digital health platform design</li>
                    </ul>
                    """
                    )

            # Initialize with resilience report
            interface.load(
                self.analyzer.generate_resilience_report, outputs=resilience_report
            )

        return interface


def launch_community_resilience_interface():
    """Launch the community resilience analysis interface"""
    logger.info("Launching Community Resilience Analysis Interface...")

    interface = CommunityResilienceInterface()
    app = interface.create_interface()

    app.launch(
        server_name="0.0.0.0",
        server_port=7862,  # Different port from other interfaces
        share=Config.GRADIO_SHARE,
        show_error=True,
    )


if __name__ == "__main__":
    launch_community_resilience_interface()
