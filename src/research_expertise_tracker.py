"""
Research Expertise Tracker for Community Resilience Analysis
Tracks and develops researcher expertise in different aspects of community resilience
"""

import json
import sqlite3
from typing import Dict, List
from datetime import datetime
from collections import defaultdict
from loguru import logger


class ResearchExpertiseTracker:
    """
    Tracks researcher expertise development in community resilience analysis
    """

    def __init__(self, db_path: str = "data/research_expertise.db"):
        self.db_path = db_path
        self.init_database()

        # Define expertise domains for community resilience research
        self.expertise_domains = {
            # Core resilience analysis
            "peer_support_analysis": {
                "name": "Peer Support Pattern Analysis",
                "description": "Identifying and analyzing mutual aid networks",
                "skills": [
                    "network mapping",
                    "support classification",
                    "interaction analysis",
                ],
            },
            "knowledge_broker_identification": {
                "name": "Knowledge Broker Research",
                "description": "Finding and analyzing community knowledge leaders",
                "skills": [
                    "influence mapping",
                    "expertise assessment",
                    "community leadership",
                ],
            },
            "cultural_bridging_analysis": {
                "name": "Cultural Adaptation Research",
                "description": "Understanding cross-cultural health information adaptation",
                "skills": [
                    "cultural competency",
                    "adaptation patterns",
                    "bridging mechanisms",
                ],
            },
            "health_info_quality": {
                "name": "Health Information Quality Assessment",
                "description": "Evaluating helpfulness and accuracy of community-shared health info",
                "skills": [
                    "quality metrics",
                    "helpfulness scoring",
                    "resource evaluation",
                ],
            },
            # Community-specific expertise
            "lgbtq_health_communities": {
                "name": "LGBTQ+ Health Community Analysis",
                "description": "Specialized analysis of gay men's health communities",
                "skills": [
                    "LGBTQ+ health literacy",
                    "community norms",
                    "stigma analysis",
                ],
            },
            "newcomer_communities": {
                "name": "Newcomer Community Resilience",
                "description": "Understanding immigrant/refugee health community dynamics",
                "skills": [
                    "cultural adaptation",
                    "integration patterns",
                    "resource navigation",
                ],
            },
            "multilingual_analysis": {
                "name": "Multilingual Community Analysis",
                "description": "Cross-language community resilience patterns",
                "skills": [
                    "language barrier analysis",
                    "translation patterns",
                    "code-switching",
                ],
            },
            # Technical research skills
            "network_analysis": {
                "name": "Social Network Analysis",
                "description": "Technical network analysis and visualization",
                "skills": ["NetworkX", "centrality measures", "community detection"],
            },
            "qualitative_analysis": {
                "name": "Qualitative Data Analysis",
                "description": "Deep qualitative analysis of community interactions",
                "skills": [
                    "thematic analysis",
                    "grounded theory",
                    "narrative analysis",
                ],
            },
            "community_engagement": {
                "name": "Community-Based Participatory Research",
                "description": "Engaging communities as research partners",
                "skills": [
                    "participatory methods",
                    "community partnership",
                    "ethical engagement",
                ],
            },
        }

        # Expertise levels
        self.expertise_levels = {
            0: "Novice",
            1: "Developing",
            2: "Competent",
            3: "Proficient",
            4: "Expert",
        }

    def init_database(self):
        """Initialize expertise tracking database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Researcher expertise profiles
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS researcher_expertise (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                researcher_id TEXT NOT NULL,
                researcher_name TEXT,
                expertise_domains TEXT DEFAULT "{}",  -- JSON of domain -> level mapping
                analysis_history TEXT DEFAULT "[]",   -- JSON of analysis activities
                specializations TEXT DEFAULT "[]",    -- JSON of specialized focus areas
                collaboration_pattern TEXT DEFAULT "{}",  -- JSON of collaboration preferences
                research_goals TEXT,                  -- Current research objectives
                last_updated TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Research activity tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                researcher_id TEXT NOT NULL,
                activity_type TEXT NOT NULL,  -- analysis_completed, insight_generated, etc.
                expertise_domain TEXT NOT NULL,
                activity_description TEXT,
                quality_score REAL DEFAULT 0.0,
                impact_score REAL DEFAULT 0.0,
                community_focus TEXT,         -- Which community was analyzed
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Research team composition tracking
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS research_teams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                research_focus TEXT NOT NULL,
                team_members TEXT DEFAULT "[]",  -- JSON of researcher IDs
                expertise_coverage TEXT DEFAULT "{}",  -- JSON of covered domains
                team_strengths TEXT DEFAULT "[]",
                team_gaps TEXT DEFAULT "[]",
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        conn.commit()
        conn.close()

    def track_research_activity(
        self,
        researcher_id: str,
        activity_type: str,
        expertise_domain: str,
        description: str = "",
        quality_score: float = 0.0,
        community_focus: str = "",
    ):
        """Track a research activity to build expertise"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Record the activity
        cursor.execute(
            """
            INSERT INTO research_activities 
            (researcher_id, activity_type, expertise_domain, activity_description, 
             quality_score, community_focus)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                researcher_id,
                activity_type,
                expertise_domain,
                description,
                quality_score,
                community_focus,
            ),
        )

        # Update researcher expertise level
        self._update_expertise_level(researcher_id, expertise_domain, cursor)

        conn.commit()
        conn.close()

        logger.info(
            f"Tracked activity: {researcher_id} - {activity_type} in {expertise_domain}"
        )

    def _update_expertise_level(self, researcher_id: str, domain: str, cursor):
        """Update expertise level based on activity history"""
        # Get activity count and quality for this domain
        cursor.execute(
            """
            SELECT COUNT(*), AVG(quality_score), MAX(quality_score)
            FROM research_activities 
            WHERE researcher_id = ? AND expertise_domain = ?
        """,
            (researcher_id, domain),
        )

        result = cursor.fetchone()
        activity_count, avg_quality, max_quality = result if result else (0, 0, 0)

        # Calculate expertise level (0-4 scale)
        expertise_level = 0
        if activity_count >= 1:
            expertise_level = 1  # Developing
        if activity_count >= 5 and avg_quality >= 0.6:
            expertise_level = 2  # Competent
        if activity_count >= 15 and avg_quality >= 0.7:
            expertise_level = 3  # Proficient
        if activity_count >= 30 and avg_quality >= 0.8 and max_quality >= 0.9:
            expertise_level = 4  # Expert

        # Update researcher expertise
        cursor.execute(
            """
            SELECT expertise_domains FROM researcher_expertise WHERE researcher_id = ?
        """,
            (researcher_id,),
        )

        result = cursor.fetchone()
        if result:
            # Update existing researcher
            current_expertise = json.loads(result[0]) if result[0] else {}
            current_expertise[domain] = expertise_level

            cursor.execute(
                """
                UPDATE researcher_expertise 
                SET expertise_domains = ?, last_updated = ?
                WHERE researcher_id = ?
            """,
                (
                    json.dumps(current_expertise),
                    datetime.now().isoformat(),
                    researcher_id,
                ),
            )
        else:
            # Create new researcher profile
            expertise_domains = {domain: expertise_level}
            cursor.execute(
                """
                INSERT INTO researcher_expertise 
                (researcher_id, expertise_domains, last_updated)
                VALUES (?, ?, ?)
            """,
                (
                    researcher_id,
                    json.dumps(expertise_domains),
                    datetime.now().isoformat(),
                ),
            )

    def get_researcher_profile(self, researcher_id: str) -> Dict:
        """Get comprehensive researcher expertise profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get basic profile
        cursor.execute(
            """
            SELECT researcher_name, expertise_domains, specializations, research_goals
            FROM researcher_expertise WHERE researcher_id = ?
        """,
            (researcher_id,),
        )

        result = cursor.fetchone()
        if not result:
            return {"error": "Researcher not found"}

        name, expertise_str, specializations_str, goals = result
        expertise_domains = json.loads(expertise_str) if expertise_str else {}
        specializations = json.loads(specializations_str) if specializations_str else []

        # Get recent activities
        cursor.execute(
            """
            SELECT activity_type, expertise_domain, activity_description, quality_score, 
                   community_focus, timestamp
            FROM research_activities 
            WHERE researcher_id = ? 
            ORDER BY timestamp DESC LIMIT 10
        """,
            (researcher_id,),
        )

        activities = cursor.fetchall()

        # Calculate overall expertise profile
        total_expertise = sum(expertise_domains.values())
        domain_count = len(expertise_domains)
        avg_expertise = total_expertise / domain_count if domain_count > 0 else 0

        # Identify strengths and development areas
        strengths = [
            domain for domain, level in expertise_domains.items() if level >= 3
        ]
        developing = [
            domain
            for domain, level in expertise_domains.items()
            if level == 1 or level == 2
        ]

        conn.close()

        return {
            "researcher_id": researcher_id,
            "name": name or researcher_id,
            "expertise_domains": expertise_domains,
            "specializations": specializations,
            "research_goals": goals,
            "recent_activities": activities,
            "overall_expertise": avg_expertise,
            "strengths": strengths,
            "developing_areas": developing,
            "expertise_summary": self._generate_expertise_summary(expertise_domains),
        }

    def _generate_expertise_summary(self, expertise_domains: Dict) -> str:
        """Generate human-readable expertise summary"""
        if not expertise_domains:
            return "New researcher - building expertise profile"

        summary_parts = []
        for domain, level in expertise_domains.items():
            if level >= 3:  # Proficient or Expert
                domain_name = self.expertise_domains.get(domain, {}).get("name", domain)
                level_name = self.expertise_levels.get(level, "Unknown")
                summary_parts.append(f"{level_name} in {domain_name}")

        if summary_parts:
            return "; ".join(summary_parts)
        else:
            return "Developing expertise across multiple domains"

    def recommend_research_focus(self, researcher_id: str) -> Dict:
        """Recommend research focus areas based on expertise and gaps"""
        profile = self.get_researcher_profile(researcher_id)
        if "error" in profile:
            return profile

        expertise_domains = profile["expertise_domains"]

        # Find domains to develop
        recommendations = {
            "continue_developing": [],
            "new_areas": [],
            "specialization_paths": [],
        }

        # Areas to continue developing (level 1-2)
        for domain, level in expertise_domains.items():
            if 1 <= level <= 2:
                domain_info = self.expertise_domains.get(domain, {})
                recommendations["continue_developing"].append(
                    {
                        "domain": domain,
                        "name": domain_info.get("name", domain),
                        "current_level": self.expertise_levels.get(level, "Unknown"),
                        "next_steps": f"Continue with {domain_info.get('name', domain)} to reach competency",
                    }
                )

        # Suggest new complementary areas
        current_domains = set(expertise_domains.keys())
        all_domains = set(self.expertise_domains.keys())
        new_domains = all_domains - current_domains

        for domain in list(new_domains)[:3]:  # Top 3 suggestions
            domain_info = self.expertise_domains.get(domain, {})
            recommendations["new_areas"].append(
                {
                    "domain": domain,
                    "name": domain_info.get("name", domain),
                    "description": domain_info.get("description", ""),
                    "rationale": f"Complements existing expertise in {', '.join(profile['strengths'])}",
                }
            )

        # Specialization paths for experts
        expert_domains = [d for d, l in expertise_domains.items() if l >= 3]
        if expert_domains:
            recommendations["specialization_paths"] = [
                f"Lead researcher in {self.expertise_domains.get(d, {}).get('name', d)}"
                for d in expert_domains
            ]

        return recommendations

    def suggest_research_team(
        self, research_focus: str, required_domains: List[str]
    ) -> Dict:
        """Suggest optimal research team composition"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all researchers with their expertise
        cursor.execute(
            """
            SELECT researcher_id, researcher_name, expertise_domains
            FROM researcher_expertise
        """
        )

        researchers = cursor.fetchall()
        conn.close()

        # Analyze expertise coverage
        team_suggestions = []
        domain_coverage = defaultdict(list)

        for researcher_id, name, expertise_str in researchers:
            expertise = json.loads(expertise_str) if expertise_str else {}

            # Check coverage of required domains
            covered_domains = []
            for domain in required_domains:
                if domain in expertise and expertise[domain] >= 2:  # Competent or above
                    covered_domains.append(domain)
                    domain_coverage[domain].append(
                        {
                            "researcher_id": researcher_id,
                            "name": name or researcher_id,
                            "level": expertise[domain],
                        }
                    )

            if covered_domains:
                team_suggestions.append(
                    {
                        "researcher_id": researcher_id,
                        "name": name or researcher_id,
                        "covered_domains": covered_domains,
                        "expertise_level": sum(
                            expertise.get(d, 0) for d in covered_domains
                        )
                        / len(covered_domains),
                    }
                )

        # Identify gaps
        uncovered_domains = [d for d in required_domains if not domain_coverage[d]]

        return {
            "research_focus": research_focus,
            "required_domains": required_domains,
            "team_suggestions": sorted(
                team_suggestions, key=lambda x: x["expertise_level"], reverse=True
            ),
            "domain_coverage": dict(domain_coverage),
            "expertise_gaps": uncovered_domains,
            "team_recommendations": self._generate_team_recommendations(
                domain_coverage, required_domains
            ),
        }

    def _generate_team_recommendations(
        self, domain_coverage: Dict, required_domains: List[str]
    ) -> List[str]:
        """Generate team composition recommendations"""
        recommendations = []

        # Check coverage completeness
        covered_count = sum(1 for d in required_domains if domain_coverage[d])
        coverage_rate = covered_count / len(required_domains) if required_domains else 0

        if coverage_rate >= 0.8:
            recommendations.append(
                "✅ Strong expertise coverage - ready for comprehensive analysis"
            )
        elif coverage_rate >= 0.6:
            recommendations.append(
                "⚠️ Good coverage but some gaps - consider training or collaboration"
            )
        else:
            recommendations.append(
                "🔍 Significant expertise gaps - recruit specialists or provide training"
            )

        # Domain-specific recommendations
        for domain in required_domains:
            if not domain_coverage[domain]:
                domain_name = self.expertise_domains.get(domain, {}).get("name", domain)
                recommendations.append(f"🎯 Need specialist in: {domain_name}")
            elif len(domain_coverage[domain]) == 1:
                recommendations.append(f"⚠️ Single point of expertise in: {domain}")

        return recommendations
