#!/usr/bin/env python3
"""
Launcher script for Health Misinformation Research Tools
Provides options to launch either the annotation interface or analytics dashboard
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))


def main():
    parser = argparse.ArgumentParser(
        description="Launch Health Misinformation Research Tools"
    )
    parser.add_argument(
        "--mode",
        choices=["annotation", "analytics", "both"],
        default="analytics",
        help="Choose which interface to launch (default: analytics)",
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create a public shareable link (requires internet)",
    )

    args = parser.parse_args()

    if args.mode == "annotation":
        print("🏥 Launching Enhanced Annotation Interface...")
        from gradio_app.enhanced_annotation_interface import EnhancedAnnotationInterface

        interface = EnhancedAnnotationInterface()
        interface.launch(share=args.share)

    elif args.mode == "analytics":
        print("📊 Launching Analytics Dashboard...")
        from gradio_app.analytics_dashboard_interface import AnalyticsDashboardInterface

        dashboard = AnalyticsDashboardInterface()
        dashboard.launch(share=args.share)

    elif args.mode == "both":
        print("🚀 Launching both interfaces...")
        print("Note: This will open both annotation interface and analytics dashboard")
        print(
            "Analytics Dashboard will be on port 7862, Annotation Interface on port 7860"
        )

        # Launch analytics dashboard in background
        import threading
        from gradio_app.analytics_dashboard_interface import AnalyticsDashboardInterface
        from gradio_app.enhanced_annotation_interface import EnhancedAnnotationInterface

        def launch_analytics():
            dashboard = AnalyticsDashboardInterface()
            dashboard.launch(share=args.share)

        def launch_annotation():
            interface = EnhancedAnnotationInterface()
            interface.launch(share=args.share)

        analytics_thread = threading.Thread(target=launch_analytics, daemon=True)
        analytics_thread.start()

        # Launch annotation interface in main thread
        launch_annotation()


if __name__ == "__main__":
    main()
