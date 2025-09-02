"""
Demo Data Generator for Misinformation Detection Pipeline
Creates realistic sample data to demonstrate the full workflow and visualizations
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
import hashlib


class DemoDataGenerator:
    def __init__(self):
        self.canadian_subreddits = [
            "gaybros",
            "askgaybros",
            "toronto",
            "vancouver",
            "canada",
            "CanadaHealthcare",
            "montreal",
            "ontario",
            "britishcolumbia",
        ]

        self.health_topics = {
            "PrEP": [
                "prep",
                "truvada",
                "descovy",
                "hiv prevention",
                "pre-exposure prophylaxis",
            ],
            "STI_testing": [
                "std test",
                "sti test",
                "sexual health clinic",
                "gonorrhea",
                "chlamydia",
            ],
            "HIV_treatment": [
                "hiv medication",
                "viral load",
                "cd4",
                "antiretroviral",
                "undetectable",
            ],
            "Mental_health": [
                "depression",
                "anxiety",
                "therapy",
                "mental health",
                "suicide",
            ],
            "General_health": [
                "doctor",
                "clinic",
                "healthcare",
                "insurance",
                "prescription",
            ],
        }

        self.misinformation_examples = [
            {
                "content": "I heard PrEP makes you infertile and damages your kidneys permanently. My friend's doctor in Toronto told him to avoid it.",
                "severity": 4,
                "type": "harmful",
                "topic": "PrEP",
                "canadian_markers": ["Toronto", "doctor"],
                "harm_potential": "high",
            },
            {
                "content": "You can't get HIV if you're a top, that's just basic biology. Don't let them scare you into taking expensive drugs.",
                "severity": 5,
                "type": "malicious",
                "topic": "HIV_prevention",
                "canadian_markers": [],
                "harm_potential": "critical",
            },
            {
                "content": "I think you need to wait 6 months between STI tests? That's what I read somewhere but not sure if it's different in Canada.",
                "severity": 2,
                "type": "misconception",
                "topic": "STI_testing",
                "canadian_markers": ["Canada"],
                "harm_potential": "low",
            },
            {
                "content": "PrEP is only covered by OHIP if you're already HIV positive, which makes no sense but that's what the clinic told me.",
                "severity": 3,
                "type": "misconception",
                "topic": "PrEP",
                "canadian_markers": ["OHIP", "clinic"],
                "harm_potential": "medium",
            },
            {
                "content": "Honestly, condoms are 100% effective if you use them right. All this talk about PrEP is just Big Pharma trying to make money.",
                "severity": 3,
                "type": "harmful",
                "topic": "HIV_prevention",
                "canadian_markers": [],
                "harm_potential": "medium",
            },
            {
                "content": "Walk-in clinics in Vancouver don't do anonymous HIV testing anymore since COVID. You have to give your real name and address now.",
                "severity": 2,
                "type": "misconception",
                "topic": "HIV_testing",
                "canadian_markers": ["Vancouver", "walk-in clinics"],
                "harm_potential": "low",
            },
            {
                "content": "If your viral load is undetectable, you still need to use condoms because you can still transmit HIV. U=U is just a myth.",
                "severity": 4,
                "type": "harmful",
                "topic": "HIV_treatment",
                "canadian_markers": [],
                "harm_potential": "high",
            },
            {
                "content": "MSP in BC covers PrEP but only if you can prove you're high-risk. They make you fill out this embarrassing questionnaire about your sex life.",
                "severity": 2,
                "type": "misconception",
                "topic": "PrEP",
                "canadian_markers": ["MSP", "BC"],
                "harm_potential": "low",
            },
            {
                "content": "You can cure gonorrhea with cranberry juice and probiotics. Antibiotics just make it worse and destroy your gut health.",
                "severity": 5,
                "type": "malicious",
                "topic": "STI_treatment",
                "canadian_markers": [],
                "harm_potential": "critical",
            },
            {
                "content": "The new rapid HIV tests they use at Pride events aren't accurate. They give tons of false positives to scare people.",
                "severity": 3,
                "type": "harmful",
                "topic": "HIV_testing",
                "canadian_markers": ["Pride events"],
                "harm_potential": "medium",
            },
        ]

    def generate_study_user_id(self, username: str) -> str:
        """Generate hashed study user ID"""
        # Simulate the username + unique identifier hashing
        unique_data = f"{username}_created_2023"
        return f"USER_{hashlib.md5(unique_data.encode()).hexdigest()[:8].upper()}"

    def generate_demo_posts(self, num_posts: int = 10) -> List[Dict]:
        """Generate realistic demo posts for the queue"""
        posts = []

        for i in range(num_posts):
            # Select misinformation example
            misinfo = random.choice(self.misinformation_examples)

            # Generate post data
            post = {
                "post_id": f"demo_{i+1:03d}_{random.randint(1000, 9999)}",
                "subreddit": random.choice(self.canadian_subreddits),
                "title": f"Question about {misinfo['topic'].replace('_', ' ')}",
                "selftext": misinfo["content"],
                "author": f"throwaway_{random.randint(100, 999)}",
                "created_utc": datetime.now() - timedelta(days=random.randint(1, 30)),
                "score": random.randint(-5, 50),
                "upvote_ratio": random.uniform(0.3, 0.9),
                "num_comments": random.randint(0, 25),
                "language": "en",
                # Canadian proxy data
                "canadian_probability": (
                    0.8 if misinfo["canadian_markers"] else random.uniform(0.2, 0.6)
                ),
                "healthcare_references": len(misinfo["canadian_markers"]),
                "canadian_spelling_score": (
                    random.uniform(0.3, 0.9)
                    if misinfo["canadian_markers"]
                    else random.uniform(0.0, 0.3)
                ),
                # Misinformation classification
                "severity_level": misinfo["severity"],
                "misinformation_type": misinfo["type"],
                "harm_potential": misinfo["harm_potential"],
                "health_topic": misinfo["topic"],
                "contains_health_keywords": True,
                # Study user ID
                "study_user_id": self.generate_study_user_id(
                    f"throwaway_{random.randint(100, 999)}"
                ),
                # Queue status
                "queue_status": random.choice(
                    ["pending", "in_review", "annotated", "flagged"]
                ),
                "priority_score": misinfo["severity"]
                + (1 if misinfo["canadian_markers"] else 0),
                "added_to_queue": datetime.now()
                - timedelta(hours=random.randint(1, 48)),
            }

            posts.append(post)

        # Sort by priority for demo queue
        posts.sort(key=lambda x: x["priority_score"], reverse=True)

        return posts

    def generate_annotation_data(self, posts: List[Dict]) -> List[Dict]:
        """Generate annotation data for demo posts"""
        annotations = []
        annotators = ["researcher_001", "researcher_002", "expert_003", "community_004"]

        for post in posts:
            # Some posts have multiple annotations
            num_annotations = (
                random.randint(1, 3) if post["queue_status"] == "annotated" else 0
            )

            for j in range(num_annotations):
                annotation = {
                    "post_id": post["post_id"],
                    "annotator": random.choice(annotators),
                    "category": (
                        "Misinformation"
                        if post["severity_level"] >= 3
                        else "Misconception"
                    ),
                    "confidence": random.randint(3, 5),
                    "severity_level": post["severity_level"]
                    + random.randint(-1, 1),  # Some disagreement
                    "misinformation_type": post["misinformation_type"],
                    "harm_potential": post["harm_potential"],
                    "target_community": (
                        "newcomers"
                        if "clinic" in post["selftext"].lower()
                        else "general"
                    ),
                    "intervention_priority": (
                        "urgent" if post["severity_level"] >= 4 else "medium"
                    ),
                    "timestamp": post["added_to_queue"]
                    + timedelta(hours=random.randint(1, 12)),
                }
                annotations.append(annotation)

        return annotations

    def generate_network_interactions(self, posts: List[Dict]) -> List[Dict]:
        """Generate user interaction data for network analysis"""
        interactions = []
        user_ids = list(set(post["study_user_id"] for post in posts))

        # Generate realistic interaction patterns
        for i in range(len(user_ids) * 2):  # Each user interacts ~2 times
            source = random.choice(user_ids)
            target = random.choice([uid for uid in user_ids if uid != source])
            post = random.choice(posts)

            interaction = {
                "source_user_id": source,
                "target_user_id": target,
                "interaction_type": random.choice(
                    ["reply", "mention", "thread_participation"]
                ),
                "post_id": post["post_id"],
                "interaction_timestamp": post["created_utc"]
                + timedelta(hours=random.randint(1, 24)),
                "subreddit_context": post["subreddit"],
                "is_misinformation_related": post["severity_level"] >= 3,
            }
            interactions.append(interaction)

        return interactions

    def save_demo_data(self, filename_prefix: str = "demo_data"):
        """Generate and save all demo data"""
        posts = self.generate_demo_posts(12)  # Good number for visualizations
        annotations = self.generate_annotation_data(posts)
        interactions = self.generate_network_interactions(posts)

        # Save to JSON files for easy loading
        demo_data = {
            "posts": posts,
            "annotations": annotations,
            "interactions": interactions,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_posts": len(posts),
                "total_annotations": len(annotations),
                "total_interactions": len(interactions),
            },
        }

        with open(f"{filename_prefix}.json", "w") as f:
            json.dump(demo_data, f, indent=2, default=str)

        return demo_data


if __name__ == "__main__":
    generator = DemoDataGenerator()
    demo_data = generator.save_demo_data("demo_dataset")

    print("Generated demo dataset:")
    print(f"- {len(demo_data['posts'])} posts")
    print(f"- {len(demo_data['annotations'])} annotations")
    print(f"- {len(demo_data['interactions'])} interactions")
    print("\nQueue Preview:")
    for i, post in enumerate(demo_data["posts"][:5]):
        print(
            f"{i+1}. [{post['queue_status'].upper()}] Severity: {post['severity_level']}/5 - {post['health_topic']}"
        )
        print(
            f"   Canadian markers: {post['canadian_probability']:.1f} - {post['subreddit']}"
        )
        print(f"   Content preview: {post['selftext'][:80]}...")
        print()
