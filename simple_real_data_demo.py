"""
Simplified Real Data Visualization - Direct from raw data
"""

import json
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter


class SimpleRealDataDemo:
    def __init__(self):
        # Load raw data directly
        with open(
            "/Users/drjforrest/dev/academicdev/misinformation_gay_mens_Health/data/raw_reddit_data_20250902_060559.json",
            "r",
        ) as f:
            self.raw_data = json.load(f)

        print(f"Loaded {len(self.raw_data)} real posts from Reddit")

        # Extract comments
        all_comments = []
        for post in self.raw_data:
            for comment in post.get("comments", []):
                comment["post_subreddit"] = post["subreddit"]
                all_comments.append(comment)

        print(f"Extracted {len(all_comments)} real comments")

        # Basic stats
        unique_authors = set()
        languages = set()

        for post in self.raw_data:
            if post.get("author"):
                unique_authors.add(post["author"])
            if post.get("language"):
                languages.add(post["language"])

        for comment in all_comments:
            if comment.get("author"):
                unique_authors.add(comment["author"])
            if comment.get("language"):
                languages.add(comment["language"])

        self.stats = {
            "total_posts": len(self.raw_data),
            "total_comments": len(all_comments),
            "unique_authors": len(unique_authors),
            "languages": languages,
        }

        print(
            f"Stats: {self.stats['total_posts']} posts, {self.stats['total_comments']} comments, {self.stats['unique_authors']} authors, {len(self.stats['languages'])} languages"
        )

    def analyze_health_keywords(self):
        """Extract health keyword patterns from real data"""
        health_keywords = {
            "PrEP": ["prep", "truvada", "descovy", "pre-exposure"],
            "HIV": ["hiv", "positive", "negative", "undetectable"],
            "STI": ["sti", "std", "gonorrhea", "chlamydia", "syphilis", "herpes"],
            "Testing": ["test", "testing", "clinic", "result"],
            "Treatment": ["doxy", "pep", "medication", "treatment", "doctor"],
            "Mental_Health": ["anxiety", "depression", "stress", "mental health"],
        }

        keyword_counts = {category: 0 for category in health_keywords}
        posts_with_health = 0

        for post in self.raw_data:
            full_text = (post.get("title", "") + " " + post.get("selftext", "")).lower()
            has_health_content = False

            for category, keywords in health_keywords.items():
                for keyword in keywords:
                    if keyword in full_text:
                        keyword_counts[category] += 1
                        has_health_content = True

            # Check comments too
            for comment in post.get("comments", []):
                comment_text = comment.get("body", "").lower()
                for category, keywords in health_keywords.items():
                    for keyword in keywords:
                        if keyword in comment_text:
                            keyword_counts[category] += 1
                            has_health_content = True

            if has_health_content:
                posts_with_health += 1

        return keyword_counts, posts_with_health

    def analyze_languages(self):
        """Analyze language diversity"""
        comment_languages = Counter()

        for post in self.raw_data:
            for comment in post.get("comments", []):
                lang = comment.get("language", "unknown")
                comment_languages[lang] += 1

        return comment_languages

    def create_research_overview_simple(self):
        """Create overview using real data"""
        keyword_counts, posts_with_health = self.analyze_health_keywords()
        comment_languages = self.analyze_languages()

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Dataset Overview",
                "Health Topic Distribution",
                "Language Diversity",
                "Community Engagement",
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "pie"}, {"type": "bar"}],
            ],
        )

        # Dataset metrics
        metrics = ["Posts", "Comments", "Authors", "Languages"]
        values = [
            self.stats["total_posts"],
            self.stats["total_comments"],
            self.stats["unique_authors"],
            len(self.stats["languages"]),
        ]

        fig.add_trace(
            go.Bar(
                x=metrics,
                y=values,
                marker_color=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"],
                text=values,
                textposition="auto",
            ),
            row=1,
            col=1,
        )

        # Health topics
        fig.add_trace(
            go.Bar(
                x=list(keyword_counts.keys()),
                y=list(keyword_counts.values()),
                marker_color="#FFA07A",
            ),
            row=1,
            col=2,
        )

        # Top languages
        top_languages = comment_languages.most_common(8)
        if top_languages:
            fig.add_trace(
                go.Pie(
                    labels=[lang[0] for lang in top_languages],
                    values=[lang[1] for lang in top_languages],
                ),
                row=2,
                col=1,
            )

        # Engagement patterns - posts by subreddit
        subreddit_counts = Counter(post["subreddit"] for post in self.raw_data)
        top_subreddits = subreddit_counts.most_common(6)

        fig.add_trace(
            go.Bar(
                x=[sub[0] for sub in top_subreddits],
                y=[sub[1] for sub in top_subreddits],
                marker_color="#96CEB4",
            ),
            row=2,
            col=2,
        )

        fig.update_layout(
            height=800,
            title_text="REAL DATA: Rich Health Information Ecosystem",
            title_x=0.5,
            showlegend=False,
        )

        # Rotate x-axis labels
        fig.update_xaxes(tickangle=45, row=2, col=2)

        return fig

    def create_information_seeking_analysis(self):
        """Analyze real information seeking patterns"""
        seeking_patterns = {
            "questions": 0,
            "advice_requests": 0,
            "experience_sharing": 0,
            "medical_concerns": 0,
        }

        question_words = [
            "?",
            "how",
            "what",
            "should i",
            "help",
            "advice",
            "anyone else",
        ]
        experience_words = ["my experience", "happened to me", "i have", "i had"]
        medical_words = ["doctor", "clinic", "medical", "symptom", "side effect"]

        post_analysis = []

        for post in self.raw_data:
            title = post.get("title", "").lower()
            text = post.get("selftext", "").lower()
            full_text = title + " " + text

            # Categorize post type
            is_question = any(word in full_text for word in question_words)
            is_experience = any(word in full_text for word in experience_words)
            is_medical = any(word in full_text for word in medical_words)

            num_comments = len(post.get("comments", []))

            post_analysis.append(
                {
                    "title": post.get("title", "")[:50] + "...",
                    "is_question": is_question,
                    "is_experience": is_experience,
                    "is_medical": is_medical,
                    "num_comments": num_comments,
                    "score": post.get("score", 0),
                    "subreddit": post.get("subreddit", ""),
                }
            )

            if is_question:
                seeking_patterns["questions"] += 1
            if is_experience:
                seeking_patterns["experience_sharing"] += 1
            if is_medical:
                seeking_patterns["medical_concerns"] += 1

        return seeking_patterns, post_analysis

    def create_community_support_viz(self):
        """Show community support patterns"""
        seeking_patterns, post_analysis = self.create_information_seeking_analysis()

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Information seeking types
        categories = list(seeking_patterns.keys())
        values = list(seeking_patterns.values())
        colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]

        axes[0, 0].bar(categories, values, color=colors)
        axes[0, 0].set_title("Information Seeking Patterns in Real Data")
        axes[0, 0].tick_params(axis="x", rotation=45)

        # Response patterns
        response_data = [(p["num_comments"], p["score"]) for p in post_analysis]
        comments = [r[0] for r in response_data]
        scores = [r[1] for r in response_data]

        axes[0, 1].scatter(comments, scores, alpha=0.6, color="coral")
        axes[0, 1].set_xlabel("Number of Comments")
        axes[0, 1].set_ylabel("Post Score")
        axes[0, 1].set_title("Community Engagement Patterns")

        # Questions vs responses
        questions = [p for p in post_analysis if p["is_question"]]
        if questions:
            question_responses = [q["num_comments"] for q in questions]
            axes[1, 0].hist(question_responses, bins=15, alpha=0.7, color="lightblue")
            axes[1, 0].set_title("Response Rate to Health Questions")
            axes[1, 0].set_xlabel("Number of Responses")

        # Medical concerns by subreddit
        medical_posts = [p for p in post_analysis if p["is_medical"]]
        if medical_posts:
            medical_subs = Counter(p["subreddit"] for p in medical_posts)
            top_medical = medical_subs.most_common(6)

            axes[1, 1].bar(
                [s[0] for s in top_medical],
                [s[1] for s in top_medical],
                color="lightgreen",
            )
            axes[1, 1].set_title("Medical Concerns by Community")
            axes[1, 1].tick_params(axis="x", rotation=45)

        plt.tight_layout()
        return fig

    def generate_pitch_summary(self):
        """Generate compelling summary for colleagues"""
        keyword_counts, posts_with_health = self.analyze_health_keywords()
        comment_languages = self.analyze_languages()
        seeking_patterns, _ = self.create_information_seeking_analysis()

        return f"""
REAL DATA RESEARCH PITCH - YOUR ACTUAL DATASET
==============================================

🎯 DATASET SUMMARY:
• {self.stats['total_posts']} authentic Reddit posts
• {self.stats['total_comments']:,} real community comments  
• {self.stats['unique_authors']:,} unique community members
• {len(self.stats['languages'])} languages detected in discussions

🏥 HEALTH CONTENT RICHNESS:
• {posts_with_health}/{self.stats['total_posts']} posts contain health content ({posts_with_health/self.stats['total_posts']*100:.1f}%)

Top Health Discussion Areas:
• PrEP discussions: {keyword_counts['PrEP']} mentions
• HIV-related content: {keyword_counts['HIV']} mentions  
• STI discussions: {keyword_counts['STI']} mentions
• Testing conversations: {keyword_counts['Testing']} mentions
• Treatment discussions: {keyword_counts['Treatment']} mentions
• Mental health: {keyword_counts['Mental_Health']} mentions

🌍 MULTILINGUAL COMMUNITY:
Most Active Languages:
{chr(10).join([f"• {lang}: {count} comments" for lang, count in comment_languages.most_common(5)])}

💬 COMMUNITY BEHAVIOR PATTERNS:
• {seeking_patterns['questions']} posts asking health questions
• {seeking_patterns['experience_sharing']} posts sharing personal experiences
• {seeking_patterns['medical_concerns']} posts with medical concerns

🔬 RESEARCH QUESTIONS YOUR DATA CAN ANSWER:

1. **Digital Health Equity**: How do multilingual communities navigate health information?
2. **Community Expertise**: Who provides trusted health advice in these spaces?
3. **Information Gaps**: What health topics generate most questions/uncertainty?
4. **Peer Support Networks**: How do community members support each other's health journeys?
5. **Cultural Health Narratives**: How do different language communities discuss the same health topics?

💡 PIVOT RECOMMENDATIONS:

Instead of "misinformation detection," focus on:

**"Multilingual Health Information Ecosystems in Digital Gay Men's Communities"**
- Community-driven health expertise identification
- Cross-cultural health narrative analysis  
- Peer support network mapping
- Information gap identification for public health intervention

**"Digital Health Equity in LGBTQ+ Communities: A Social Network Analysis"**
- Language barriers in health information access
- Community health champion identification
- Optimal intervention points for health education

🎯 IMMEDIATE VALUE:
✅ Ethics-approved data collection already running
✅ Rich multilingual dataset demonstrating global reach
✅ Clear community health priorities emerging from real discussions
✅ Technical infrastructure ready for expanded analysis
✅ Direct community impact potential through gap identification

This data represents authentic, community-driven health discussions across 
multiple languages - a unique research opportunity that goes far beyond 
simple misinformation detection to understand how health information 
actually flows in digital LGBTQ+ communities.
"""


def create_all_research_visuals():
    """Generate research pitch materials"""
    demo = SimpleRealDataDemo()

    print("Creating research overview...")
    overview = demo.create_research_overview_simple()
    overview.write_html("REAL_DATA_research_overview.html")

    print("Creating community support analysis...")
    support_fig = demo.create_community_support_viz()
    support_fig.savefig(
        "REAL_DATA_community_patterns.png", dpi=300, bbox_inches="tight"
    )

    print("Generating pitch summary...")
    summary = demo.generate_pitch_summary()
    with open("REAL_DATA_pitch_summary.txt", "w") as f:
        f.write(summary)

    print("\n" + "=" * 60)
    print("RESEARCH PITCH MATERIALS CREATED!")
    print("=" * 60)
    print("Files generated from YOUR REAL DATA:")
    print("• REAL_DATA_research_overview.html - Interactive dashboard")
    print("• REAL_DATA_community_patterns.png - Community analysis")
    print("• REAL_DATA_pitch_summary.txt - Executive summary")
    print("\nThis demonstrates the rich research potential of your actual dataset!")


if __name__ == "__main__":
    create_all_research_visuals()
