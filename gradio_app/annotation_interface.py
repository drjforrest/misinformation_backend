"""
Gradio interface for human annotation of Reddit posts
Gamified design for research team engagement
"""

import os
import sqlite3
from datetime import datetime
from typing import Dict, Optional

import gradio as gr
from loguru import logger

from config.settings import AnnotationConfig, Config
from src.data_persistence import DataPersistenceManager
from src.database_models import RedditComment, RedditPost


class AnnotationInterface:
    """Gamified Gradio interface for post annotation"""

    def __init__(self, limit: int = 100, filter_criteria: Optional[Dict] = None):
        """
        Initialize annotation interface with database-driven data loading

        Args:
            limit: Maximum number of posts to load for annotation
            filter_criteria: Optional filters (e.g., {'subreddit': 'askgaybros', 'annotated': False})
        """
        self.limit = limit
        self.filter_criteria = filter_criteria or {}
        self.current_post_index = 0
        self.posts_data = []
        self.db_manager = DataPersistenceManager()

        # Load posts from database
        self.load_posts_from_database()

        self.annotation_db = "data/annotations.db"
        self.init_database()

        # User session tracking
        self.current_user = "default_user"
        self.session_stats = {"posts_reviewed": 0, "session_start": datetime.now()}

    def load_posts_from_database(self) -> None:
        """Load posts from PostgreSQL database for annotation"""
        try:
            with self.db_manager.get_session() as session:
                # Build query with filters
                query = session.query(RedditPost)

                # Apply filters
                if "subreddit" in self.filter_criteria:
                    query = query.filter(
                        RedditPost.subreddit == self.filter_criteria["subreddit"]
                    )

                if "language" in self.filter_criteria:
                    query = query.filter(
                        RedditPost.language == self.filter_criteria["language"]
                    )

                if "newcomer_related" in self.filter_criteria:
                    query = query.filter(
                        RedditPost.is_newcomer_related
                        == self.filter_criteria["newcomer_related"]
                    )

                # Order by creation date (newest first) and limit
                query = query.order_by(RedditPost.created_utc.desc()).limit(self.limit)

                posts = query.all()

                # Convert to dictionary format and load comments
                self.posts_data = []
                for post in posts:
                    post_dict = {
                        "post_id": post.post_id,
                        "subreddit": post.subreddit,
                        "title": post.title,
                        "selftext": post.selftext or "",
                        "author": post.author,
                        "created_utc": (
                            post.created_utc.isoformat() if post.created_utc else ""
                        ),
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "language": post.language,
                        "is_newcomer_related": post.is_newcomer_related,
                        "english_translation": getattr(
                            post, "english_translation", None
                        ),
                        "translation_backend": getattr(
                            post, "translation_backend", None
                        ),
                        "translation_confidence": getattr(
                            post, "translation_confidence", None
                        ),
                        "comments": [],
                    }

                    # Load associated comments
                    comments_query = (
                        session.query(RedditComment)
                        .filter(RedditComment.post_id == post.post_id)
                        .order_by(RedditComment.created_utc.asc())
                        .limit(10)
                    )  # Limit comments for performance

                    for comment in comments_query:
                        comment_dict = {
                            "comment_id": comment.comment_id,
                            "author": comment.author,
                            "body": comment.body,
                            "created_utc": (
                                comment.created_utc.isoformat()
                                if comment.created_utc
                                else ""
                            ),
                            "score": comment.score,
                        }
                        post_dict["comments"].append(comment_dict)

                    self.posts_data.append(post_dict)

                logger.info(
                    f"Loaded {len(self.posts_data)} posts from database for annotation"
                )

        except Exception as e:
            logger.error(f"Error loading posts from database: {e}")
            self.posts_data = []

    def init_database(self):
        """Initialize SQLite database for storing annotations"""
        os.makedirs("data", exist_ok=True)

        conn = sqlite3.connect(self.annotation_db)
        cursor = conn.cursor()

        # Create annotations table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                annotator TEXT,
                category TEXT,
                confidence INTEGER,
                timestamp TEXT,
                notes TEXT
            )
        """
        )

        # Create user stats table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_stats (
                annotator TEXT PRIMARY KEY,
                total_annotations INTEGER DEFAULT 0,
                accuracy_score REAL DEFAULT 0.0,
                last_active TEXT,
                achievements TEXT DEFAULT "[]"
            )
        """
        )

        conn.commit()
        conn.close()

    def get_current_post(self) -> Dict:
        """Get the current post for annotation"""
        if self.current_post_index >= len(self.posts_data):
            return {"error": "No more posts to annotate!"}

        return self.posts_data[self.current_post_index]

    def _format_language_info(self, post: Dict) -> str:
        """Format language and translation status information"""
        language = post.get("language", "unknown")
        language_display = f"**Language:** {language}"

        # Add language flag emoji if available
        lang_flags = {
            "en": "🇬🇧",
            "es": "🇪🇸",
            "fr": "🇫🇷",
            "zh": "🇨🇳",
            "zh-cn": "🇨🇳",
            "zh-tw": "🇹🇼",
            "tl": "🇵🇭",
            "pa": "🇮🇳",
        }
        if language in lang_flags:
            language_display = f"**Language:** {lang_flags[language]} {language}"

        # Show translation status if available
        if post.get("english_translation"):
            backend = post.get("translation_backend", "unknown")
            confidence = post.get("translation_confidence", 0)
            language_display += f" | **Translation:** ✅ ({backend}, {confidence:.2f})"
        elif language not in ["en", "unknown"]:
            language_display += " | **Translation:** ⚠️ Not available"

        return language_display

    def _format_translation_display(self, post: Dict) -> str:
        """Format translation content if available"""
        if post.get("english_translation") and post.get("language") not in [
            "en",
            "unknown",
        ]:
            return f"""
            **🌐 English Translation:**
            {post["english_translation"][:1000]}{"..." if len(post["english_translation"]) > 1000 else ""}
            
            *Translated using {post.get("translation_backend", "unknown")} (confidence: {post.get("translation_confidence", 0):.2f})*
            """
        return ""

    def get_public_health_context(self, post_text: str) -> str:
        """Generate relevant public health guideline context"""
        context_items = []

        post_lower = post_text.lower()

        if any(term in post_lower for term in ["prep", "truvada", "descovy"]):
            context_items.append(
                "**PrEP Guidelines (PHAC):** Pre-exposure prophylaxis is highly effective "
                "when taken daily. Consult healthcare provider for prescription and monitoring."
            )

        if any(term in post_lower for term in ["hiv", "viral load", "undetectable"]):
            context_items.append(
                "**HIV Facts (WHO):** Undetectable = Untransmittable (U=U). "
                "People with undetectable viral loads cannot transmit HIV sexually."
            )

        if any(
            term in post_lower
            for term in ["syphilis", "chlamydia", "gonorrhea", "gonorrhoea"]
        ):
            context_items.append(
                "**STI Treatment (CDC):** Most bacterial STIs are easily treatable with antibiotics. "
                "Regular testing is recommended for sexually active individuals."
            )

        if any(term in post_lower for term in ["doxy", "doxypep"]):
            context_items.append(
                "**Doxy-PEP (Recent Research):** Post-exposure doxycycline shows promise "
                "for preventing bacterial STIs. Consult healthcare provider for guidance."
            )

        return (
            "\n\n".join(context_items)
            if context_items
            else "No specific guidelines matched."
        )

    def save_annotation(self, category: str, confidence: int, notes: str = "") -> str:
        """Save annotation to database and update stats"""

        current_post = self.get_current_post()
        if "error" in current_post:
            return "Error: No post to annotate"

        # Save annotation
        conn = sqlite3.connect(self.annotation_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO annotations (post_id, annotator, category, confidence, timestamp, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                current_post["post_id"],
                self.current_user,
                category,
                confidence,
                datetime.now().isoformat(),
                notes,
            ),
        )

        # Update user stats
        cursor.execute(
            """
            INSERT OR REPLACE INTO user_stats (annotator, total_annotations, last_active)
            VALUES (?, 
                    COALESCE((SELECT total_annotations FROM user_stats WHERE annotator = ?), 0) + 1,
                    ?)
        """,
            (self.current_user, self.current_user, datetime.now().isoformat()),
        )

        conn.commit()
        conn.close()

        # Update session stats
        self.session_stats["posts_reviewed"] += 1

        # Move to next post
        self.current_post_index += 1

        return f"✅ Annotation saved! Post {self.session_stats['posts_reviewed']} completed."

    def get_user_stats(self) -> str:
        """Get current user statistics for gamification"""
        conn = sqlite3.connect(self.annotation_db)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT total_annotations FROM user_stats WHERE annotator = ?",
            (self.current_user,),
        )
        result = cursor.fetchone()
        total = result[0] if result else 0

        conn.close()

        session_time = datetime.now() - self.session_stats["session_start"]

        stats_text = f"""
        **📊 Your Progress:**
        - Session: {self.session_stats["posts_reviewed"]} posts reviewed
        - Total: {total} posts annotated
        - Session time: {str(session_time).split(".")[0]}
        - Progress: {self.current_post_index}/{len(self.posts_data)} posts
        """

        # Achievement badges
        if total >= 10:
            stats_text += "\n🏆 **Getting Started** - 10+ annotations!"
        if total >= 50:
            stats_text += "\n🌟 **Contributor** - 50+ annotations!"
        if total >= 100:
            stats_text += "\n💎 **Expert Annotator** - 100+ annotations!"

        return stats_text

    def create_interface(self):
        """Create the Gradio interface"""

        def display_post():
            """Display current post for annotation"""
            post = self.get_current_post()

            if "error" in post:
                return post["error"], "", "", ""

            # Format post display with language and translation indicators
            language_info = self._format_language_info(post)

            post_display = f"""
            **Subreddit:** r/{post["subreddit"]}
            **Title:** {post["title"]}
            **Author:** {post["author"]}
            **Date:** {post["created_utc"]}
            **Score:** {post["score"]} | **Comments:** {post["num_comments"]}
            {language_info}
            **Newcomer-related:** {post["is_newcomer_related"]}
            
            **Original Content:**
            {post["selftext"][:1000]}{"..." if len(post["selftext"]) > 1000 else ""}
            
            {self._format_translation_display(post)}
            """

            # Show some comments for context
            comments_display = ""
            if post.get("comments"):
                comments_display = "**Top Comments:**\n"
                for i, comment in enumerate(post["comments"][:3]):
                    comments_display += f"\n**{comment['author']}:** {comment['body'][:200]}{'...' if len(comment['body']) > 200 else ''}\n"

            # Get relevant public health context
            health_context = self.get_public_health_context(
                post["title"] + " " + post["selftext"]
            )

            return post_display, comments_display, health_context, self.get_user_stats()

        def submit_annotation(category, confidence, notes):
            """Handle annotation submission"""
            if not category:
                return "Please select a category!", self.get_user_stats()

            result = self.save_annotation(category, confidence, notes)

            # Refresh display for next post
            return result, self.get_user_stats()

        def next_post():
            """Move to next post without annotating"""
            self.current_post_index += 1
            return display_post()

        # Create the Gradio interface
        with gr.Blocks(
            title="Health Misinformation Annotation Tool", theme=gr.themes.Soft()
        ) as iface:
            gr.Markdown("# 🏥 Health Misinformation Annotation Tool")
            gr.Markdown(
                "Help us identify and combat health misinformation in online communities!"
            )

            with gr.Row():
                with gr.Column(scale=2):
                    post_display = gr.Textbox(
                        label="📝 Post Content", lines=10, interactive=False
                    )

                    comments_display = gr.Textbox(
                        label="💬 Comments Context", lines=5, interactive=False
                    )

                with gr.Column(scale=1):
                    stats_display = gr.Markdown(
                        value=self.get_user_stats(), label="Your Progress"
                    )

                    health_context = gr.Textbox(
                        label="🩺 Public Health Guidelines", lines=6, interactive=False
                    )

            gr.Markdown("---")

            with gr.Row():
                with gr.Column():
                    gr.Markdown("### 🎯 Annotation")

                    category = gr.Radio(
                        choices=AnnotationConfig.ANNOTATION_CATEGORIES,
                        label="Content Category",
                        value=None,
                    )

                    confidence = gr.Slider(
                        minimum=1,
                        maximum=5,
                        step=1,
                        label="Confidence Level (1=Low, 5=High)",
                        value=3,
                    )

                    notes = gr.Textbox(
                        label="Notes (Optional)",
                        placeholder="Any additional context or reasoning...",
                        lines=2,
                    )

                    with gr.Row():
                        submit_btn = gr.Button(
                            "✅ Submit Annotation", variant="primary"
                        )
                        skip_btn = gr.Button("⏭️ Skip Post", variant="secondary")

            status_message = gr.Textbox(label="Status", interactive=False)

            # Event handlers
            submit_btn.click(
                fn=submit_annotation,
                inputs=[category, confidence, notes],
                outputs=[status_message, stats_display],
            ).then(
                fn=display_post,
                outputs=[post_display, comments_display, health_context, stats_display],
            )

            skip_btn.click(
                fn=next_post,
                outputs=[post_display, comments_display, health_context, stats_display],
            )

            # Load initial post
            iface.load(
                fn=display_post,
                outputs=[post_display, comments_display, health_context, stats_display],
            )

        return iface

    def launch(self, share: bool = False):
        """Launch the Gradio interface"""
        iface = self.create_interface()
        iface.launch(
            share=share,
            server_port=Config.GRADIO_PORT,
            server_name="0.0.0.0" if share else "127.0.0.1",
        )


if __name__ == "__main__":
    # Example usage with database-driven loading
    # Load 50 posts from askgaybros subreddit
    filter_criteria = {"subreddit": "askgaybros"}
    annotation_tool = AnnotationInterface(limit=50, filter_criteria=filter_criteria)
    annotation_tool.launch(share=False)
    annotation_tool = AnnotationInterface(limit=50, filter_criteria=filter_criteria)
    annotation_tool.launch(share=False)
