"""
Network analysis module for health misinformation research
"""

import networkx as nx
import pandas as pd
from typing import List, Dict, Optional
import json
from datetime import datetime
import plotly.graph_objects as go
from loguru import logger
from src.data_persistence import DataPersistenceManager
from src.database_models import RedditPost, RedditComment


class MisinformationNetwork:
    """Handles network analysis of Reddit conversations"""

    def __init__(self):
        self.graph = nx.DiGraph()  # Directed graph for reply relationships
        self.posts_df = None
        self.comments_df = None

    def load_data(self, data_path: str) -> None:
        """Load Reddit data from JSON file"""
        with open(data_path, "r") as f:
            raw_data = json.load(f)

        # Flatten posts and comments into separate dataframes
        posts = []
        comments = []

        for post in raw_data:
            posts.append(
                {
                    "post_id": post["post_id"],
                    "subreddit": post["subreddit"],
                    "author": post["author"],
                    "title": post["title"],
                    "selftext": post["selftext"],
                    "created_utc": post["created_utc"],
                    "score": post["score"],
                    "num_comments": post["num_comments"],
                    "language": post["language"],
                    "is_newcomer_related": post["is_newcomer_related"],
                }
            )

            # Extract comments
            for comment in post.get("comments", []):
                comment["post_id"] = post["post_id"]
                comment["subreddit"] = post["subreddit"]
                comments.append(comment)

        self.posts_df = pd.DataFrame(posts)
        self.comments_df = pd.DataFrame(comments)

        logger.info(f"Loaded {len(posts)} posts and {len(comments)} comments")


class NetworkAnalyzer:
    """Enhanced network analyzer for research-grade analysis"""

    def __init__(self):
        self.db_manager = DataPersistenceManager()
        self.graph = nx.DiGraph()

    def build_user_network(self, subreddit_filter: Optional[str] = None) -> Dict:
        """Build user interaction network from database"""
        with self.db_manager.get_session() as session:
            # Load posts and comments
            posts_query = session.query(RedditPost)
            if subreddit_filter:
                posts_query = posts_query.filter(
                    RedditPost.subreddit == subreddit_filter
                )
            posts = posts_query.all()

            comments_query = session.query(RedditComment)
            if subreddit_filter:
                # Join with posts to filter comments by subreddit
                comments_query = comments_query.join(
                    RedditPost, RedditComment.post_id == RedditPost.post_id
                ).filter(RedditPost.subreddit == subreddit_filter)
            comments = comments_query.all()

            if not posts and not comments:
                return {"nodes": [], "edges": []}

            # Build graph
            self.graph.clear()

            # Add nodes for users
            users = set()
            post_authors = {post.post_id: post.author for post in posts if post.author}

            for post in posts:
                if post.author and post.author != "[deleted]":
                    users.add(post.author)

            for comment in comments:
                if comment.author and comment.author != "[deleted]":
                    users.add(comment.author)

            self.graph.add_nodes_from(users)

            # Add edges for interactions
            for comment in comments:
                if not comment.author or comment.author == "[deleted]":
                    continue

                post_author = post_authors.get(comment.post_id)
                if (
                    post_author
                    and post_author != "[deleted]"
                    and post_author != comment.author
                ):
                    if self.graph.has_edge(comment.author, post_author):
                        self.graph[comment.author][post_author]["weight"] += 1
                    else:
                        self.graph.add_edge(comment.author, post_author, weight=1)

            # Convert to visualization format
            return self._graph_to_vis_data()

    def _graph_to_vis_data(self) -> Dict:
        """Convert NetworkX graph to visualization data"""
        if not self.graph.nodes():
            return {"nodes": [], "edges": []}

        # Calculate layout using spring algorithm
        pos = nx.spring_layout(self.graph, k=1, iterations=50)

        # Calculate centrality measures
        try:
            centrality = nx.degree_centrality(self.graph)
            betweenness = nx.betweenness_centrality(self.graph)
        except:
            centrality = {node: 0 for node in self.graph.nodes()}
            betweenness = {node: 0 for node in self.graph.nodes()}

        # Create nodes data
        nodes = []
        for node in self.graph.nodes():
            x, y = pos[node]
            size = max(10, centrality.get(node, 0) * 100)

            nodes.append(
                {
                    "id": node,
                    "x": float(x),
                    "y": float(y),
                    "size": float(size),
                    "centrality": float(centrality.get(node, 0)),
                    "betweenness": float(betweenness.get(node, 0)),
                }
            )

        # Create edges data
        edges = []
        for edge in self.graph.edges(data=True):
            source, target, data = edge
            if source in pos and target in pos:
                edges.append(
                    {
                        "source": source,
                        "target": target,
                        "weight": data.get("weight", 1),
                    }
                )

        return {"nodes": nodes, "edges": edges}

    def visualize_network(self, network_data: Dict) -> go.Figure:
        """Create interactive network visualization"""
        nodes = network_data.get("nodes", [])
        edges = network_data.get("edges", [])

        if not nodes:
            fig = go.Figure()
            fig.add_annotation(
                text="No network data to visualize",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
            )
            return fig

        # Create edge traces
        edge_x = []
        edge_y = []
        edge_info = []

        for edge in edges:
            source_node = next((n for n in nodes if n["id"] == edge["source"]), None)
            target_node = next((n for n in nodes if n["id"] == edge["target"]), None)

            if source_node and target_node:
                edge_x.extend([source_node["x"], target_node["x"], None])
                edge_y.extend([source_node["y"], target_node["y"], None])
                edge_info.append(
                    f"{edge['source']} → {edge['target']} (weight: {edge['weight']})"
                )

        edge_trace = go.Scatter(
            x=edge_x,
            y=edge_y,
            line=dict(width=0.5, color="#888"),
            hoverinfo="none",
            mode="lines",
        )

        # Create node trace
        node_x = [node["x"] for node in nodes]
        node_y = [node["y"] for node in nodes]
        node_text = [node["id"] for node in nodes]
        node_sizes = [max(5, node["size"]) for node in nodes]

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            hoverinfo="text",
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=node_sizes,
                color=[node["centrality"] for node in nodes],
                colorscale="YlOrRd",
                showscale=True,
                colorbar=dict(title="Centrality"),
                line=dict(width=2),
            ),
        )

        # Hover text
        node_hover_text = []
        for node in nodes:
            hover_text = f"User: {node['id']}<br>"
            hover_text += f"Centrality: {node['centrality']:.3f}<br>"
            hover_text += f"Betweenness: {node['betweenness']:.3f}"
            node_hover_text.append(hover_text)

        node_trace.hovertext = node_hover_text

        # Create figure
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=f"User Interaction Network ({len(nodes)} users, {len(edges)} interactions)",
                titlefont_size=16,
                showlegend=False,
                hovermode="closest",
                margin=dict(b=20, l=5, r=5, t=40),
                annotations=[
                    dict(
                        text="User network based on post-comment interactions",
                        showarrow=False,
                        xref="paper",
                        yref="paper",
                        x=0.005,
                        y=-0.002,
                        xanchor="left",
                        yanchor="bottom",
                        font=dict(color="#999", size=12),
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            ),
        )

        return fig

    def build_interaction_network(self) -> None:
        """Build network graph from user interactions"""

        # Add nodes for all users
        all_users = set()
        all_users.update(self.posts_df["author"].unique())
        all_users.update(self.comments_df["author"].unique())
        all_users.discard("[deleted]")  # Remove deleted users

        self.graph.add_nodes_from(all_users)

        # Add edges for post-comment relationships
        for _, comment in self.comments_df.iterrows():
            if comment["author"] == "[deleted]":
                continue

            # Find the post author
            post_author = self.posts_df[self.posts_df["post_id"] == comment["post_id"]][
                "author"
            ].iloc[0]

            if post_author != "[deleted]" and post_author != comment["author"]:
                # Add edge from commenter to post author
                if self.graph.has_edge(comment["author"], post_author):
                    self.graph[comment["author"]][post_author]["weight"] += 1
                else:
                    self.graph.add_edge(
                        comment["author"],
                        post_author,
                        weight=1,
                        interaction_type="comment_to_post",
                    )

        # Add edges for comment-reply relationships
        for _, comment in self.comments_df.iterrows():
            parent_id = comment.get("parent_id", "")
            if parent_id.startswith("t1_"):  # Comment reply
                parent_comment_id = parent_id[3:]  # Remove 't1_' prefix

                parent_comment = self.comments_df[
                    self.comments_df["comment_id"] == parent_comment_id
                ]

                if not parent_comment.empty:
                    parent_author = parent_comment["author"].iloc[0]
                    if (
                        parent_author != "[deleted]"
                        and parent_author != comment["author"]
                    ):

                        if self.graph.has_edge(comment["author"], parent_author):
                            self.graph[comment["author"]][parent_author]["weight"] += 1
                        else:
                            self.graph.add_edge(
                                comment["author"],
                                parent_author,
                                weight=1,
                                interaction_type="reply",
                            )

        logger.info(
            f"Built network with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges"
        )

    def calculate_network_metrics(self) -> Dict:
        """Calculate key network metrics"""
        metrics = {}

        # Basic network statistics
        metrics["num_nodes"] = self.graph.number_of_nodes()
        metrics["num_edges"] = self.graph.number_of_edges()
        metrics["density"] = nx.density(self.graph)

        # Centrality measures
        degree_centrality = nx.degree_centrality(self.graph)
        betweenness_centrality = nx.betweenness_centrality(self.graph)
        eigenvector_centrality = nx.eigenvector_centrality(self.graph, max_iter=1000)

        # Top influential users
        metrics["top_degree_users"] = sorted(
            degree_centrality.items(), key=lambda x: x[1], reverse=True
        )[:10]

        metrics["top_betweenness_users"] = sorted(
            betweenness_centrality.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Community detection
        communities = nx.community.greedy_modularity_communities(
            self.graph.to_undirected()
        )
        metrics["num_communities"] = len(communities)
        metrics["largest_community_size"] = (
            max(len(c) for c in communities) if communities else 0
        )

        return metrics

    def identify_misinformation_spreaders(
        self, misinformation_posts: List[str]
    ) -> List[Dict]:
        """Identify users who frequently post misinformation"""

        # Get authors of misinformation posts
        misinfo_authors = self.posts_df[
            self.posts_df["post_id"].isin(misinformation_posts)
        ]["author"].value_counts()

        spreaders = []
        for author, count in misinfo_authors.items():
            if author in self.graph.nodes:
                degree_cent = nx.degree_centrality(self.graph)[author]
                betweenness_cent = nx.betweenness_centrality(self.graph)[author]

                spreaders.append(
                    {
                        "author": author,
                        "misinformation_posts": count,
                        "degree_centrality": degree_cent,
                        "betweenness_centrality": betweenness_cent,
                        "influence_score": count
                        * degree_cent
                        * 10,  # Custom influence metric
                    }
                )

        return sorted(spreaders, key=lambda x: x["influence_score"], reverse=True)

    def visualize_network(self, highlight_users: List[str] = None) -> go.Figure:
        """Create interactive network visualization"""

        # Calculate layout
        pos = nx.spring_layout(self.graph, k=1, iterations=50)

        # Extract node and edge information
        node_x = [pos[node][0] for node in self.graph.nodes()]
        node_y = [pos[node][1] for node in self.graph.nodes()]
        node_text = list(self.graph.nodes())

        # Color nodes based on whether they're highlighted
        node_colors = []
        for node in self.graph.nodes():
            if highlight_users and node in highlight_users:
                node_colors.append("red")  # Highlight misinformation spreaders
            else:
                node_colors.append("lightblue")

        # Create edge traces
        edge_x = []
        edge_y = []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        # Create the plot
        fig = go.Figure()

        # Add edges
        fig.add_trace(
            go.Scatter(
                x=edge_x,
                y=edge_y,
                line=dict(width=0.5, color="gray"),
                hoverinfo="none",
                mode="lines",
                name="Interactions",
            )
        )

        # Add nodes
        fig.add_trace(
            go.Scatter(
                x=node_x,
                y=node_y,
                mode="markers+text",
                hoverinfo="text",
                text=node_text,
                textposition="middle center",
                marker=dict(
                    size=10, color=node_colors, line=dict(width=2, color="black")
                ),
                name="Users",
            )
        )

        fig.update_layout(
            title="Reddit Health Discussion Network",
            showlegend=False,
            hovermode="closest",
            margin=dict(b=20, l=5, r=5, t=40),
            annotations=[
                dict(
                    text="Red nodes: Potential misinformation spreaders",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.005,
                    y=-0.002,
                    xanchor="left",
                    yanchor="bottom",
                    font=dict(size=12),
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        )

        return fig

    def generate_network_report(self) -> Dict:
        """Generate comprehensive network analysis report"""

        metrics = self.calculate_network_metrics()

        # Language distribution
        language_dist = self.posts_df["language"].value_counts().to_dict()

        # Newcomer-related content analysis
        newcomer_posts = self.posts_df[self.posts_df["is_newcomer_related"] == True]

        # Subreddit activity
        subreddit_activity = self.posts_df["subreddit"].value_counts().to_dict()

        report = {
            "collection_date": datetime.now().isoformat(),
            "total_posts": len(self.posts_df),
            "total_comments": len(self.comments_df),
            "network_metrics": metrics,
            "language_distribution": language_dist,
            "newcomer_related_posts": len(newcomer_posts),
            "subreddit_activity": subreddit_activity,
            "multilingual_posts": len(
                self.posts_df[
                    self.posts_df["language"].isin(ResearchConfig.TARGET_LANGUAGES)
                ]
            ),
        }

        return report


if __name__ == "__main__":
    # Example usage
    scraper = RedditScraper()

    # Test with a single subreddit first
    test_data = scraper.scrape_subreddit("askgaybros", limit=50)
    print(f"Test collection: {len(test_data)} posts")
