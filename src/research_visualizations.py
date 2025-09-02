"""
Research Visualizations for Health Misinformation Detection Platform
Comprehensive visualization system for data analysis and research insights
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import json
import sqlite3
from datetime import datetime
from typing import Dict, Optional
from collections import Counter
from loguru import logger


class ResearchVisualizations:
    """Comprehensive visualization system for research analysis"""

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self.data = None
        self.annotations_db = "data/enhanced_annotations.db"

        # Color schemes for consistent branding
        self.colors = {
            "primary": "#2E86AB",
            "secondary": "#A23B72",
            "accent": "#F18F01",
            "success": "#C73E1D",
            "warning": "#F5B041",
            "danger": "#E74C3C",
            "misinformation": "#E74C3C",
            "accurate": "#27AE60",
            "unclear": "#F39C12",
            "severity_colors": ["#27AE60", "#F39C12", "#E67E22", "#E74C3C", "#8E44AD"],
        }

    def load_data(self) -> None:
        """Load Reddit data from JSON file"""
        if self.data_path and self.data_path.endswith(".json"):
            with open(self.data_path, "r") as f:
                self.data = json.load(f)
            logger.info(f"Loaded {len(self.data)} posts for visualization")

    def create_data_overview_dashboard(self) -> go.Figure:
        """Create comprehensive data overview dashboard"""
        if not self.data:
            self.load_data()

        # Create subplot structure
        fig = make_subplots(
            rows=3,
            cols=3,
            subplot_titles=[
                "Posts by Subreddit",
                "Language Distribution",
                "Temporal Activity",
                "Health Keywords Found",
                "Newcomer Content",
                "Post Engagement",
                "Comment Activity",
                "Language Patterns",
                "Content Quality",
            ],
            specs=[
                [{"type": "bar"}, {"type": "pie"}, {"type": "scatter"}],
                [{"type": "bar"}, {"type": "indicator"}, {"type": "box"}],
                [{"type": "histogram"}, {"type": "bar"}, {"type": "violin"}],
            ],
        )

        # 1. Posts by Subreddit
        subreddit_counts = Counter([post["subreddit"] for post in self.data])
        fig.add_trace(
            go.Bar(
                x=list(subreddit_counts.keys()),
                y=list(subreddit_counts.values()),
                marker_color=self.colors["primary"],
                name="Posts",
            ),
            row=1,
            col=1,
        )

        # 2. Language Distribution
        lang_counts = Counter([post.get("language", "unknown") for post in self.data])
        fig.add_trace(
            go.Pie(
                labels=list(lang_counts.keys()),
                values=list(lang_counts.values()),
                marker_colors=px.colors.qualitative.Set3,
            ),
            row=1,
            col=2,
        )

        # 3. Temporal Activity
        dates = [
            datetime.fromisoformat(post["created_utc"].replace("Z", "+00:00"))
            for post in self.data
            if "created_utc" in post
        ]
        if dates:
            date_counts = Counter([d.date() for d in dates])
            fig.add_trace(
                go.Scatter(
                    x=list(date_counts.keys()),
                    y=list(date_counts.values()),
                    mode="lines+markers",
                    marker_color=self.colors["accent"],
                    name="Daily Posts",
                ),
                row=1,
                col=3,
            )

        # 4. Health Keywords
        keyword_mentions = {}
        keywords = ["HIV", "PrEP", "syphilis", "chlamydia", "gonorrhea", "doxy"]
        for keyword in keywords:
            count = sum(
                1
                for post in self.data
                if keyword.lower()
                in (post["title"] + " " + post.get("selftext", "")).lower()
            )
            keyword_mentions[keyword] = count

        fig.add_trace(
            go.Bar(
                x=list(keyword_mentions.keys()),
                y=list(keyword_mentions.values()),
                marker_color=self.colors["secondary"],
                name="Keyword Mentions",
            ),
            row=2,
            col=1,
        )

        # 5. Newcomer Content Indicator
        newcomer_count = sum(
            1 for post in self.data if post.get("is_newcomer_related", False)
        )
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=newcomer_count,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Newcomer Posts"},
                gauge={
                    "axis": {"range": [0, len(self.data)]},
                    "bar": {"color": self.colors["accent"]},
                    "steps": [
                        {"range": [0, len(self.data) // 2], "color": "lightgray"}
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": len(self.data) * 0.3,
                    },
                },
            ),
            row=2,
            col=2,
        )

        # 6. Post Engagement (scores)
        scores = [post.get("score", 0) for post in self.data]
        fig.add_trace(
            go.Box(y=scores, name="Post Scores", marker_color=self.colors["primary"]),
            row=2,
            col=3,
        )

        # 7. Comment Activity
        comment_counts = [post.get("num_comments", 0) for post in self.data]
        fig.add_trace(
            go.Histogram(
                x=comment_counts,
                nbinsx=20,
                marker_color=self.colors["accent"],
                name="Comments Distribution",
            ),
            row=3,
            col=1,
        )

        # 8. Language Complexity (by subreddit)
        subreddit_langs = {}
        for post in self.data:
            subreddit = post["subreddit"]
            if subreddit not in subreddit_langs:
                subreddit_langs[subreddit] = []
            subreddit_langs[subreddit].append(post.get("language", "en"))

        lang_diversity = {sr: len(set(langs)) for sr, langs in subreddit_langs.items()}
        fig.add_trace(
            go.Bar(
                x=list(lang_diversity.keys()),
                y=list(lang_diversity.values()),
                marker_color=self.colors["secondary"],
                name="Language Diversity",
            ),
            row=3,
            col=2,
        )

        # 9. Content Quality (text length distribution)
        text_lengths = [
            len(post["title"] + " " + post.get("selftext", "")) for post in self.data
        ]
        fig.add_trace(
            go.Violin(
                y=text_lengths, name="Text Length", marker_color=self.colors["primary"]
            ),
            row=3,
            col=3,
        )

        # Update layout
        fig.update_layout(
            height=1200,
            title_text=f"Research Data Overview Dashboard - {len(self.data)} Posts",
            showlegend=False,
            template="plotly_white",
        )

        return fig

    def create_network_visualization(
        self, network_data: Optional[Dict] = None
    ) -> go.Figure:
        """Create interactive network visualization"""
        if not network_data and self.data:
            # Build simple network from data
            network_data = self._build_network_from_data()

        if not network_data:
            return go.Figure().add_annotation(text="No network data available")

        # Extract network components
        nodes = network_data.get("nodes", [])
        edges = network_data.get("edges", [])

        # Create network layout (spring layout simulation)
        pos = {}
        for i, node in enumerate(nodes):
            angle = 2 * np.pi * i / len(nodes)
            pos[node["id"]] = (np.cos(angle), np.sin(angle))

        # Create edge traces
        edge_x, edge_y = [], []
        for edge in edges:
            if edge["source"] in pos and edge["target"] in pos:
                x0, y0 = pos[edge["source"]]
                x1, y1 = pos[edge["target"]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])

        # Create node traces
        node_x = [pos[node["id"]][0] for node in nodes if node["id"] in pos]
        node_y = [pos[node["id"]][1] for node in nodes if node["id"] in pos]
        node_text = [
            f"{node['id']}<br>Degree: {node.get('degree', 0)}"
            for node in nodes
            if node["id"] in pos
        ]

        fig = go.Figure()

        # Add edges
        fig.add_trace(
            go.Scatter(
                x=edge_x,
                y=edge_y,
                mode="lines",
                line=dict(width=1, color="rgba(125, 125, 125, 0.5)"),
                hoverinfo="none",
                showlegend=False,
            )
        )

        # Add nodes
        fig.add_trace(
            go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers+text",
                marker=dict(
                    size=[
                        node.get("degree", 5) * 2 + 10
                        for node in nodes
                        if node["id"] in pos
                    ],
                    color=[
                        node.get("influence", 1) for node in nodes if node["id"] in pos
                    ],
                    colorscale="Viridis",
                    line=dict(width=2, color="white"),
                ),
                text=node_text,
                textposition="middle center",
                hoverinfo="text",
                showlegend=False,
            )
        )

        fig.update_layout(
            title="User Interaction Network",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Network shows user interactions based on comments and replies",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.002,
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(color="gray", size=12),
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            template="plotly_white",
        )

        return fig

    def create_annotation_analysis_dashboard(self) -> go.Figure:
        """Create dashboard analyzing annotation data"""
        try:
            conn = sqlite3.connect(self.annotations_db)

            # Load annotation data
            annotations_df = pd.read_sql_query(
                """
                SELECT * FROM enhanced_annotations 
                WHERE timestamp IS NOT NULL
                ORDER BY timestamp DESC
            """,
                conn,
            )

            if annotations_df.empty:
                return go.Figure().add_annotation(
                    text="No annotation data available yet.<br>Start annotating posts to see analysis here!",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=16),
                )

            # Create subplot structure
            fig = make_subplots(
                rows=2,
                cols=3,
                subplot_titles=[
                    "Annotation Categories",
                    "Severity Distribution",
                    "Annotator Activity",
                    "Confidence Levels",
                    "Health Topics",
                    "Intervention Priority",
                ],
                specs=[
                    [{"type": "pie"}, {"type": "bar"}, {"type": "bar"}],
                    [{"type": "histogram"}, {"type": "sunburst"}, {"type": "bar"}],
                ],
            )

            # 1. Annotation Categories
            category_counts = annotations_df["category"].value_counts()
            colors = [
                (
                    self.colors["accurate"]
                    if cat == "Accurate"
                    else (
                        self.colors["misinformation"]
                        if cat == "Misinformation"
                        else self.colors["unclear"]
                    )
                )
                for cat in category_counts.index
            ]

            fig.add_trace(
                go.Pie(
                    labels=category_counts.index,
                    values=category_counts.values,
                    marker=dict(colors=colors),
                ),
                row=1,
                col=1,
            )

            # 2. Severity Distribution
            if "severity_level" in annotations_df.columns:
                severity_counts = (
                    annotations_df["severity_level"].value_counts().sort_index()
                )
                fig.add_trace(
                    go.Bar(
                        x=severity_counts.index,
                        y=severity_counts.values,
                        marker=dict(
                            color=[
                                self.colors["severity_colors"][int(i) - 1]
                                for i in severity_counts.index
                                if i <= 5
                            ]
                        ),
                    ),
                    row=1,
                    col=2,
                )

            # 3. Annotator Activity
            annotator_counts = annotations_df["annotator"].value_counts()
            fig.add_trace(
                go.Bar(
                    x=annotator_counts.index,
                    y=annotator_counts.values,
                    marker_color=self.colors["primary"],
                ),
                row=1,
                col=3,
            )

            # 4. Confidence Levels
            confidence_dist = annotations_df["confidence"].value_counts().sort_index()
            fig.add_trace(
                go.Histogram(
                    x=annotations_df["confidence"],
                    nbinsx=5,
                    marker_color=self.colors["accent"],
                ),
                row=2,
                col=1,
            )

            # 5. Health Topics (if available)
            if "health_topic" in annotations_df.columns:
                topic_counts = annotations_df["health_topic"].value_counts()
                # Create a sunburst chart for topics and severity
                fig.add_trace(
                    go.Sunburst(
                        labels=list(topic_counts.index) + ["Overall"],
                        parents=["Overall"] * len(topic_counts.index) + [""],
                        values=list(topic_counts.values) + [topic_counts.sum()],
                    ),
                    row=2,
                    col=2,
                )

            # 6. Intervention Priority
            if "intervention_priority" in annotations_df.columns:
                priority_counts = annotations_df["intervention_priority"].value_counts()
                priority_colors = {
                    "low": "#27AE60",
                    "medium": "#F39C12",
                    "high": "#E67E22",
                    "urgent": "#E74C3C",
                }
                colors = [
                    priority_colors.get(p, self.colors["primary"])
                    for p in priority_counts.index
                ]

                fig.add_trace(
                    go.Bar(
                        x=priority_counts.index,
                        y=priority_counts.values,
                        marker=dict(color=colors),
                    ),
                    row=2,
                    col=3,
                )

            fig.update_layout(
                height=800,
                title_text=f"Annotation Analysis Dashboard - {len(annotations_df)} Annotations",
                showlegend=False,
                template="plotly_white",
            )

            conn.close()
            return fig

        except Exception as e:
            logger.error(f"Error creating annotation dashboard: {e}")
            return go.Figure().add_annotation(
                text=f"Error loading annotation data: {str(e)}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14),
            )

    def create_temporal_analysis(self) -> go.Figure:
        """Create temporal analysis of posts and annotations"""
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=["Post Collection Timeline", "Annotation Progress"],
            shared_xaxes=True,
        )

        # Posts timeline
        if self.data:
            dates = []
            for post in self.data:
                try:
                    if "created_utc" in post:
                        date_str = post["created_utc"]
                        if isinstance(date_str, str):
                            date = pd.to_datetime(date_str)
                        else:
                            date = pd.to_datetime(date_str, unit="s")
                        dates.append(date)
                except:
                    continue

            if dates:
                date_counts = pd.Series(dates).dt.date.value_counts().sort_index()
                fig.add_trace(
                    go.Scatter(
                        x=date_counts.index,
                        y=date_counts.values,
                        mode="lines+markers",
                        name="Posts Collected",
                        line=dict(color=self.colors["primary"]),
                    ),
                    row=1,
                    col=1,
                )

        # Annotations timeline
        try:
            conn = sqlite3.connect(self.annotations_db)
            annotations_df = pd.read_sql_query(
                """
                SELECT timestamp FROM enhanced_annotations 
                WHERE timestamp IS NOT NULL
            """,
                conn,
            )

            if not annotations_df.empty:
                annotations_df["timestamp"] = pd.to_datetime(
                    annotations_df["timestamp"]
                )
                annotation_counts = (
                    annotations_df["timestamp"].dt.date.value_counts().sort_index()
                )

                fig.add_trace(
                    go.Scatter(
                        x=annotation_counts.index,
                        y=annotation_counts.values,
                        mode="lines+markers",
                        name="Annotations",
                        line=dict(color=self.colors["secondary"]),
                    ),
                    row=2,
                    col=1,
                )

            conn.close()
        except Exception as e:
            logger.warning(f"Could not load annotation timeline: {e}")

        fig.update_layout(
            height=600,
            title_text="Temporal Analysis - Data Collection & Annotation Progress",
            template="plotly_white",
        )

        return fig

    def create_health_keywords_analysis(self) -> go.Figure:
        """Analyze health keyword patterns across posts"""
        if not self.data:
            self.load_data()

        keywords = {
            "PrEP Related": ["prep", "truvada", "descovy", "pre-exposure"],
            "HIV Related": ["hiv", "viral load", "undetectable", "cd4"],
            "STI Related": ["syphilis", "chlamydia", "gonorrhea", "gonorrhoea", "doxy"],
            "Healthcare Access": [
                "ohip",
                "clinic",
                "doctor",
                "healthcare",
                "insurance",
            ],
        }

        # Count keywords by subreddit
        subreddit_keywords = {}
        for post in self.data:
            subreddit = post["subreddit"]
            text = (post["title"] + " " + post.get("selftext", "")).lower()

            if subreddit not in subreddit_keywords:
                subreddit_keywords[subreddit] = {category: 0 for category in keywords}

            for category, terms in keywords.items():
                if any(term in text for term in terms):
                    subreddit_keywords[subreddit][category] += 1

        # Create stacked bar chart
        categories = list(keywords.keys())
        subreddits = list(subreddit_keywords.keys())

        fig = go.Figure()

        colors = [
            self.colors["primary"],
            self.colors["secondary"],
            self.colors["accent"],
            self.colors["success"],
        ]

        for i, category in enumerate(categories):
            values = [subreddit_keywords[sr][category] for sr in subreddits]
            fig.add_trace(
                go.Bar(
                    name=category,
                    x=subreddits,
                    y=values,
                    marker_color=colors[i % len(colors)],
                )
            )

        fig.update_layout(
            title="Health Keywords by Subreddit",
            xaxis_title="Subreddit",
            yaxis_title="Keyword Mentions",
            barmode="stack",
            template="plotly_white",
            height=500,
        )

        return fig

    def create_language_community_analysis(self) -> go.Figure:
        """Analyze language patterns and community indicators"""
        if not self.data:
            self.load_data()

        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=[
                "Language Distribution by Subreddit",
                "Newcomer Content Analysis",
            ],
            specs=[[{"type": "bar"}, {"type": "scatter"}]],
        )

        # Language by subreddit
        subreddit_langs = {}
        for post in self.data:
            subreddit = post["subreddit"]
            language = post.get("language", "unknown")

            if subreddit not in subreddit_langs:
                subreddit_langs[subreddit] = {}
            subreddit_langs[subreddit][language] = (
                subreddit_langs[subreddit].get(language, 0) + 1
            )

        # Create stacked bar for languages
        all_languages = set()
        for langs in subreddit_langs.values():
            all_languages.update(langs.keys())

        for i, lang in enumerate(all_languages):
            values = [
                subreddit_langs.get(sr, {}).get(lang, 0)
                for sr in subreddit_langs.keys()
            ]
            fig.add_trace(
                go.Bar(
                    name=lang,
                    x=list(subreddit_langs.keys()),
                    y=values,
                    marker_color=px.colors.qualitative.Set3[
                        i % len(px.colors.qualitative.Set3)
                    ],
                ),
                row=1,
                col=1,
            )

        # Newcomer analysis
        newcomer_data = []
        for post in self.data:
            newcomer_data.append(
                {
                    "subreddit": post["subreddit"],
                    "is_newcomer": post.get("is_newcomer_related", False),
                    "score": post.get("score", 0),
                    "comments": post.get("num_comments", 0),
                }
            )

        newcomer_df = pd.DataFrame(newcomer_data)

        # Scatter plot of newcomer posts
        for is_newcomer in [True, False]:
            subset = newcomer_df[newcomer_df["is_newcomer"] == is_newcomer]
            fig.add_trace(
                go.Scatter(
                    x=subset["score"],
                    y=subset["comments"],
                    mode="markers",
                    name="Newcomer Related" if is_newcomer else "General Posts",
                    marker=dict(
                        color=(
                            self.colors["accent"]
                            if is_newcomer
                            else self.colors["primary"]
                        ),
                        size=8,
                        opacity=0.7,
                    ),
                ),
                row=1,
                col=2,
            )

        fig.update_layout(
            height=500,
            title_text="Language & Community Analysis",
            template="plotly_white",
        )

        return fig

    def _build_network_from_data(self) -> Dict:
        """Build a simple network structure from post data"""
        nodes = []
        edges = []
        user_stats = {}

        # Collect users and their activity
        for post in self.data:
            author = post.get("author", "unknown")
            if author != "[deleted]":
                if author not in user_stats:
                    user_stats[author] = {"posts": 0, "comments": 0, "interactions": 0}
                user_stats[author]["posts"] += 1

                # Process comments for interactions
                for comment in post.get("comments", []):
                    commenter = comment.get("author", "unknown")
                    if commenter != "[deleted]" and commenter != author:
                        if commenter not in user_stats:
                            user_stats[commenter] = {
                                "posts": 0,
                                "comments": 0,
                                "interactions": 0,
                            }
                        user_stats[commenter]["comments"] += 1
                        user_stats[commenter]["interactions"] += 1

                        # Create edge
                        edges.append(
                            {"source": commenter, "target": author, "weight": 1}
                        )

        # Create nodes
        for user, stats in user_stats.items():
            nodes.append(
                {
                    "id": user,
                    "degree": stats["posts"] + stats["comments"],
                    "influence": stats["interactions"],
                    "type": "author" if stats["posts"] > 0 else "commenter",
                }
            )

        return {"nodes": nodes, "edges": edges}

    def save_all_visualizations(
        self, output_dir: str = "visualizations"
    ) -> Dict[str, str]:
        """Generate and save all visualizations"""
        import os

        os.makedirs(output_dir, exist_ok=True)

        saved_files = {}

        try:
            # Data overview dashboard
            fig = self.create_data_overview_dashboard()
            path = f"{output_dir}/data_overview_dashboard.html"
            fig.write_html(path)
            saved_files["data_overview"] = path

            # Network visualization
            fig = self.create_network_visualization()
            path = f"{output_dir}/network_visualization.html"
            fig.write_html(path)
            saved_files["network"] = path

            # Annotation analysis
            fig = self.create_annotation_analysis_dashboard()
            path = f"{output_dir}/annotation_analysis.html"
            fig.write_html(path)
            saved_files["annotations"] = path

            # Temporal analysis
            fig = self.create_temporal_analysis()
            path = f"{output_dir}/temporal_analysis.html"
            fig.write_html(path)
            saved_files["temporal"] = path

            # Health keywords analysis
            fig = self.create_health_keywords_analysis()
            path = f"{output_dir}/health_keywords_analysis.html"
            fig.write_html(path)
            saved_files["keywords"] = path

            # Language community analysis
            fig = self.create_language_community_analysis()
            path = f"{output_dir}/language_community_analysis.html"
            fig.write_html(path)
            saved_files["language"] = path

            logger.info(f"Saved {len(saved_files)} visualizations to {output_dir}/")

        except Exception as e:
            logger.error(f"Error saving visualizations: {e}")

        return saved_files


if __name__ == "__main__":
    # Example usage
    import sys

    if len(sys.argv) > 1:
        data_path = sys.argv[1]
    else:
        # Use most recent demo data
        import glob

        demo_files = glob.glob("data/demo_data_*.json")
        if demo_files:
            data_path = max(demo_files)
        else:
            print("No data files found. Please provide a data path.")
            sys.exit(1)

    print(f"Creating visualizations for: {data_path}")

    viz = ResearchVisualizations(data_path)
    saved_files = viz.save_all_visualizations()

    print("\n✅ Generated visualizations:")
    for name, path in saved_files.items():
        print(f"   📊 {name}: {path}")

    print("\n🎯 Open any HTML file in your browser to view the interactive charts!")
