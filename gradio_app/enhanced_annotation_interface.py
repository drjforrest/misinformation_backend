"""
Enhanced Gradio interface for human annotation of Reddit posts
Supports the full enhanced schema including severity analysis, language communities, and intervention planning
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, Optional

import gradio as gr
from loguru import logger

from config.settings import Config
from src.data_persistence import DataPersistenceManager
from src.database_models import RedditComment, RedditPost
from src.research_expertise_tracker import ResearchExpertiseTracker


class EnhancedAnnotationInterface:
    """Enhanced Gradio interface supporting full schema capabilities"""

    def __init__(self, limit: int = 100, filter_criteria: Optional[Dict] = None):
        """
        Initialize enhanced annotation interface with database-driven data loading

        Args:
            limit: Maximum number of posts to load for annotation
            filter_criteria: Optional filters (e.g., {'subreddit': 'askgaybros', 'language': 'tl'})
        """
        self.limit = limit
        self.filter_criteria = filter_criteria or {}
        self.current_post_index = 0
        self.posts_data = []
        self.db_manager = DataPersistenceManager()
        self.expertise_tracker = ResearchExpertiseTracker()

        # Load posts from database
        self.load_posts_from_database()

        self.annotation_db = "data/enhanced_annotations.db"
        self.init_enhanced_database()

        # User session tracking - now researcher-focused
        self.current_user = "default_researcher"
        self.session_stats = {
            "analyses_completed": 0,
            "session_start": datetime.now(),
            "expertise_gained": [],
        }

    def load_posts_from_database(self) -> None:
        """Load posts from PostgreSQL database for enhanced annotation"""
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
                    f"Loaded {len(self.posts_data)} posts from database for enhanced annotation"
                )

        except Exception as e:
            logger.error(f"Error loading posts from database: {e}")
            self.posts_data = []

    def init_enhanced_database(self):
        """Initialize SQLite database with enhanced schema support"""
        os.makedirs("data", exist_ok=True)

        conn = sqlite3.connect(self.annotation_db)
        cursor = conn.cursor()

        # Enhanced annotations table matching new schema
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS enhanced_annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id TEXT,
                annotator TEXT,
                
                -- Basic annotation
                category TEXT,
                confidence INTEGER,
                notes TEXT,
                timestamp TEXT,
                
                -- Enhanced severity classification
                severity_level INTEGER,
                misinformation_type TEXT,
                target_community TEXT,
                intervention_priority TEXT,
                
                -- Detailed severity analysis
                harm_potential TEXT,
                urgency_score INTEGER,
                health_topic TEXT,
                target_population TEXT,
                suggested_response TEXT,
                resource_needed TEXT,
                
                -- Language community analysis
                detected_languages TEXT,
                code_switching_detected BOOLEAN,
                cultural_references TEXT,
                translation_needed BOOLEAN
            )
        """
        )

        # Enhanced user stats table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS enhanced_user_stats (
                annotator TEXT PRIMARY KEY,
                total_annotations INTEGER DEFAULT 0,
                accuracy_score REAL DEFAULT 0.0,
                last_active TEXT,
                achievements TEXT DEFAULT "[]",
                
                -- Community expertise enhancements
                community_expertise TEXT DEFAULT "[]",
                language_communities TEXT DEFAULT "[]",
                cultural_competency_score REAL DEFAULT 0.0,
                
                -- Specialization tracking
                health_topic_expertise TEXT DEFAULT "[]",
                annotation_quality_score REAL DEFAULT 0.0
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

    def analyze_language_patterns(self, text: str) -> Dict:
        """Analyze language patterns in the text"""
        patterns = {
            "detected_languages": [],
            "code_switching_indicators": [],
            "cultural_references": [],
            "translation_indicators": [],
        }

        text_lower = text.lower()

        # Simple language pattern detection (you could enhance this with proper NLP)
        if any(phrase in text_lower for phrase in ["kumusta", "salamat", "po"]):
            patterns["detected_languages"].append("Tagalog")
        if any(phrase in text_lower for phrase in ["你好", "谢谢", "ni hao"]):
            patterns["detected_languages"].append("Chinese")
        if any(phrase in text_lower for phrase in ["sat sri akal", "punjabi"]):
            patterns["detected_languages"].append("Punjabi")
        if any(phrase in text_lower for phrase in ["gracias", "hola", "por favor"]):
            patterns["detected_languages"].append("Spanish")

        # Code-switching indicators
        if len(patterns["detected_languages"]) > 0:
            patterns["code_switching_indicators"].append(
                "Mixed language usage detected"
            )

        # Cultural health references
        cultural_terms = [
            "traditional medicine",
            "herbal",
            "home remedy",
            "cultural practice",
            "back home",
            "in my country",
            "family tradition",
        ]
        for term in cultural_terms:
            if term in text_lower:
                patterns["cultural_references"].append(term)

        return patterns

    def get_enhanced_public_health_context(self, post_text: str) -> str:
        """Generate comprehensive public health guideline context"""
        context_items = []

        post_lower = post_text.lower()

        # Existing health context (enhanced)
        if any(term in post_lower for term in ["prep", "truvada", "descovy"]):
            context_items.append(
                "🔷 **PrEP Guidelines (PHAC):** Pre-exposure prophylaxis is highly effective "
                "when taken daily. Available through provincial health programs. "
                "Severity: LOW for accurate info, HIGH for dosage misinformation."
            )

        if any(term in post_lower for term in ["hiv", "viral load", "undetectable"]):
            context_items.append(
                "🔷 **HIV Facts (WHO):** Undetectable = Untransmittable (U=U). "
                "Modern treatment allows normal life expectancy. "
                "Severity: CRITICAL for stigma/transmission misinformation."
            )

        if any(
            term in post_lower
            for term in ["syphilis", "chlamydia", "gonorrhea", "gonorrhoea"]
        ):
            context_items.append(
                "🔷 **STI Treatment (CDC):** Most bacterial STIs are curable with antibiotics. "
                "Regular testing prevents complications. "
                "Severity: MEDIUM for treatment delays, HIGH for cure denial."
            )

        # Newcomer-specific context
        if any(
            term in post_lower
            for term in ["ohip", "health card", "walk-in", "without insurance"]
        ):
            context_items.append(
                "🍁 **Canadian Healthcare Access:** OHIP covers STI testing and treatment. "
                "Walk-in clinics accept uninsured patients. Community health centers available. "
                "Target: Newcomer communities."
            )

        # Cultural sensitivity context
        if any(
            term in post_lower
            for term in ["traditional", "herbal", "cultural", "family"]
        ):
            context_items.append(
                "🌍 **Cultural Considerations:** Respect traditional practices while providing "
                "evidence-based medical information. Consider language barriers and cultural stigma. "
                "Intervention: Cultural competency required."
            )

        return (
            "\n\n".join(context_items)
            if context_items
            else "No specific guidelines matched."
        )

    def save_enhanced_annotation(
        self,
        category: str,
        confidence: int,
        notes: str = "",
        severity_level: int = 1,
        misinformation_type: str = "",
        target_community: str = "",
        intervention_priority: str = "low",
        harm_potential: str = "low",
        urgency_score: int = 1,
        health_topic: str = "",
        target_population: str = "",
        suggested_response: str = "",
        resource_needed: str = "",
    ) -> str:
        """Save enhanced annotation with all new schema fields"""

        current_post = self.get_current_post()
        if "error" in current_post:
            return "Error: No post to annotate"

        # Analyze language patterns
        full_text = current_post["title"] + " " + current_post["selftext"]
        lang_analysis = self.analyze_language_patterns(full_text)

        # Save enhanced annotation
        conn = sqlite3.connect(self.annotation_db)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO enhanced_annotations (
                post_id, annotator, category, confidence, notes, timestamp,
                severity_level, misinformation_type, target_community, intervention_priority,
                harm_potential, urgency_score, health_topic, target_population,
                suggested_response, resource_needed,
                detected_languages, code_switching_detected, cultural_references, translation_needed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                current_post["post_id"],
                self.current_user,
                category,
                confidence,
                notes,
                datetime.now().isoformat(),
                severity_level,
                misinformation_type,
                target_community,
                intervention_priority,
                harm_potential,
                urgency_score,
                health_topic,
                target_population,
                suggested_response,
                resource_needed,
                json.dumps(lang_analysis["detected_languages"]),
                len(lang_analysis["code_switching_indicators"]) > 0,
                json.dumps(lang_analysis["cultural_references"]),
                "translation" in notes.lower(),
            ),
        )

        # Update enhanced user stats
        cursor.execute(
            """
            INSERT OR REPLACE INTO enhanced_user_stats (
                annotator, total_annotations, last_active, cultural_competency_score
            ) VALUES (?, 
                    COALESCE((SELECT total_annotations FROM enhanced_user_stats WHERE annotator = ?), 0) + 1,
                    ?, ?)
        """,
            (
                self.current_user,
                self.current_user,
                datetime.now().isoformat(),
                self.calculate_cultural_competency(lang_analysis),
            ),
        )

        conn.commit()
        conn.close()

        # Update session stats
        self.session_stats["posts_reviewed"] += 1
        self.current_post_index += 1

        return f"✅ Enhanced annotation saved! Post {self.session_stats['posts_reviewed']} completed."

    def calculate_cultural_competency(self, lang_analysis: Dict) -> float:
        """Calculate cultural competency score based on language analysis"""
        score = 0.0
        if lang_analysis["detected_languages"]:
            score += 0.3
        if lang_analysis["cultural_references"]:
            score += 0.4
        if lang_analysis["code_switching_indicators"]:
            score += 0.3
        return min(score, 1.0)

    def get_research_profile_stats(self) -> str:
        """Get researcher expertise profile and development progress"""
        # Get researcher profile from expertise tracker
        profile = self.expertise_tracker.get_researcher_profile(self.current_user)

        if "error" in profile:
            # Initialize new researcher
            total_analyses = 0
            expertise_summary = "New researcher - building expertise profile"
            strengths = []
            developing_areas = []
        else:
            total_analyses = len(profile.get("recent_activities", []))
            expertise_summary = profile.get("expertise_summary", "")
            strengths = profile.get("strengths", [])
            developing_areas = profile.get("developing_areas", [])

        session_time = datetime.now() - self.session_stats["session_start"]

        # Map domain keys to readable names
        def get_domain_name(domain_key):
            return self.expertise_tracker.expertise_domains.get(domain_key, {}).get(
                "name", domain_key
            )

        stats_text = f"""
**🔬 Research Profile:**
- Session: {self.session_stats["analyses_completed"]} analyses completed
- Total Analyses: {total_analyses}
- Session time: {str(session_time).split(".")[0]}
- Progress: {self.current_post_index}/{len(self.posts_data)} posts

**🌟 Expertise Summary:**
{expertise_summary}
"""

        # Show expertise areas
        if strengths:
            stats_text += "\n**💎 Research Strengths:**\n"
            for domain in strengths[:3]:  # Show top 3
                stats_text += f"• {get_domain_name(domain)}\n"

        if developing_areas:
            stats_text += "\n**📈 Developing Expertise:**\n"
            for domain in developing_areas[:3]:  # Show top 3
                stats_text += f"• {get_domain_name(domain)}\n"

        # Session expertise gained
        if self.session_stats["expertise_gained"]:
            stats_text += "\n**🎯 This Session:**\n"
            for domain in set(self.session_stats["expertise_gained"]):
                stats_text += f"• Practiced {get_domain_name(domain)}\n"

        # Research achievement badges
        if total_analyses >= 5:
            stats_text += "\n🏆 **Emerging Researcher** - 5+ analyses!"
        if total_analyses >= 20:
            stats_text += "\n🌟 **Active Researcher** - 20+ analyses!"
        if total_analyses >= 50:
            stats_text += "\n💎 **Expert Researcher** - 50+ analyses!"
        if len(strengths) >= 2:
            stats_text += "\n🎓 **Multi-domain Expert** - Proficient in multiple areas!"

        return stats_text

    def track_research_activity(
        self,
        analysis_type: str,
        quality_score: float = 0.7,
        community_focus: str = "",
        description: str = "",
    ):
        """Track research activity for expertise development"""
        # Map analysis types to expertise domains
        domain_mapping = {
            "peer_support_analysis": "peer_support_analysis",
            "knowledge_broker_identification": "knowledge_broker_identification",
            "cultural_adaptation": "cultural_bridging_analysis",
            "health_info_quality": "health_info_quality",
            "network_analysis": "network_analysis",
            "community_engagement": "community_engagement",
            "qualitative_analysis": "qualitative_analysis",
        }

        expertise_domain = domain_mapping.get(analysis_type, "qualitative_analysis")

        # Track the activity
        self.expertise_tracker.track_research_activity(
            researcher_id=self.current_user,
            activity_type="analysis_completed",
            expertise_domain=expertise_domain,
            description=description,
            quality_score=quality_score,
            community_focus=community_focus,
        )

        # Update session stats
        self.session_stats["analyses_completed"] += 1
        self.session_stats["expertise_gained"].append(expertise_domain)

    def get_research_recommendations(self) -> str:
        """Get personalized research focus recommendations"""
        recommendations = self.expertise_tracker.recommend_research_focus(
            self.current_user
        )

        if "error" in recommendations:
            return """
**🎯 Research Focus Recommendations:**

*Complete a few analyses to get personalized recommendations!*

**Suggested Starting Areas:**
• **Peer Support Analysis** - Identify mutual aid patterns in community posts
• **Cultural Adaptation Research** - Study how health info gets adapted across cultures  
• **Health Information Quality** - Assess helpfulness of community-shared health advice
"""

        rec_text = "**🎯 Research Focus Recommendations:**\n\n"

        # Continue developing areas
        if recommendations["continue_developing"]:
            rec_text += "**📈 Continue Building Expertise:**\n"
            for area in recommendations["continue_developing"]:
                rec_text += (
                    f"• **{area['name']}** - Currently {area['current_level']}\n"
                )
                rec_text += f"  {area['next_steps']}\n"

        # New areas to explore
        if recommendations["new_areas"]:
            rec_text += "\n**🌟 Explore New Areas:**\n"
            for area in recommendations["new_areas"][:3]:  # Top 3
                rec_text += f"• **{area['name']}** - {area['description']}\n"
                rec_text += f"  {area['rationale']}\n"

        # Specialization opportunities
        if recommendations["specialization_paths"]:
            rec_text += "\n**💎 Lead Research Opportunities:**\n"
            for path in recommendations["specialization_paths"]:
                rec_text += f"• {path}\n"

        return rec_text

    def generate_classification_suggestions(self, post, lang_analysis):
        """Generate intelligent classification suggestions"""
        suggestions = "**🤖 AI Suggestions:**\n"

        text = (post["title"] + " " + post["selftext"]).lower()

        # Severity suggestions
        if any(term in text for term in ["cure", "miracle", "dangerous", "deadly"]):
            suggestions += "- High severity potential detected\n"
        if any(term in text for term in ["undetectable", "prep", "treatment"]):
            suggestions += "- Medical accuracy critical\n"

        # Community targeting
        if lang_analysis["detected_languages"]:
            suggestions += f"- Target community: {', '.join(lang_analysis['detected_languages'])}\n"
        if post["is_newcomer_related"]:
            suggestions += "- Newcomer-focused intervention needed\n"

        # Intervention type
        if "question" in text or "?" in post["title"]:
            suggestions += "- Suggested response: Educational resource\n"
        else:
            suggestions += "- Suggested response: Fact-check\n"

        return suggestions

    def create_enhanced_interface(self):
        """Create the enhanced Gradio interface with full schema support"""

        def display_enhanced_post():
            """Display current post with enhanced analysis"""
            post = self.get_current_post()

            if "error" in post:
                return post["error"], "", "", "", self.get_research_profile_stats()

            # Enhanced post display with language analysis
            lang_analysis = self.analyze_language_patterns(
                post["title"] + " " + post["selftext"]
            )

            # Format language flags for better visual appeal
            lang_flags = {
                "en": "🇺🇸",
                "tl": "🇵🇭",
                "zh-CN": "🇨🇳",
                "zh-TW": "🇹🇼",
                "pa": "🇮🇳",
                "es": "🇪🇸",
                "fr": "🇫🇷",
            }
            lang_flag = lang_flags.get(post["language"], "🌐")

            post_display = f"""
## 📋 Post Information
**Subreddit:** r/{post["subreddit"]} | **Language:** {lang_flag} {post["language"]} | **Newcomer-related:** {"✅" if post["is_newcomer_related"] else "❌"}

### 📝 Title
**{post["title"]}**

### 👤 Metadata
- **Author:** {post["author"]}
- **Date:** {post["created_utc"][:10] if post["created_utc"] else "Unknown"}
- **Score:** {post["score"]} | **Comments:** {post["num_comments"]}

### 🔍 Language Analysis
- **Detected Languages:** {", ".join(lang_analysis["detected_languages"]) if lang_analysis["detected_languages"] else "English only"}
- **Code-switching:** {"✅ Yes" if lang_analysis["code_switching_indicators"] else "❌ No"}
- **Cultural References:** {", ".join(lang_analysis["cultural_references"][:3]) if lang_analysis["cultural_references"] else "None detected"}

### 📄 Content
{post["selftext"][:1200]}{"..." if len(post["selftext"]) > 1200 else ""}
            """

            # Enhanced comments display with better formatting
            comments_display = ""
            if post.get("comments"):
                comments_display = "## 💬 Comment Context\n\n"
                for i, comment in enumerate(post["comments"][:3]):
                    comment_lang = self.analyze_language_patterns(comment["body"])
                    lang_tags = (
                        comment_lang["detected_languages"]
                        if comment_lang["detected_languages"]
                        else ["EN"]
                    )
                    lang_badges = " ".join([f"`{lang}`" for lang in lang_tags])

                    comments_display += f"### 👤 {comment['author']} {lang_badges}\n"
                    comments_display += f"{comment['body'][:150]}{'...' if len(comment['body']) > 150 else ''}\n\n"

            # Enhanced health context
            health_context = self.get_enhanced_public_health_context(
                post["title"] + " " + post["selftext"]
            )

            # Suggested classification based on analysis
            suggestions = self.generate_classification_suggestions(post, lang_analysis)

            return (
                post_display,
                comments_display,
                health_context,
                suggestions,
                self.get_research_profile_stats(),
            )

        def submit_enhanced_annotation(
            category,
            confidence,
            notes,
            severity_level,
            misinformation_type,
            target_community,
            intervention_priority,
            harm_potential,
            urgency_score,
            health_topic,
            target_population,
            suggested_response,
            resource_needed,
        ):
            """Handle enhanced research analysis submission"""
            if not category:
                return "Please select a category!", self.get_research_profile_stats()

            # Determine analysis type for expertise tracking
            analysis_type = "qualitative_analysis"  # default
            community_focus = target_community or ""

            if "support" in category.lower() or "helpful" in category.lower():
                analysis_type = "peer_support_analysis"
            elif "cultural" in notes.lower() or "bridge" in notes.lower():
                analysis_type = "cultural_adaptation"
            elif "quality" in notes.lower() or "accurate" in category.lower():
                analysis_type = "health_info_quality"
            elif "network" in notes.lower() or "community" in notes.lower():
                analysis_type = "network_analysis"

            # Calculate quality score based on completeness and confidence
            quality_score = (confidence + (1.0 if notes.strip() else 0.5)) / 2
            if severity_level > 0:
                quality_score += 0.1
            if health_topic.strip():
                quality_score += 0.1
            quality_score = min(quality_score, 1.0)

            # Track research activity for expertise development
            self.track_research_activity(
                analysis_type=analysis_type,
                quality_score=quality_score,
                community_focus=community_focus,
                description=f"Analyzed {category} post in r/{self.get_current_post().get('subreddit', 'unknown')}",
            )

            result = self.save_enhanced_annotation(
                category,
                confidence,
                notes,
                severity_level,
                misinformation_type,
                target_community,
                intervention_priority,
                harm_potential,
                urgency_score,
                health_topic,
                target_population,
                suggested_response,
                resource_needed,
            )

            return result, self.get_research_profile_stats()

        def next_post():
            """Move to next post without annotating"""
            self.current_post_index += 1
            return display_enhanced_post()

        # Create the enhanced Gradio interface
        with gr.Blocks(
            title="Community Resilience Research Interface",
            theme=gr.themes.Soft(),
        ) as iface:
            gr.Markdown("# 🔬 Community Resilience Research Interface")
            gr.Markdown(
                "Research-grade analysis tool for studying supportive digital health communities with expertise development tracking"
            )

            with gr.Row():
                with gr.Column(scale=3):
                    post_display = gr.Markdown(label="📝 Enhanced Post Analysis")

                    comments_display = gr.Markdown(
                        label="💬 Comments with Language Analysis"
                    )

                with gr.Column(scale=2):
                    stats_display = gr.Markdown(
                        value=self.get_research_profile_stats(),
                        label="Research Expertise Profile",
                    )

                    recommendations_display = gr.Markdown(
                        value=self.get_research_recommendations(),
                        label="Research Focus Recommendations",
                    )

                    health_context = gr.Textbox(
                        label="🩺 Enhanced Public Health Guidelines",
                        lines=5,
                        interactive=False,
                    )

                    suggestions = gr.Textbox(
                        label="🤖 AI Classification Suggestions",
                        lines=4,
                        interactive=False,
                    )

            gr.Markdown("---")

            with gr.Row():
                # Basic annotation (left column)
                with gr.Column():
                    gr.Markdown("### 🎯 Basic Classification")

                    category = gr.Radio(
                        choices=[
                            "Peer Support",
                            "Knowledge Sharing",
                            "Help Seeking",
                            "Cultural Bridging",
                            "Resource Sharing",
                            "Off-topic",
                        ],
                        label="Community Function",
                        value=None,
                    )

                    confidence = gr.Slider(
                        minimum=1, maximum=5, step=1, label="Confidence Level", value=3
                    )

                    notes = gr.Textbox(
                        label="Notes",
                        placeholder="Reasoning and additional context...",
                        lines=2,
                    )

                # Community impact analysis (middle column)
                with gr.Column():
                    gr.Markdown("### 💡 Community Impact Analysis")

                    severity_level = gr.Slider(
                        minimum=1,
                        maximum=5,
                        step=1,
                        label="Support Quality (1=Basic, 5=Exceptional)",
                        value=3,
                    )

                    misinformation_type = gr.Radio(
                        choices=["informational", "emotional", "practical"],
                        label="Support Type",
                        value="informational",
                    )

                    harm_potential = gr.Radio(
                        choices=["low", "medium", "high", "very high"],
                        label="Community Benefit",
                        value="medium",
                    )

                    urgency_score = gr.Slider(
                        minimum=1,
                        maximum=5,
                        step=1,
                        label="Replication Priority",
                        value=3,
                    )

                # Community support planning (right column)
                with gr.Column():
                    gr.Markdown("### 🤝 Community Support Enhancement")

                    target_community = gr.Dropdown(
                        choices=[
                            "English",
                            "Tagalog",
                            "Chinese",
                            "Punjabi",
                            "Spanish",
                            "Multi-language",
                            "General",
                        ],
                        label="Target Community",
                        value="General",
                    )

                    intervention_priority = gr.Radio(
                        choices=["low", "medium", "high", "urgent"],
                        label="Intervention Priority",
                        value="low",
                    )

                    health_topic = gr.Dropdown(
                        choices=[
                            "HIV/AIDS",
                            "PrEP",
                            "STI_testing",
                            "STI_treatment",
                            "General_health",
                            "Healthcare_access",
                        ],
                        label="Health Topic",
                        value="General_health",
                    )

                    target_population = gr.Dropdown(
                        choices=[
                            "newcomers",
                            "youth",
                            "MSM",
                            "general",
                            "LGBTQ+",
                            "immigrants",
                        ],
                        label="Target Population",
                        value="general",
                    )

                    suggested_response = gr.Radio(
                        choices=[
                            "amplify_support",
                            "provide_resources",
                            "facilitate_connection",
                            "document_practice",
                        ],
                        label="Enhancement Action",
                        value="amplify_support",
                    )

                    resource_needed = gr.Textbox(
                        label="Resources to Amplify",
                        placeholder="Resources to enhance or replicate this community support pattern...",
                        lines=2,
                    )

            with gr.Row():
                submit_btn = gr.Button(
                    "✅ Submit Community Analysis", variant="primary", size="lg"
                )
                skip_btn = gr.Button("⏭️ Skip Post", variant="secondary")

            status_message = gr.Textbox(label="Status", interactive=False)

            # Event handlers
            submit_btn.click(
                fn=submit_enhanced_annotation,
                inputs=[
                    category,
                    confidence,
                    notes,
                    severity_level,
                    misinformation_type,
                    target_community,
                    intervention_priority,
                    harm_potential,
                    urgency_score,
                    health_topic,
                    target_population,
                    suggested_response,
                    resource_needed,
                ],
                outputs=[status_message, stats_display],
            ).then(
                fn=display_enhanced_post,
                outputs=[
                    post_display,
                    comments_display,
                    health_context,
                    suggestions,
                    stats_display,
                ],
            ).then(
                fn=lambda: self.get_research_recommendations(),
                outputs=[recommendations_display],
            )

            skip_btn.click(
                fn=next_post,
                outputs=[
                    post_display,
                    comments_display,
                    health_context,
                    suggestions,
                    stats_display,
                ],
            )

            # Load initial post
            iface.load(
                fn=display_enhanced_post,
                outputs=[
                    post_display,
                    comments_display,
                    health_context,
                    suggestions,
                    stats_display,
                ],
            ).then(
                fn=lambda: self.get_research_recommendations(),
                outputs=[recommendations_display],
            )

        return iface

    def launch(self, share: bool = False):
        """Launch the enhanced Gradio interface"""
        iface = self.create_enhanced_interface()
        iface.launch(
            share=share,
            server_port=Config.GRADIO_PORT + 1,  # Use different port
            server_name="0.0.0.0" if share else "127.0.0.1",
        )


if __name__ == "__main__":
    # Example usage with database-driven loading
    # Load 50 posts from askgaybros subreddit
    filter_criteria = {"subreddit": "askgaybros"}
    annotation_tool = EnhancedAnnotationInterface(
        limit=50, filter_criteria=filter_criteria
    )
    annotation_tool.launch(share=False)
    annotation_tool = EnhancedAnnotationInterface(
        limit=50, filter_criteria=filter_criteria
    )
    annotation_tool.launch(share=False)
