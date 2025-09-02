#!/usr/bin/env python3
"""
Analytics Dashboard for Health Misinformation Research
Provides comprehensive insights and visualizations for research teams
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from collections import Counter, defaultdict
from typing import Dict, List, Any
from datetime import datetime
import json
from pathlib import Path
from loguru import logger

from src.data_persistence import DataPersistenceManager
from src.database_models import RedditPost, RedditComment
from config.settings import ResearchConfig


class HealthMisinformationAnalytics:
    """
    Comprehensive analytics for health misinformation research
    Provides insights for research teams and stakeholders
    """

    def __init__(self):
        self.db_manager = DataPersistenceManager()
        self.posts_data = []
        self.comments_data = []
        self.analytics_cache = {}

    def load_data(self) -> Dict[str, int]:
        """Load all posts and comments from database"""
        logger.info("Loading data for analytics...")

        with self.db_manager.get_session() as session:
            # Load posts
            posts = session.query(RedditPost).all()
            self.posts_data = [
                {
                    "post_id": post.post_id,
                    "subreddit": post.subreddit,
                    "title": post.title,
                    "selftext": post.selftext or "",
                    "author": post.author,
                    "created_utc": post.created_utc,
                    "score": post.score,
                    "num_comments": post.num_comments,
                    "language": post.language,
                    "is_newcomer_related": post.is_newcomer_related,
                    "english_translation": getattr(post, "english_translation", None),
                    "contains_health_keywords": getattr(
                        post, "contains_health_keywords", False
                    ),
                    "keyword_count": getattr(post, "keyword_count", 0),
                }
                for post in posts
            ]

            # Load comments
            comments = session.query(RedditComment).all()
            self.comments_data = [
                {
                    "comment_id": comment.comment_id,
                    "post_id": comment.post_id,
                    "author": comment.author,
                    "body": comment.body,
                    "created_utc": comment.created_utc,
                    "score": comment.score,
                    "language": comment.language,
                    "english_translation": getattr(
                        comment, "english_translation", None
                    ),
                }
                for comment in comments
            ]

        stats = {
            "total_posts": len(self.posts_data),
            "total_comments": len(self.comments_data),
            "unique_authors": len(
                set(
                    [p["author"] for p in self.posts_data]
                    + [c["author"] for c in self.comments_data]
                )
            ),
        }

        logger.info(
            f"Loaded {stats['total_posts']} posts, {stats['total_comments']} comments from {stats['unique_authors']} unique authors"
        )
        return stats

    def analyze_language_distribution(self) -> Dict[str, Any]:
        """Analyze language distribution across posts and comments"""

        # Posts by language
        post_languages = Counter(
            [p["language"] for p in self.posts_data if p["language"]]
        )

        # Comments by language
        comment_languages = Counter(
            [c["language"] for c in self.comments_data if c["language"]]
        )

        # Multilingual posts (posts with translations)
        multilingual_posts = len(
            [p for p in self.posts_data if p["english_translation"]]
        )

        # Language coverage
        all_languages = set(post_languages.keys()) | set(comment_languages.keys())

        return {
            "post_languages": dict(post_languages),
            "comment_languages": dict(comment_languages),
            "total_languages": len(all_languages),
            "multilingual_posts": multilingual_posts,
            "multilingual_percentage": (
                (multilingual_posts / len(self.posts_data) * 100)
                if self.posts_data
                else 0
            ),
        }

    def analyze_health_keywords(self) -> Dict[str, Any]:
        """Analyze health keyword usage across posts"""

        # Health keywords from config
        primary_keywords = ResearchConfig.PRIMARY_KEYWORDS
        colloquial_terms = ResearchConfig.COLLOQUIAL_TERMS
        all_keywords = primary_keywords + colloquial_terms

        keyword_counts = defaultdict(int)
        posts_with_keywords = []

        for post in self.posts_data:
            full_text = (post["title"] + " " + post["selftext"]).lower()
            found_keywords = []

            for keyword in all_keywords:
                if keyword.lower() in full_text:
                    keyword_counts[keyword] += 1
                    found_keywords.append(keyword)

            if found_keywords:
                posts_with_keywords.append(
                    {
                        "post_id": post["post_id"],
                        "subreddit": post["subreddit"],
                        "keywords": found_keywords,
                        "keyword_count": len(found_keywords),
                        "language": post["language"],
                        "is_newcomer_related": post["is_newcomer_related"],
                    }
                )

        # Top keyword combinations
        keyword_combinations = defaultdict(int)
        for post in posts_with_keywords:
            if len(post["keywords"]) > 1:
                combo = tuple(sorted(post["keywords"]))
                keyword_combinations[combo] += 1

        return {
            "keyword_counts": dict(keyword_counts),
            "posts_with_keywords": len(posts_with_keywords),
            "keyword_coverage": (
                (len(posts_with_keywords) / len(self.posts_data) * 100)
                if self.posts_data
                else 0
            ),
            "top_combinations": {
                ", ".join(combo): count
                for combo, count in sorted(
                    keyword_combinations.items(), key=lambda x: x[1], reverse=True
                )[:10]
            },
            "posts_with_keywords_data": posts_with_keywords,
        }

    def analyze_subreddit_patterns(self) -> Dict[str, Any]:
        """Analyze patterns across different subreddits"""

        subreddit_stats = defaultdict(
            lambda: {
                "post_count": 0,
                "comment_count": 0,
                "languages": set(),
                "health_keywords": 0,
                "newcomer_posts": 0,
                "avg_score": 0,
                "total_score": 0,
            }
        )

        # Analyze posts by subreddit
        for post in self.posts_data:
            sub = post["subreddit"]
            subreddit_stats[sub]["post_count"] += 1
            if post["language"]:
                subreddit_stats[sub]["languages"].add(post["language"])
            if post["contains_health_keywords"]:
                subreddit_stats[sub]["health_keywords"] += 1
            if post["is_newcomer_related"]:
                subreddit_stats[sub]["newcomer_posts"] += 1
            if post["score"]:
                subreddit_stats[sub]["total_score"] += post["score"]

        # Calculate averages and convert sets to lists
        for sub, stats in subreddit_stats.items():
            if stats["post_count"] > 0:
                stats["avg_score"] = stats["total_score"] / stats["post_count"]
            stats["languages"] = list(stats["languages"])
            stats["language_diversity"] = len(stats["languages"])

        # Count comments per subreddit
        comment_counts = defaultdict(int)
        for comment in self.comments_data:
            # Find the subreddit for this comment's post
            post = next(
                (p for p in self.posts_data if p["post_id"] == comment["post_id"]), None
            )
            if post:
                comment_counts[post["subreddit"]] += 1

        for sub, count in comment_counts.items():
            subreddit_stats[sub]["comment_count"] = count

        return dict(subreddit_stats)

    def analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze temporal patterns in posts"""

        # Convert dates and analyze
        posts_with_dates = [p for p in self.posts_data if p["created_utc"]]

        if not posts_with_dates:
            return {"error": "No posts with valid dates found"}

        # Daily posting patterns
        daily_counts = defaultdict(int)
        weekly_counts = defaultdict(int)
        hourly_counts = defaultdict(int)

        for post in posts_with_dates:
            date = post["created_utc"]
            if isinstance(date, str):
                date = datetime.fromisoformat(date.replace("Z", "+00:00"))

            daily_counts[date.strftime("%Y-%m-%d")] += 1
            weekly_counts[date.strftime("%Y-W%U")] += 1
            hourly_counts[date.hour] += 1

        return {
            "daily_counts": dict(daily_counts),
            "weekly_counts": dict(weekly_counts),
            "hourly_counts": dict(hourly_counts),
            "date_range": {
                "earliest": min(
                    p["created_utc"] for p in posts_with_dates if p["created_utc"]
                ),
                "latest": max(
                    p["created_utc"] for p in posts_with_dates if p["created_utc"]
                ),
            },
        }

    def analyze_newcomer_content(self) -> Dict[str, Any]:
        """Analyze content specifically related to newcomers"""

        newcomer_posts = [p for p in self.posts_data if p["is_newcomer_related"]]

        # Language distribution for newcomer posts
        newcomer_languages = Counter(
            [p["language"] for p in newcomer_posts if p["language"]]
        )

        # Health topics in newcomer posts
        newcomer_keywords = defaultdict(int)
        for post in newcomer_posts:
            full_text = (post["title"] + " " + post["selftext"]).lower()
            for keyword in (
                ResearchConfig.PRIMARY_KEYWORDS + ResearchConfig.COLLOQUIAL_TERMS
            ):
                if keyword.lower() in full_text:
                    newcomer_keywords[keyword] += 1

        # Subreddit distribution for newcomer posts
        newcomer_subreddits = Counter([p["subreddit"] for p in newcomer_posts])

        return {
            "total_newcomer_posts": len(newcomer_posts),
            "percentage_newcomer": (
                (len(newcomer_posts) / len(self.posts_data) * 100)
                if self.posts_data
                else 0
            ),
            "newcomer_languages": dict(newcomer_languages),
            "newcomer_keywords": dict(newcomer_keywords),
            "newcomer_subreddits": dict(newcomer_subreddits),
        }

    def generate_insights(self) -> Dict[str, List[str]]:
        """Generate actionable insights for research teams"""

        insights = {
            "language_insights": [],
            "content_insights": [],
            "engagement_insights": [],
            "research_recommendations": [],
        }

        # Load analytics data
        lang_data = self.analyze_language_distribution()
        keyword_data = self.analyze_health_keywords()
        subreddit_data = self.analyze_subreddit_patterns()
        newcomer_data = self.analyze_newcomer_content()

        # Language insights
        if lang_data["multilingual_percentage"] > 10:
            insights["language_insights"].append(
                f"🌐 {lang_data['multilingual_percentage']:.1f}% of posts contain multilingual content requiring translation"
            )

        top_languages = sorted(
            lang_data["post_languages"].items(), key=lambda x: x[1], reverse=True
        )[:3]
        if top_languages:
            insights["language_insights"].append(
                f"📊 Top non-English languages: {', '.join([f'{lang} ({count} posts)' for lang, count in top_languages if lang != 'en'])}"
            )

        # Content insights
        if keyword_data["keyword_coverage"] > 0:
            insights["content_insights"].append(
                f"🔍 {keyword_data['keyword_coverage']:.1f}% of posts contain health-related keywords"
            )

        top_keywords = sorted(
            keyword_data["keyword_counts"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        if top_keywords:
            insights["content_insights"].append(
                f"🏥 Most discussed health topics: {', '.join([f'{kw} ({count})' for kw, count in top_keywords])}"
            )

        # Engagement insights
        high_engagement_subs = [
            (sub, data)
            for sub, data in subreddit_data.items()
            if data["avg_score"] > 10
        ]
        if high_engagement_subs:
            high_engagement_subs.sort(key=lambda x: x[1]["avg_score"], reverse=True)
            insights["engagement_insights"].append(
                f"🔥 Highest engagement subreddits: {', '.join([f'r/{sub} (avg score: {data["avg_score"]:.1f})' for sub, data in high_engagement_subs[:3]])}"
            )

        # Newcomer insights
        if newcomer_data["total_newcomer_posts"] > 0:
            insights["content_insights"].append(
                f"🆕 {newcomer_data['total_newcomer_posts']} posts ({newcomer_data['percentage_newcomer']:.1f}%) specifically target newcomer communities"
            )

        # Research recommendations
        if lang_data["total_languages"] > 3:
            insights["research_recommendations"].append(
                "🔬 Consider developing language-specific misinformation detection models"
            )

        if keyword_data["keyword_coverage"] < 50:
            insights["research_recommendations"].append(
                "📝 Expand health keyword dictionary - current coverage may miss relevant posts"
            )

        if newcomer_data["percentage_newcomer"] > 20:
            insights["research_recommendations"].append(
                "🎯 Focus intervention strategies on newcomer-specific platforms and content"
            )

        diverse_subs = [
            sub
            for sub, data in subreddit_data.items()
            if data["language_diversity"] > 2
        ]
        if diverse_subs:
            insights["research_recommendations"].append(
                f"🌍 Prioritize multilingual monitoring in: {', '.join([f'r/{sub}' for sub in diverse_subs[:3]])}"
            )

        return insights

    def create_visualizations(self) -> Dict[str, go.Figure]:
        """Create comprehensive visualizations for the dashboard"""

        figures = {}

        # Language distribution visualization
        lang_data = self.analyze_language_distribution()
        if lang_data["post_languages"]:
            fig = px.pie(
                values=list(lang_data["post_languages"].values()),
                names=list(lang_data["post_languages"].keys()),
                title="Posts by Language Distribution",
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            figures["language_distribution"] = fig

        # Health keywords bar chart
        keyword_data = self.analyze_health_keywords()
        if keyword_data["keyword_counts"]:
            top_keywords = dict(
                sorted(
                    keyword_data["keyword_counts"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:15]
            )
            fig = px.bar(
                x=list(top_keywords.values()),
                y=list(top_keywords.keys()),
                orientation="h",
                title="Most Mentioned Health Keywords",
                labels={"x": "Frequency", "y": "Keywords"},
            )
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            figures["health_keywords"] = fig

        # Subreddit analysis
        subreddit_data = self.analyze_subreddit_patterns()
        if subreddit_data:
            sub_names = list(subreddit_data.keys())
            post_counts = [data["post_count"] for data in subreddit_data.values()]
            keyword_counts = [
                data["health_keywords"] for data in subreddit_data.values()
            ]

            fig = make_subplots(
                rows=1,
                cols=2,
                subplot_titles=("Posts per Subreddit", "Health Keywords per Subreddit"),
                specs=[[{"type": "bar"}, {"type": "bar"}]],
            )

            fig.add_trace(
                go.Bar(x=sub_names, y=post_counts, name="Posts"), row=1, col=1
            )

            fig.add_trace(
                go.Bar(
                    x=sub_names,
                    y=keyword_counts,
                    name="Health Keywords",
                    marker_color="orange",
                ),
                row=1,
                col=2,
            )

            fig.update_layout(
                title_text="Subreddit Activity Analysis", showlegend=False
            )
            figures["subreddit_analysis"] = fig

        # Multilingual content analysis
        multilingual_posts = len(
            [p for p in self.posts_data if p["english_translation"]]
        )
        english_only = len(self.posts_data) - multilingual_posts

        if multilingual_posts > 0:
            fig = px.pie(
                values=[english_only, multilingual_posts],
                names=["English Only", "Multilingual/Translated"],
                title="Content Language Composition",
                color_discrete_map={
                    "English Only": "#3498db",
                    "Multilingual/Translated": "#e74c3c",
                },
            )
            figures["multilingual_composition"] = fig

        # Newcomer-related content
        newcomer_data = self.analyze_newcomer_content()
        if newcomer_data["total_newcomer_posts"] > 0:
            newcomer_count = newcomer_data["total_newcomer_posts"]
            general_count = len(self.posts_data) - newcomer_count

            fig = px.pie(
                values=[general_count, newcomer_count],
                names=["General Content", "Newcomer-Focused"],
                title="Newcomer-Related Content Distribution",
                color_discrete_map={
                    "General Content": "#95a5a6",
                    "Newcomer-Focused": "#2ecc71",
                },
            )
            figures["newcomer_content"] = fig

        return figures

    def export_analytics_report(self, output_path: str = "data/analytics_report.json"):
        """Export comprehensive analytics report"""

        logger.info("Generating comprehensive analytics report...")

        report = {
            "generated_at": datetime.now().isoformat(),
            "data_summary": self.load_data(),
            "language_analysis": self.analyze_language_distribution(),
            "keyword_analysis": self.analyze_health_keywords(),
            "subreddit_analysis": self.analyze_subreddit_patterns(),
            "temporal_analysis": self.analyze_temporal_patterns(),
            "newcomer_analysis": self.analyze_newcomer_content(),
            "insights": self.generate_insights(),
        }

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Save report
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Analytics report saved to {output_path}")
        return report


if __name__ == "__main__":
    # Generate analytics report
    analytics = HealthMisinformationAnalytics()
    report = analytics.export_analytics_report()

    print("🔍 Health Misinformation Research Analytics")
    print("=" * 50)

    # Print key insights
    insights = report["insights"]
    for category, insight_list in insights.items():
        if insight_list:
            print(f"\n{category.replace('_', ' ').title()}:")
            for insight in insight_list:
                print(f"  {insight}")
