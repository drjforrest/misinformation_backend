"""
Health Information Quality Assessment Module
For analyzing the quality and helpfulness of community-shared health information
"""

from typing import Dict, List, Optional
from collections import defaultdict
import numpy as np

from src.data_persistence import DataPersistenceManager
from src.database_models import RedditPost


class HealthInfoQualityAnalyzer:
    """
    Analyzer for assessing quality and helpfulness of health information shared in communities
    Focus on supportive, accurate information rather than misinformation detection
    """

    def __init__(self):
        self.db_manager = DataPersistenceManager()

        # Quality indicators (positive signals)
        self.quality_indicators = {
            "evidence_based": [
                "study shows",
                "research indicates",
                "clinical trial",
                "peer reviewed",
                "meta-analysis",
                "systematic review",
                "published",
                "evidence suggests",
                "studies show",
                "according to research",
            ],
            "professional_source": [
                "doctor said",
                "my physician",
                "healthcare provider",
                "clinic told me",
                "medical professional",
                "my doctor",
                "specialist explained",
                "nurse said",
                "pharmacist",
                "counselor",
            ],
            "personal_experience": [
                "in my experience",
                "what worked for me",
                "my journey",
                "personally",
                "from my experience",
                "what helped me",
                "my story",
                "i found that",
            ],
            "resource_sharing": [
                "here's a link",
                "resource",
                "website",
                "organization",
                "support group",
                "helpline",
                "clinic",
                "program",
                "service",
                "check out",
            ],
            "encouraging": [
                "you can do this",
                "stay strong",
                "proud of you",
                "you're brave",
                "sending support",
                "here for you",
                "you matter",
                "not alone",
            ],
            "cautious_language": [
                "talk to your doctor",
                "consult a professional",
                "seek medical advice",
                "everyone's different",
                "may vary",
                "consider discussing",
                "might want to ask",
            ],
        }

        # Concern indicators (potential quality issues)
        self.concern_indicators = {
            "absolute_claims": [
                "always works",
                "never fails",
                "guaranteed cure",
                "definitely will",
                "100% effective",
                "miracle cure",
                "instant relief",
            ],
            "anti_medical": [
                "doctors don't know",
                "big pharma",
                "medical conspiracy",
                "don't trust doctors",
                "natural is better",
                "avoid medication",
            ],
            "fear_mongering": [
                "you will die",
                "extremely dangerous",
                "terrible side effects",
                "ruined my life",
                "destroyed",
                "poison",
            ],
        }

        # Health literacy indicators
        self.health_literacy_markers = {
            "high": [
                "side effects",
                "efficacy",
                "dosage",
                "contraindications",
                "clinical",
                "mechanism",
                "pharmacology",
                "bioavailability",
            ],
            "medium": [
                "treatment",
                "symptoms",
                "diagnosis",
                "prevention",
                "risk factors",
                "lifestyle",
                "immune system",
                "infection",
            ],
            "accessible": [
                "feeling",
                "experience",
                "what happens",
                "how it works",
                "simple terms",
                "easy to understand",
                "basically",
            ],
        }

    def assess_post_quality(self, post_text: str) -> Dict[str, float]:
        """Assess the quality of health information in a post"""
        text = post_text.lower()
        quality_scores = {}

        # Calculate quality indicator scores
        for category, indicators in self.quality_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in text)
            quality_scores[f"quality_{category}"] = min(
                matches / max(len(indicators) * 0.1, 1), 1.0
            )

        # Calculate concern scores (negative indicators)
        for category, indicators in self.concern_indicators.items():
            matches = sum(1 for indicator in indicators if indicator in text)
            quality_scores[f"concern_{category}"] = min(
                matches / max(len(indicators) * 0.1, 1), 1.0
            )

        # Calculate health literacy level
        literacy_scores = {}
        for level, markers in self.health_literacy_markers.items():
            matches = sum(1 for marker in markers if marker in text)
            literacy_scores[level] = matches / max(len(markers) * 0.1, 1)

        quality_scores["health_literacy_level"] = max(
            literacy_scores, key=literacy_scores.get
        )
        quality_scores["literacy_score"] = max(literacy_scores.values())

        # Calculate overall quality score
        positive_score = np.mean(
            [
                quality_scores.get("quality_evidence_based", 0) * 0.3,
                quality_scores.get("quality_professional_source", 0) * 0.25,
                quality_scores.get("quality_resource_sharing", 0) * 0.2,
                quality_scores.get("quality_cautious_language", 0) * 0.15,
                quality_scores.get("quality_personal_experience", 0) * 0.1,
            ]
        )

        negative_score = np.mean(
            [
                quality_scores.get("concern_absolute_claims", 0),
                quality_scores.get("concern_anti_medical", 0),
                quality_scores.get("concern_fear_mongering", 0),
            ]
        )

        quality_scores["overall_quality"] = max(0, positive_score - negative_score)
        quality_scores["helpfulness_score"] = (
            quality_scores.get("quality_encouraging", 0) * 0.4
            + quality_scores.get("quality_personal_experience", 0) * 0.3
            + quality_scores.get("quality_resource_sharing", 0) * 0.3
        )

        return quality_scores

    def analyze_community_info_quality(self, subreddit: Optional[str] = None) -> Dict:
        """Analyze information quality patterns across communities"""
        with self.db_manager.get_session() as session:
            # Load posts
            posts_query = session.query(RedditPost)
            if subreddit:
                posts_query = posts_query.filter(RedditPost.subreddit == subreddit)

            posts = posts_query.filter(
                RedditPost.contains_health_keywords == True
            ).all()

            if not posts:
                return {"error": "No health-related posts found"}

            # Analyze each post
            quality_data = []
            community_stats = defaultdict(list)

            for post in posts:
                full_text = post.title + " " + (post.selftext or "")
                quality_scores = self.assess_post_quality(full_text)

                post_data = {
                    "post_id": post.post_id,
                    "subreddit": post.subreddit,
                    "author": post.author,
                    "score": post.score,
                    "language": post.language,
                    **quality_scores,
                }
                quality_data.append(post_data)

                # Aggregate by community
                community_stats[post.subreddit].append(
                    quality_scores["overall_quality"]
                )

            # Calculate community-level statistics
            community_quality = {}
            for community, scores in community_stats.items():
                community_quality[community] = {
                    "avg_quality": np.mean(scores),
                    "posts_analyzed": len(scores),
                    "high_quality_posts": sum(1 for s in scores if s > 0.7),
                    "medium_quality_posts": sum(1 for s in scores if 0.3 <= s <= 0.7),
                    "low_quality_posts": sum(1 for s in scores if s < 0.3),
                }

            return {
                "post_quality_data": quality_data,
                "community_quality": community_quality,
                "overall_stats": {
                    "total_posts": len(quality_data),
                    "avg_quality": np.mean(
                        [p["overall_quality"] for p in quality_data]
                    ),
                    "avg_helpfulness": np.mean(
                        [p["helpfulness_score"] for p in quality_data]
                    ),
                },
            }

    def identify_helpful_content_patterns(self) -> Dict:
        """Identify patterns in helpful health content"""
        analysis = self.analyze_community_info_quality()

        if "error" in analysis:
            return analysis

        quality_data = analysis["post_quality_data"]

        # Find high-quality posts
        high_quality_posts = [p for p in quality_data if p["overall_quality"] > 0.7]
        medium_quality_posts = [
            p for p in quality_data if 0.3 <= p["overall_quality"] <= 0.7
        ]

        patterns = {
            "high_quality_characteristics": {},
            "helpful_language_patterns": [],
            "quality_by_community": {},
            "recommended_practices": [],
        }

        if high_quality_posts:
            # Analyze high-quality post characteristics
            for category in self.quality_indicators.keys():
                avg_score = np.mean(
                    [p.get(f"quality_{category}", 0) for p in high_quality_posts]
                )
                patterns["high_quality_characteristics"][category] = avg_score

            # Community quality rankings
            community_quality_avg = defaultdict(list)
            for post in high_quality_posts:
                community_quality_avg[post["subreddit"]].append(post["overall_quality"])

            for community, scores in community_quality_avg.items():
                patterns["quality_by_community"][community] = {
                    "avg_quality": np.mean(scores),
                    "high_quality_posts": len(scores),
                }

        # Generate recommendations based on patterns
        if patterns["high_quality_characteristics"]:
            top_characteristics = sorted(
                patterns["high_quality_characteristics"].items(),
                key=lambda x: x[1],
                reverse=True,
            )[:3]

            for char, score in top_characteristics:
                if char == "evidence_based":
                    patterns["recommended_practices"].append(
                        "Share links to studies and research when discussing health topics"
                    )
                elif char == "professional_source":
                    patterns["recommended_practices"].append(
                        "Reference healthcare provider advice and clinical guidance"
                    )
                elif char == "resource_sharing":
                    patterns["recommended_practices"].append(
                        "Provide links to helpful resources, clinics, and support services"
                    )
                elif char == "cautious_language":
                    patterns["recommended_practices"].append(
                        "Use cautious language and recommend consulting healthcare providers"
                    )

        return patterns

    def generate_quality_improvement_suggestions(
        self, community: str = None
    ) -> List[str]:
        """Generate suggestions for improving health information quality"""
        patterns = self.identify_helpful_content_patterns()

        if "error" in patterns:
            return ["No data available for generating suggestions"]

        suggestions = []

        # General suggestions based on successful patterns
        if patterns["recommended_practices"]:
            suggestions.extend(
                ["🌟 **Successful Practices to Amplify:**"]
                + [f"• {practice}" for practice in patterns["recommended_practices"]]
            )

        # Community-specific suggestions
        if patterns["quality_by_community"] and community:
            if community in patterns["quality_by_community"]:
                community_data = patterns["quality_by_community"][community]
                suggestions.append(f"\n📊 **{community} Community Strengths:**")
                suggestions.append(
                    f"• Average quality score: {community_data['avg_quality']:.2f}"
                )
                suggestions.append(
                    f"• High-quality posts: {community_data['high_quality_posts']}"
                )
            else:
                suggestions.append(
                    f"• No high-quality posts identified in r/{community} yet"
                )

        # General improvement suggestions
        suggestions.extend(
            [
                "\n💡 **Community Enhancement Opportunities:**",
                "• Encourage members to share credible sources",
                "• Create pinned posts with trusted health resources",
                "• Highlight helpful community responses",
                "• Foster peer support and experience sharing",
                "• Promote cautious language around medical advice",
            ]
        )

        return suggestions
