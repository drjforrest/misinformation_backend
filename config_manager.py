#!/usr/bin/env python3
"""
Configuration Manager - Easily modify scraping configurations
"""

import json
from pathlib import Path


class ConfigManager:
    def __init__(self, config_file="config/scraping_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self._load_config()

    def _load_config(self):
        """Load configuration from JSON file"""
        if self.config_file.exists():
            with open(self.config_file, "r") as f:
                return json.load(f)
        else:
            # Create default config
            default_config = {
                "multilingual_subreddits": [
                    "NewToCanada",
                    "ImmigrationCanada",
                    "immigrationlaw",
                    "PersonalFinanceCanada",
                    "toronto",
                    "vancouver",
                    "montreal",
                    "calgary",
                    "edmonton",
                    "askTO",
                    "vancouver4friends",
                    "HealthAnxiety",
                    "medical_advice",
                    "AskDocs",
                    "STD",
                    "std",
                    "HIV",
                    "sexualhealth",
                    "sexualhealthtalk",
                    "askgaybros",
                    "gaybros",
                    "lgbt",
                    "ainbow",
                    "gay_irl",
                    "torontogaybros",
                    "relationship_advice",
                    "TooAfraidToAsk",
                    "NoStupidQuestions",
                    "offmychest",
                    "CasualConversation",
                    "Philippines",
                    "canada",
                    "China",
                    "Chinese",
                    "italy",
                    "Spain",
                    "mexico",
                    "india",
                    "pakistan",
                ],
                "enhanced_subreddits": [
                    "askgaybros",
                    "gaybros",
                    "lgbt",
                    "toronto",
                    "NewToCanada",
                ],
                "health_keywords": {
                    "english": [
                        "HIV",
                        "PrEP",
                        "ARVs",
                        "syphilis",
                        "doxy",
                        "PEP",
                        "chlamydia",
                        "gonorrhoea",
                        "gonorrhea",
                        "the clap",
                        "burning",
                        "discharge",
                        "Truvada",
                        "Descovy",
                        "undetectable",
                        "viral load",
                        "CD4",
                    ],
                    "spanish": [
                        "VIH",
                        "PrEP",
                        "sífilis",
                        "clamidia",
                        "gonorrea",
                        "condón",
                        "salud sexual",
                    ],
                    "tagalog": [
                        "HIV",
                        "PrEP",
                        "silis",
                        "STD",
                        "kalusugang sekswal",
                        "proteksyon",
                    ],
                    "chinese": [
                        "艾滋病",
                        "HIV",
                        "梅毒",
                        "淋病",
                        "衣原体",
                        "性健康",
                        "安全套",
                    ],
                    "french": [
                        "VIH",
                        "PrEP",
                        "syphilis",
                        "chlamydia",
                        "gonorrhée",
                        "santé sexuelle",
                    ],
                    "punjabi": ["HIV", "ਏਚਆਈਵੀ", "ਸਿਫਿਲਿਸ", "ਸੈਕਸੁਅਲ ਸਿਹਤ"],
                },
            }
            self._save_config(default_config)
            return default_config

    def _save_config(self, config=None):
        """Save configuration to JSON file"""
        if config is None:
            config = self.config

        with open(self.config_file, "w") as f:
            json.dump(config, f, indent=2)

    def list_subreddits(self, category="multilingual_subreddits"):
        """List all subreddits in a category"""
        if category in self.config:
            return self.config[category]
        return []

    def add_subreddit(self, subreddit, category="multilingual_subreddits"):
        """Add a subreddit to a category"""
        if category not in self.config:
            self.config[category] = []

        if subreddit not in self.config[category]:
            self.config[category].append(subreddit)
            self._save_config()
            print(f"✅ Added r/{subreddit} to {category}")
            return True
        else:
            print(f"⚠️  r/{subreddit} already exists in {category}")
            return False

    def remove_subreddit(self, subreddit, category="multilingual_subreddits"):
        """Remove a subreddit from a category"""
        if category in self.config and subreddit in self.config[category]:
            self.config[category].remove(subreddit)
            self._save_config()
            print(f"✅ Removed r/{subreddit} from {category}")
            return True
        else:
            print(f"⚠️  r/{subreddit} not found in {category}")
            return False

    def search_subreddits(self, term):
        """Search for subreddits containing a term"""
        matches = []
        for category, subreddits in self.config.items():
            if isinstance(subreddits, list):
                for subreddit in subreddits:
                    if term.lower() in subreddit.lower():
                        matches.append((category, subreddit))
        return matches

    def update_keywords(self, language, keywords):
        """Update health keywords for a language"""
        if "health_keywords" not in self.config:
            self.config["health_keywords"] = {}

        self.config["health_keywords"][language] = keywords
        self._save_config()
        print(f"✅ Updated {language} health keywords")

    def print_config(self):
        """Print current configuration"""
        print("🔧 Current Configuration")
        print("=" * 40)

        for category, items in self.config.items():
            if isinstance(items, list):
                print(f"\n{category.upper()}:")
                for item in items:
                    print(f"  • {item}")
            elif isinstance(items, dict):
                print(f"\n{category.upper()}:")
                for lang, keywords in items.items():
                    print(f"  {lang}: {len(keywords)} keywords")


def main():
    manager = ConfigManager()

    while True:
        print("\n⚙️  Configuration Manager")
        print("=" * 30)
        print("1. List subreddits")
        print("2. Add subreddit")
        print("3. Remove subreddit")
        print("4. Search subreddits")
        print("5. View configuration")
        print("6. Exit")

        choice = input("\nSelect an option (1-6): ").strip()

        if choice == "1":
            category = (
                input("Category (default: multilingual_subreddits): ").strip()
                or "multilingual_subreddits"
            )
            subreddits = manager.list_subreddits(category)
            print(f"\n{category}:")
            for subreddit in subreddits:
                print(f"  • {subreddit}")

        elif choice == "2":
            subreddit = input("Subreddit name (e.g., 'health' without 'r/'): ").strip()
            category = (
                input("Category (default: multilingual_subreddits): ").strip()
                or "multilingual_subreddits"
            )
            manager.add_subreddit(subreddit, category)

        elif choice == "3":
            subreddit = input("Subreddit name (e.g., 'health' without 'r/'): ").strip()
            category = (
                input("Category (default: multilingual_subreddits): ").strip()
                or "multilingual_subreddits"
            )
            manager.remove_subreddit(subreddit, category)

        elif choice == "4":
            term = input("Search term: ").strip()
            matches = manager.search_subreddits(term)
            if matches:
                print(f"\nMatches for '{term}':")
                for category, subreddit in matches:
                    print(f"  • {subreddit} (in {category})")
            else:
                print(f"No matches found for '{term}'")

        elif choice == "5":
            manager.print_config()

        elif choice == "6":
            print("Goodbye!")
            break

        else:
            print("Invalid option. Please try again.")


if __name__ == "__main__":
    main()
