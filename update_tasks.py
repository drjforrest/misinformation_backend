#!/usr/bin/env python3
"""
Update task manager with completed tasks and new tasks
"""

from task_manager import ScrapingTaskManager
from datetime import datetime


def update_tasks():
    """Update task statuses"""
    manager = ScrapingTaskManager()

    # Mark multilingual data collection as completed
    manager.update_task_status(
        "collections",
        "multilingual_data_collection",
        "completed",
        "2025-09-04T16:35:26",
    )

    # Add new tasks based on our analysis
    manager.tasks["collections"]["spanish_content_expansion"] = {
        "status": "pending",
        "last_run": None,
        "description": "Expand Spanish language content collection",
        "frequency": "weekly",
        "next_run": None,
    }

    manager.tasks["collections"]["tagalog_improvement"] = {
        "status": "pending",
        "last_run": None,
        "description": "Improve Tagalog translation quality and collection",
        "frequency": "weekly",
        "next_run": None,
    }

    manager.tasks["analysis"]["translation_quality_review"] = {
        "status": "pending",
        "last_run": None,
        "description": "Review and improve translation quality for technical terms",
        "frequency": "after_collection",
        "next_run": None,
    }

    manager.tasks["maintenance"]["progress_tracking_update"] = {
        "status": "completed",
        "last_run": datetime.now().isoformat(),
        "description": "Update progress tracking with latest collection data",
        "frequency": "after_collection",
        "next_run": None,
    }

    # Save updated tasks
    manager.save_tasks()

    print("✅ Task manager updated successfully!")
    manager.print_task_summary()


if __name__ == "__main__":
    update_tasks()
