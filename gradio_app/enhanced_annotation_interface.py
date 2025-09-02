"""
Enhanced Gradio interface for human annotation of Reddit posts
Supports the full enhanced schema including severity analysis, language communities, and intervention planning
"""

import gradio as gr
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional
import sqlite3
import os
from loguru import logger

from config.settings import Config, AnnotationConfig, ResearchConfig

class EnhancedAnnotationInterface:
    """Enhanced Gradio interface supporting full schema capabilities"""
    
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.current_post_index = 0
        self.posts_data = self.load_posts_data()
        self.annotation_db = 'data/enhanced_annotations.db'
        self.init_enhanced_database()
        
        # User session tracking
        self.current_user = "default_user"
        self.session_stats = {
            'posts_reviewed': 0,
            'session_start': datetime.now()
        }
    
    def load_posts_data(self) -> List[Dict]:
        """Load posts data for annotation"""
        with open(self.data_path, 'r') as f:
            return json.load(f)
    
    def init_enhanced_database(self):
        """Initialize SQLite database with enhanced schema support"""
        os.makedirs('data', exist_ok=True)
        
        conn = sqlite3.connect(self.annotation_db)
        cursor = conn.cursor()
        
        # Enhanced annotations table matching new schema
        cursor.execute('''
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
        ''')
        
        # Enhanced user stats table
        cursor.execute('''
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
        ''')
        
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
            'detected_languages': [],
            'code_switching_indicators': [],
            'cultural_references': [],
            'translation_indicators': []
        }
        
        text_lower = text.lower()
        
        # Simple language pattern detection (you could enhance this with proper NLP)
        if any(phrase in text_lower for phrase in ['kumusta', 'salamat', 'po']):
            patterns['detected_languages'].append('Tagalog')
        if any(phrase in text_lower for phrase in ['你好', '谢谢', 'ni hao']):
            patterns['detected_languages'].append('Chinese')
        if any(phrase in text_lower for phrase in ['sat sri akal', 'punjabi']):
            patterns['detected_languages'].append('Punjabi')
        if any(phrase in text_lower for phrase in ['gracias', 'hola', 'por favor']):
            patterns['detected_languages'].append('Spanish')
        
        # Code-switching indicators
        if len(patterns['detected_languages']) > 0:
            patterns['code_switching_indicators'].append('Mixed language usage detected')
        
        # Cultural health references
        cultural_terms = ['traditional medicine', 'herbal', 'home remedy', 'cultural practice', 
                         'back home', 'in my country', 'family tradition']
        for term in cultural_terms:
            if term in text_lower:
                patterns['cultural_references'].append(term)
        
        return patterns
    
    def get_enhanced_public_health_context(self, post_text: str) -> str:
        """Generate comprehensive public health guideline context"""
        context_items = []
        
        post_lower = post_text.lower()
        
        # Existing health context (enhanced)
        if any(term in post_lower for term in ['prep', 'truvada', 'descovy']):
            context_items.append(
                "🔷 **PrEP Guidelines (PHAC):** Pre-exposure prophylaxis is highly effective "
                "when taken daily. Available through provincial health programs. "
                "Severity: LOW for accurate info, HIGH for dosage misinformation."
            )
        
        if any(term in post_lower for term in ['hiv', 'viral load', 'undetectable']):
            context_items.append(
                "🔷 **HIV Facts (WHO):** Undetectable = Untransmittable (U=U). "
                "Modern treatment allows normal life expectancy. "
                "Severity: CRITICAL for stigma/transmission misinformation."
            )
        
        if any(term in post_lower for term in ['syphilis', 'chlamydia', 'gonorrhea', 'gonorrhoea']):
            context_items.append(
                "🔷 **STI Treatment (CDC):** Most bacterial STIs are curable with antibiotics. "
                "Regular testing prevents complications. "
                "Severity: MEDIUM for treatment delays, HIGH for cure denial."
            )
        
        # Newcomer-specific context
        if any(term in post_lower for term in ['ohip', 'health card', 'walk-in', 'without insurance']):
            context_items.append(
                "🍁 **Canadian Healthcare Access:** OHIP covers STI testing and treatment. "
                "Walk-in clinics accept uninsured patients. Community health centers available. "
                "Target: Newcomer communities."
            )
        
        # Cultural sensitivity context
        if any(term in post_lower for term in ['traditional', 'herbal', 'cultural', 'family']):
            context_items.append(
                "🌍 **Cultural Considerations:** Respect traditional practices while providing "
                "evidence-based medical information. Consider language barriers and cultural stigma. "
                "Intervention: Cultural competency required."
            )
        
        return "\n\n".join(context_items) if context_items else "No specific guidelines matched."
    
    def save_enhanced_annotation(self, category: str, confidence: int, notes: str = "",
                                severity_level: int = 1, misinformation_type: str = "",
                                target_community: str = "", intervention_priority: str = "low",
                                harm_potential: str = "low", urgency_score: int = 1,
                                health_topic: str = "", target_population: str = "",
                                suggested_response: str = "", resource_needed: str = "") -> str:
        """Save enhanced annotation with all new schema fields"""
        
        current_post = self.get_current_post()
        if "error" in current_post:
            return "Error: No post to annotate"
        
        # Analyze language patterns
        full_text = current_post['title'] + " " + current_post['selftext']
        lang_analysis = self.analyze_language_patterns(full_text)
        
        # Save enhanced annotation
        conn = sqlite3.connect(self.annotation_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO enhanced_annotations (
                post_id, annotator, category, confidence, notes, timestamp,
                severity_level, misinformation_type, target_community, intervention_priority,
                harm_potential, urgency_score, health_topic, target_population,
                suggested_response, resource_needed,
                detected_languages, code_switching_detected, cultural_references, translation_needed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            current_post['post_id'], self.current_user, category, confidence, notes,
            datetime.now().isoformat(), severity_level, misinformation_type,
            target_community, intervention_priority, harm_potential, urgency_score,
            health_topic, target_population, suggested_response, resource_needed,
            json.dumps(lang_analysis['detected_languages']),
            len(lang_analysis['code_switching_indicators']) > 0,
            json.dumps(lang_analysis['cultural_references']),
            'translation' in notes.lower()
        ))
        
        # Update enhanced user stats
        cursor.execute('''
            INSERT OR REPLACE INTO enhanced_user_stats (
                annotator, total_annotations, last_active, cultural_competency_score
            ) VALUES (?, 
                    COALESCE((SELECT total_annotations FROM enhanced_user_stats WHERE annotator = ?), 0) + 1,
                    ?, ?)
        ''', (self.current_user, self.current_user, datetime.now().isoformat(), 
              self.calculate_cultural_competency(lang_analysis)))
        
        conn.commit()
        conn.close()
        
        # Update session stats
        self.session_stats['posts_reviewed'] += 1
        self.current_post_index += 1
        
        return f"✅ Enhanced annotation saved! Post {self.session_stats['posts_reviewed']} completed."
    
    def calculate_cultural_competency(self, lang_analysis: Dict) -> float:
        """Calculate cultural competency score based on language analysis"""
        score = 0.0
        if lang_analysis['detected_languages']:
            score += 0.3
        if lang_analysis['cultural_references']:
            score += 0.4
        if lang_analysis['code_switching_indicators']:
            score += 0.3
        return min(score, 1.0)
    
    def get_enhanced_user_stats(self) -> str:
        """Get enhanced user statistics for gamification"""
        conn = sqlite3.connect(self.annotation_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT total_annotations, cultural_competency_score, community_expertise 
            FROM enhanced_user_stats WHERE annotator = ?
        ''', (self.current_user,))
        result = cursor.fetchone()
        
        if result:
            total, cultural_score, expertise = result
            expertise_list = json.loads(expertise) if expertise else []
        else:
            total, cultural_score, expertise_list = 0, 0.0, []
        
        conn.close()
        
        session_time = datetime.now() - self.session_stats['session_start']
        
        stats_text = f"""
        **📊 Enhanced Progress:**
        - Session: {self.session_stats['posts_reviewed']} posts reviewed
        - Total: {total} posts annotated
        - Cultural Competency: {cultural_score:.2f}/1.0
        - Session time: {str(session_time).split('.')[0]}
        - Progress: {self.current_post_index}/{len(self.posts_data)} posts
        """
        
        # Enhanced achievement badges
        if total >= 10:
            stats_text += "\n🏆 **Getting Started** - 10+ annotations!"
        if total >= 50:
            stats_text += "\n🌟 **Contributor** - 50+ annotations!"
        if total >= 100:
            stats_text += "\n💎 **Expert Annotator** - 100+ annotations!"
        if cultural_score >= 0.5:
            stats_text += "\n🌍 **Cultural Expert** - High cultural competency!"
        
        return stats_text
    
    def create_enhanced_interface(self):
        """Create the enhanced Gradio interface with full schema support"""
        
        def display_enhanced_post():
            """Display current post with enhanced analysis"""
            post = self.get_current_post()
            
            if "error" in post:
                return post["error"], "", "", "", self.get_enhanced_user_stats()
            
            # Enhanced post display with language analysis
            lang_analysis = self.analyze_language_patterns(post['title'] + " " + post['selftext'])
            
            post_display = f"""
            **Subreddit:** r/{post['subreddit']} | **Language:** {post['language']} | **Newcomer-related:** {post['is_newcomer_related']}
            **Title:** {post['title']}
            **Author:** {post['author']} | **Date:** {post['created_utc']}
            **Score:** {post['score']} | **Comments:** {post['num_comments']}
            
            **🔍 Language Analysis:**
            - Detected Languages: {', '.join(lang_analysis['detected_languages']) if lang_analysis['detected_languages'] else 'English only'}
            - Code-switching: {'Yes' if lang_analysis['code_switching_indicators'] else 'No'}
            - Cultural References: {', '.join(lang_analysis['cultural_references'][:3]) if lang_analysis['cultural_references'] else 'None detected'}
            
            **Content:**
            {post['selftext'][:1200]}{'...' if len(post['selftext']) > 1200 else ''}
            """
            
            # Enhanced comments display
            comments_display = ""
            if post.get('comments'):
                comments_display = "**💬 Comment Context:**\n"
                for i, comment in enumerate(post['comments'][:3]):
                    comment_lang = self.analyze_language_patterns(comment['body'])
                    lang_info = f"[{','.join(comment_lang['detected_languages']) if comment_lang['detected_languages'] else 'EN'}]"
                    comments_display += f"\n**{comment['author']}** {lang_info}: {comment['body'][:150]}{'...' if len(comment['body']) > 150 else ''}\n"
            
            # Enhanced health context
            health_context = self.get_enhanced_public_health_context(post['title'] + " " + post['selftext'])
            
            # Suggested classification based on analysis
            suggestions = self.generate_classification_suggestions(post, lang_analysis)
            
            return post_display, comments_display, health_context, suggestions, self.get_enhanced_user_stats()
        
        def generate_classification_suggestions(self, post, lang_analysis):
            """Generate intelligent classification suggestions"""
            suggestions = "**🤖 AI Suggestions:**\n"
            
            text = (post['title'] + " " + post['selftext']).lower()
            
            # Severity suggestions
            if any(term in text for term in ['cure', 'miracle', 'dangerous', 'deadly']):
                suggestions += "- High severity potential detected\n"
            if any(term in text for term in ['undetectable', 'prep', 'treatment']):
                suggestions += "- Medical accuracy critical\n"
            
            # Community targeting
            if lang_analysis['detected_languages']:
                suggestions += f"- Target community: {', '.join(lang_analysis['detected_languages'])}\n"
            if post['is_newcomer_related']:
                suggestions += "- Newcomer-focused intervention needed\n"
            
            # Intervention type
            if 'question' in text or '?' in post['title']:
                suggestions += "- Suggested response: Educational resource\n"
            else:
                suggestions += "- Suggested response: Fact-check\n"
            
            return suggestions
        
        def submit_enhanced_annotation(category, confidence, notes, severity_level, 
                                     misinformation_type, target_community, intervention_priority,
                                     harm_potential, urgency_score, health_topic, 
                                     target_population, suggested_response, resource_needed):
            """Handle enhanced annotation submission"""
            if not category:
                return "Please select a category!", self.get_enhanced_user_stats()
            
            result = self.save_enhanced_annotation(
                category, confidence, notes, severity_level, misinformation_type,
                target_community, intervention_priority, harm_potential, urgency_score,
                health_topic, target_population, suggested_response, resource_needed
            )
            
            return result, self.get_enhanced_user_stats()
        
        def next_post():
            """Move to next post without annotating"""
            self.current_post_index += 1
            return display_enhanced_post()
        
        # Create the enhanced Gradio interface
        with gr.Blocks(title="Enhanced Health Misinformation Annotation Tool", theme=gr.themes.Soft()) as iface:
            
            gr.Markdown("# 🏥 Enhanced Health Misinformation Annotation Tool")
            gr.Markdown("Advanced annotation interface supporting severity analysis, cultural competency, and intervention planning")
            
            with gr.Row():
                with gr.Column(scale=3):
                    post_display = gr.Textbox(
                        label="📝 Enhanced Post Analysis", 
                        lines=12,
                        interactive=False
                    )
                    
                    comments_display = gr.Textbox(
                        label="💬 Comments with Language Analysis",
                        lines=4,
                        interactive=False
                    )
                
                with gr.Column(scale=2):
                    stats_display = gr.Markdown(
                        value=self.get_enhanced_user_stats(),
                        label="Enhanced Progress Tracking"
                    )
                    
                    health_context = gr.Textbox(
                        label="🩺 Enhanced Public Health Guidelines",
                        lines=5,
                        interactive=False
                    )
                    
                    suggestions = gr.Textbox(
                        label="🤖 AI Classification Suggestions",
                        lines=4,
                        interactive=False
                    )
            
            gr.Markdown("---")
            
            with gr.Row():
                # Basic annotation (left column)
                with gr.Column():
                    gr.Markdown("### 🎯 Basic Classification")
                    
                    category = gr.Radio(
                        choices=['Accurate', 'Misinformation', 'Unclear/Mixed', 'Off-topic'],
                        label="Content Category",
                        value=None
                    )
                    
                    confidence = gr.Slider(
                        minimum=1, maximum=5, step=1,
                        label="Confidence Level",
                        value=3
                    )
                    
                    notes = gr.Textbox(
                        label="Notes",
                        placeholder="Reasoning and additional context...",
                        lines=2
                    )
                
                # Enhanced severity analysis (middle column)
                with gr.Column():
                    gr.Markdown("### ⚠️ Severity Analysis")
                    
                    severity_level = gr.Slider(
                        minimum=1, maximum=5, step=1,
                        label="Severity Level (1=Misconception, 5=Dangerous)",
                        value=1
                    )
                    
                    misinformation_type = gr.Radio(
                        choices=['misconception', 'harmful', 'malicious'],
                        label="Misinformation Type",
                        value='misconception'
                    )
                    
                    harm_potential = gr.Radio(
                        choices=['low', 'medium', 'high', 'critical'],
                        label="Harm Potential",
                        value='low'
                    )
                    
                    urgency_score = gr.Slider(
                        minimum=1, maximum=5, step=1,
                        label="Response Urgency",
                        value=1
                    )
                
                # Intervention planning (right column)
                with gr.Column():
                    gr.Markdown("### 🎯 Intervention Planning")
                    
                    target_community = gr.Dropdown(
                        choices=['English', 'Tagalog', 'Chinese', 'Punjabi', 'Spanish', 'Multi-language', 'General'],
                        label="Target Community",
                        value='General'
                    )
                    
                    intervention_priority = gr.Radio(
                        choices=['low', 'medium', 'high', 'urgent'],
                        label="Intervention Priority",
                        value='low'
                    )
                    
                    health_topic = gr.Dropdown(
                        choices=['HIV/AIDS', 'PrEP', 'STI_testing', 'STI_treatment', 'General_health', 'Healthcare_access'],
                        label="Health Topic",
                        value='General_health'
                    )
                    
                    target_population = gr.Dropdown(
                        choices=['newcomers', 'youth', 'MSM', 'general', 'LGBTQ+', 'immigrants'],
                        label="Target Population",
                        value='general'
                    )
                    
                    suggested_response = gr.Radio(
                        choices=['educate', 'fact_check', 'resource_link', 'urgent_intervention'],
                        label="Suggested Response",
                        value='educate'
                    )
                    
                    resource_needed = gr.Textbox(
                        label="Resources Needed",
                        placeholder="Specific resources or corrections needed...",
                        lines=2
                    )
            
            with gr.Row():
                submit_btn = gr.Button("✅ Submit Enhanced Annotation", variant="primary", size="lg")
                skip_btn = gr.Button("⏭️ Skip Post", variant="secondary")
            
            status_message = gr.Textbox(label="Status", interactive=False)
            
            # Event handlers
            submit_btn.click(
                fn=submit_enhanced_annotation,
                inputs=[category, confidence, notes, severity_level, misinformation_type,
                       target_community, intervention_priority, harm_potential, urgency_score,
                       health_topic, target_population, suggested_response, resource_needed],
                outputs=[status_message, stats_display]
            ).then(
                fn=display_enhanced_post,
                outputs=[post_display, comments_display, health_context, suggestions, stats_display]
            )
            
            skip_btn.click(
                fn=next_post,
                outputs=[post_display, comments_display, health_context, suggestions, stats_display]
            )
            
            # Load initial post
            iface.load(
                fn=display_enhanced_post,
                outputs=[post_display, comments_display, health_context, suggestions, stats_display]
            )
        
        return iface
    
    def launch(self, share: bool = False):
        """Launch the enhanced Gradio interface"""
        iface = self.create_enhanced_interface()
        iface.launch(
            share=share,
            server_port=Config.GRADIO_PORT + 1,  # Use different port
            server_name="0.0.0.0" if share else "127.0.0.1"
        )

if __name__ == "__main__":
    # Example usage
    annotation_tool = EnhancedAnnotationInterface('data/raw_reddit_data_latest.json')
    annotation_tool.launch(share=False)
