#!/usr/bin/env python3
"""
Scraping Task Manager - Track what's been done and what's pending
"""

import json
from pathlib import Path
from datetime import datetime


class ScrapingTaskManager:
    def __init__(self, task_file="data/scraping_tasks.json"):
        self.task_file = Path(task_file)
        self.task_file.parent.mkdir(parents=True, exist_ok=True)
        self.tasks = self._load_tasks()

    def _load_tasks(self):
        """Load existing tasks"""
        if self.task_file.exists():
            try:
                with open(self.task_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Could not load task file: {e}")
                return self._get_default_tasks()
        return self._get_default_tasks()

    def _get_default_tasks(self):
        """Get default task structure"""
        return {
            "collections": {
                "multilingual_data_collection": {
                    "status": "in_progress",
                    "last_run": "2025-09-04T16:35:26",
                    "description": "Collect multilingual health data from diverse communities",
                    "frequency": "weekly",
                    "next_run": "2025-09-11",
                },
                "enhanced_data_collection": {
                    "status": "pending",
                    "last_run": None,
                    "description": "Run enhanced systematic data collection",
                    "frequency": "daily",
                    "next_run": None,
                },
                "targeted_health_collection": {
                    "status": "pending",
                    "last_run": None,
                    "description": "Targeted collection from health-focused subreddits",
                    "frequency": "weekly",
                    "next_run": None,
                },
            },
            "analysis": {
                "generate_visualizations": {
                    "status": "pending",
                    "last_run": None,
                    "description": "Generate data visualizations",
                    "frequency": "after_collection",
                    "next_run": None,
                },
                "run_annotation_tool": {
                    "status": "pending",
                    "last_run": None,
                    "description": "Launch annotation tool for data labeling",
                    "frequency": "after_collection",
                    "next_run": None,
                },
            },
            "maintenance": {
                "database_cleanup": {
                    "status": "pending",
                    "last_run": None,
                    "description": "Clean up duplicate posts and optimize database",
                    "frequency": "monthly",
                    "next_run": None,
                },
                "translation_cache_maintenance": {
                    "status": "pending",
                    "last_run": None,
                    "description": "Clean and optimize translation cache",
                    "frequency": "weekly",
                    "next_run": None,
                },
            },
        }

    def update_task_status(self, category, task_name, status, run_time=None):
        """Update task status"""
        if category in self.tasks and task_name in self.tasks[category]:
            self.tasks[category][task_name]["status"] = status
            self.tasks[category][task_name]["last_run"] = (
                run_time or datetime.now().isoformat()
            )

            # Calculate next run based on frequency
            frequency = self.tasks[category][task_name]["frequency"]
            if frequency == "daily":
                next_run = datetime.now().replace(day=datetime.now().day + 1)
                self.tasks[category][task_name]["next_run"] = next_run.isoformat()
            elif frequency == "weekly":
                next_run = datetime.now().replace(day=datetime.now().day + 7)
                self.tasks[category][task_name]["next_run"] = next_run.isoformat()
            elif frequency == "monthly":
                next_run = datetime.now().replace(month=datetime.now().month + 1)
                self.tasks[category][task_name]["next_run"] = next_run.isoformat()

    def get_pending_tasks(self):
        """Get all pending tasks"""
        pending = []
        for category, tasks in self.tasks.items():
            for task_name, task_info in tasks.items():
                if task_info["status"] == "pending":
                    pending.append(
                        {
                            "category": category,
                            "task": task_name,
                            "description": task_info["description"],
                            "frequency": task_info["frequency"],
                        }
                    )
        return pending

    def get_completed_tasks(self):
        """Get all completed tasks"""
        completed = []
        for category, tasks in self.tasks.items():
            for task_name, task_info in tasks.items():
                if task_info["status"] == "completed":
                    completed.append(
                        {
                            "category": category,
                            "task": task_name,
                            "description": task_info["description"],
                            "last_run": task_info["last_run"],
                        }
                    )
        return completed

    def get_overdue_tasks(self):
        """Get overdue tasks"""
        overdue = []
        now = datetime.now()
        for category, tasks in self.tasks.items():
            for task_name, task_info in tasks.items():
                if task_info["next_run"]:
                    next_run = datetime.fromisoformat(task_info["next_run"])
                    if next_run < now and task_info["status"] != "completed":
                        overdue.append(
                            {
                                "category": category,
                                "task": task_name,
                                "description": task_info["description"],
                                "next_run": task_info["next_run"],
                            }
                        )
        return overdue

    def save_tasks(self):
        """Save tasks to file"""
        try:
            with open(self.task_file, "w") as f:
                json.dump(self.tasks, f, indent=2)
        except Exception as e:
            print(f"Could not save task file: {e}")

    def print_task_summary(self):
        """Print task summary"""
        print("📋 Scraping Task Summary")
        print("=" * 50)

        # Print task status by category
        for category, tasks in self.tasks.items():
            print(f"\n{category.upper()}:")
            for task_name, task_info in tasks.items():
                status_icon = {
                    "completed": "✅",
                    "in_progress": "🔄",
                    "pending": "⏳",
                }.get(task_info["status"], "❓")

                print(f"  {status_icon} {task_name}")
                print(f"     Description: {task_info['description']}")
                print(f"     Status: {task_info['status']}")
                if task_info["last_run"]:
                    print(f"     Last run: {task_info['last_run']}")
                if task_info["next_run"]:
                    print(f"     Next run: {task_info['next_run']}")
                print()

        # Print quick stats
        total_tasks = sum(len(tasks) for tasks in self.tasks.values())
        completed_tasks = len(self.get_completed_tasks())
        pending_tasks = len(self.get_pending_tasks())
        overdue_tasks = len(self.get_overdue_tasks())

        print(f"📊 Task Statistics:")
        print(f"  Total tasks: {total_tasks}")
        print(f"  Completed: {completed_tasks}")
        print(f"  Pending: {pending_tasks}")
        print(f"  Overdue: {overdue_tasks}")


def main():
    manager = ScrapingTaskManager()
    manager.print_task_summary()


if __name__ == "__main__":
    main()
