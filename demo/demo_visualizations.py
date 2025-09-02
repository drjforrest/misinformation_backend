"""
Demo Visualization Dashboard for Misinformation Detection Pipeline
Creates interactive visualizations to demonstrate system capabilities
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import networkx as nx
import numpy as np


class DemoVisualizationDashboard:
    def __init__(self, demo_data_file: str = "demo_dataset.json"):
        with open(demo_data_file, "r") as f:
            self.data = json.load(f)

        self.posts_df = pd.DataFrame(self.data["posts"])
        self.annotations_df = pd.DataFrame(self.data["annotations"])
        self.interactions_df = pd.DataFrame(self.data["interactions"])

        # Convert datetime strings back to datetime objects
        self.posts_df["created_utc"] = pd.to_datetime(self.posts_df["created_utc"])
        self.posts_df["added_to_queue"] = pd.to_datetime(
            self.posts_df["added_to_queue"]
        )

        plt.style.use("default")  # Use default instead of seaborn-v0_8

    def create_queue_status_visualization(self):
        """Show the annotation queue with priorities"""
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Annotation Queue Status",
                "Priority Distribution",
                "Severity by Health Topic",
                "Canadian Users vs Misinformation",
            ),
            specs=[
                [{"type": "bar"}, {"type": "histogram"}],
                [{"type": "scatter"}, {"type": "scatter"}],
            ],
        )

        # Queue status distribution
        queue_counts = self.posts_df["queue_status"].value_counts()
        fig.add_trace(
            go.Bar(
                x=queue_counts.index,
                y=queue_counts.values,
                name="Queue Status",
                marker_color=["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"],
            ),
            row=1,
            col=1,
        )

        # Priority score histogram
        fig.add_trace(
            go.Histogram(
                x=self.posts_df["priority_score"],
                nbinsx=8,
                name="Priority Distribution",
                marker_color="#FFA07A",
            ),
            row=1,
            col=2,
        )

        # Severity by health topic
        severity_topic = (
            self.posts_df.groupby("health_topic")["severity_level"].mean().reset_index()
        )
        fig.add_trace(
            go.Scatter(
                x=severity_topic["health_topic"],
                y=severity_topic["severity_level"],
                mode="markers",
                marker=dict(size=12, color="#FF69B4"),
                name="Avg Severity by Topic",
            ),
            row=2,
            col=1,
        )

        # Canadian probability vs severity
        fig.add_trace(
            go.Scatter(
                x=self.posts_df["canadian_probability"],
                y=self.posts_df["severity_level"],
                mode="markers",
                marker=dict(
                    size=8,
                    color=self.posts_df["priority_score"],
                    colorscale="Viridis",
                    showscale=True,
                ),
                name="Canadian Users vs Severity",
            ),
            row=2,
            col=2,
        )

        fig.update_layout(
            height=800,
            title_text="Misinformation Detection Queue Dashboard",
            title_x=0.5,
            showlegend=False,
        )

        return fig

    def create_severity_spectrum_analysis(self):
        """Visualize the misinformation severity spectrum - your key innovation"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))

        # Severity distribution
        severity_counts = self.posts_df["severity_level"].value_counts().sort_index()
        axes[0, 0].bar(
            severity_counts.index,
            severity_counts.values,
            color=["#2ECC71", "#F39C12", "#E67E22", "#E74C3C", "#8E44AD"],
        )
        axes[0, 0].set_title("Misinformation Severity Distribution")
        axes[0, 0].set_xlabel("Severity Level (1=Harmless → 5=Dangerous)")
        axes[0, 0].set_ylabel("Number of Posts")

        # Type vs Severity heatmap
        type_severity = pd.crosstab(
            self.posts_df["misinformation_type"], self.posts_df["severity_level"]
        )
        sns.heatmap(
            type_severity,
            annot=True,
            fmt="d",
            ax=axes[0, 1],
            cmap="YlOrRd",
            cbar_kws={"label": "Post Count"},
        )
        axes[0, 1].set_title("Misinformation Type vs Severity Level")

        # Harm potential distribution
        harm_counts = self.posts_df["harm_potential"].value_counts()
        harm_order = ["low", "medium", "high", "critical"]
        harm_counts = harm_counts.reindex(harm_order, fill_value=0)

        colors = ["#27AE60", "#F39C12", "#E67E22", "#C0392B"]
        axes[1, 0].pie(
            harm_counts.values,
            labels=harm_counts.index,
            autopct="%1.1f%%",
            colors=colors,
        )
        axes[1, 0].set_title("Harm Potential Distribution")

        # Health topic vs severity
        topic_severity = self.posts_df.groupby("health_topic")["severity_level"].agg(
            ["mean", "count"]
        )
        scatter = axes[1, 1].scatter(
            topic_severity["mean"],
            topic_severity["count"],
            s=100,
            alpha=0.7,
            c=topic_severity["mean"],
            cmap="RdYlBu_r",
        )
        axes[1, 1].set_xlabel("Average Severity Level")
        axes[1, 1].set_ylabel("Number of Posts")
        axes[1, 1].set_title("Health Topics: Severity vs Volume")

        # Add topic labels
        for idx, topic in enumerate(topic_severity.index):
            axes[1, 1].annotate(
                topic.replace("_", " "),
                (topic_severity.iloc[idx]["mean"], topic_severity.iloc[idx]["count"]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
            )

        plt.tight_layout()
        return fig

    def create_network_analysis_viz(self):
        """Visualize the social network of misinformation spread"""
        # Create network graph
        G = nx.Graph()

        # Add nodes (users)
        users = set(self.interactions_df["source_user_id"]).union(
            set(self.interactions_df["target_user_id"])
        )
        G.add_nodes_from(users)

        # Add edges (interactions)
        for _, interaction in self.interactions_df.iterrows():
            G.add_edge(interaction["source_user_id"], interaction["target_user_id"])

        # Calculate network metrics
        centrality = nx.degree_centrality(G)
        clustering = nx.clustering(G)

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        # Network visualization
        pos = nx.spring_layout(G, k=1, iterations=50)

        # Color nodes by misinformation involvement
        misinfo_users = set(
            self.interactions_df[
                self.interactions_df["is_misinformation_related"] == True
            ]["source_user_id"]
        )

        node_colors = [
            "#E74C3C" if node in misinfo_users else "#3498DB" for node in G.nodes()
        ]
        node_sizes = [centrality[node] * 1000 + 100 for node in G.nodes()]

        nx.draw(
            G,
            pos,
            ax=axes[0],
            node_color=node_colors,
            node_size=node_sizes,
            with_labels=False,
            edge_color="lightgray",
            alpha=0.7,
        )
        axes[0].set_title(
            "Social Network of Health Discussions\n(Red: Misinformation involved, Blue: Clean)"
        )

        # Network metrics
        metrics_data = {
            "User": list(centrality.keys())[:8],  # Top 8 users
            "Centrality": [centrality[user] for user in list(centrality.keys())[:8]],
            "Clustering": [clustering[user] for user in list(centrality.keys())[:8]],
        }

        x_pos = np.arange(len(metrics_data["User"]))
        width = 0.35

        axes[1].bar(
            x_pos - width / 2,
            metrics_data["Centrality"],
            width,
            label="Degree Centrality",
            color="#3498DB",
            alpha=0.7,
        )
        axes[1].bar(
            x_pos + width / 2,
            metrics_data["Clustering"],
            width,
            label="Clustering Coefficient",
            color="#E74C3C",
            alpha=0.7,
        )

        axes[1].set_xlabel("Top Users")
        axes[1].set_ylabel("Network Metrics")
        axes[1].set_title("User Influence and Community Formation")
        axes[1].set_xticks(x_pos)
        axes[1].set_xticklabels(
            [uid[:8] + "..." for uid in metrics_data["User"]], rotation=45
        )
        axes[1].legend()

        plt.tight_layout()
        return fig

    def create_intervention_pipeline_viz(self):
        """Show the intervention response pipeline"""
        # Simulate intervention responses
        interventions = []
        for _, post in self.posts_df.iterrows():
            if post["severity_level"] >= 3:  # Only for significant misinformation
                intervention = {
                    "post_id": post["post_id"],
                    "severity": post["severity_level"],
                    "response_type": (
                        "urgent_correction"
                        if post["severity_level"] >= 4
                        else "educational_resource"
                    ),
                    "target_community": (
                        "newcomers"
                        if "clinic" in post["selftext"].lower()
                        else "general"
                    ),
                    "resource_needed": f"Canadian {post['health_topic'].replace('_', ' ')} information",
                    "priority_queue_position": post["priority_score"],
                }
                interventions.append(intervention)

        interventions_df = pd.DataFrame(interventions)

        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Intervention Response Types",
                "Priority Queue Position",
                "Target Communities",
                "Resource Categories",
            ),
            specs=[
                [{"type": "pie"}, {"type": "bar"}],
                [{"type": "pie"}, {"type": "bar"}],
            ],
        )

        # Response types
        response_counts = interventions_df["response_type"].value_counts()
        fig.add_trace(
            go.Pie(
                labels=response_counts.index,
                values=response_counts.values,
                name="Response Types",
            ),
            row=1,
            col=1,
        )

        # Priority queue visualization
        queue_data = interventions_df.sort_values(
            "priority_queue_position", ascending=False
        )
        fig.add_trace(
            go.Bar(
                x=list(range(len(queue_data))),
                y=queue_data["priority_queue_position"],
                name="Queue Position",
                marker_color="#FF6B6B",
            ),
            row=1,
            col=2,
        )

        # Target communities
        community_counts = interventions_df["target_community"].value_counts()
        fig.add_trace(
            go.Pie(
                labels=community_counts.index,
                values=community_counts.values,
                name="Target Communities",
            ),
            row=2,
            col=1,
        )

        # Resource categories
        resource_types = interventions_df["resource_needed"].value_counts()[:6]  # Top 6
        fig.add_trace(
            go.Bar(
                x=resource_types.values,
                y=resource_types.index,
                orientation="h",
                name="Resources Needed",
                marker_color="#4ECDC4",
            ),
            row=2,
            col=2,
        )

        fig.update_layout(
            height=800,
            title_text="Intervention Response Pipeline Dashboard",
            title_x=0.5,
        )

        return fig

    def generate_summary_report(self):
        """Generate text summary for the demo"""
        total_posts = len(self.posts_df)
        high_severity = len(self.posts_df[self.posts_df["severity_level"] >= 4])
        canadian_posts = len(
            self.posts_df[self.posts_df["canadian_probability"] >= 0.7]
        )

        # Most common health topics
        top_topics = self.posts_df["health_topic"].value_counts().head(3)

        # Network stats
        unique_users = len(
            set(self.interactions_df["source_user_id"]).union(
                set(self.interactions_df["target_user_id"])
            )
        )

        report = f"""
MISINFORMATION DETECTION PIPELINE - DEMO SUMMARY
=================================================

Dataset Overview:
• Total posts analyzed: {total_posts}
• High-severity misinformation detected: {high_severity} posts ({high_severity/total_posts*100:.1f}%)
• Canadian user posts (≥70% confidence): {canadian_posts} posts ({canadian_posts/total_posts*100:.1f}%)
• Unique users in network: {unique_users}
• Total user interactions tracked: {len(self.interactions_df)}

Top Health Discussion Topics:
1. {top_topics.index[0].replace('_', ' ')}: {top_topics.iloc[0]} posts
2. {top_topics.index[1].replace('_', ' ')}: {top_topics.iloc[1]} posts  
3. {top_topics.index[2].replace('_', ' ')}: {top_topics.iloc[2]} posts

Misinformation Severity Breakdown:
• Level 1-2 (Harmless misconceptions): {len(self.posts_df[self.posts_df['severity_level'] <= 2])} posts
• Level 3 (Moderate concern): {len(self.posts_df[self.posts_df['severity_level'] == 3])} posts
• Level 4-5 (Harmful/Dangerous): {len(self.posts_df[self.posts_df['severity_level'] >= 4])} posts

Intervention Pipeline Status:
• Posts requiring urgent intervention: {high_severity}
• Educational resources needed: {len(self.posts_df[(self.posts_df['severity_level'] == 3)])}
• Community alerts generated: {len(self.posts_df[self.posts_df['severity_level'] >= 4])}

Key Innovation: Severity Spectrum Classification
Instead of binary "misinformation/not misinformation," this system provides nuanced 
classification enabling appropriate responses - from gentle education for misconceptions 
to urgent intervention for dangerous misinformation.
"""

        return report


def generate_demo_visualizations():
    """Generate all demo visualizations"""
    # First generate the demo data
    from demo_data_generator import DemoDataGenerator

    generator = DemoDataGenerator()
    demo_data = generator.save_demo_data("demo_dataset")
    print("Demo data generated successfully!")

    # Create visualizations
    dashboard = DemoVisualizationDashboard("demo_dataset.json")

    # Generate all visualizations
    print("Creating queue status visualization...")
    queue_fig = dashboard.create_queue_status_visualization()
    queue_fig.write_html("demo_queue_dashboard.html")

    print("Creating severity spectrum analysis...")
    severity_fig = dashboard.create_severity_spectrum_analysis()
    severity_fig.savefig("demo_severity_analysis.png", dpi=300, bbox_inches="tight")

    print("Creating network analysis...")
    network_fig = dashboard.create_network_analysis_viz()
    network_fig.savefig("demo_network_analysis.png", dpi=300, bbox_inches="tight")

    print("Creating intervention pipeline...")
    intervention_fig = dashboard.create_intervention_pipeline_viz()
    intervention_fig.write_html("demo_intervention_pipeline.html")

    # Generate summary report
    report = dashboard.generate_summary_report()
    with open("demo_summary_report.txt", "w") as f:
        f.write(report)

    print("All demo materials created!")
    print("Files generated:")
    print("- demo_dataset.json (raw data)")
    print("- demo_queue_dashboard.html (interactive queue)")
    print("- demo_severity_analysis.png (severity spectrum)")
    print("- demo_network_analysis.png (social network)")
    print("- demo_intervention_pipeline.html (intervention responses)")
    print("- demo_summary_report.txt (executive summary)")

    return dashboard


if __name__ == "__main__":
    generate_demo_visualizations()
