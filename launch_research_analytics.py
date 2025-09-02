#!/usr/bin/env python3
"""
Launch script for the Research Analytics Interface
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from gradio_app.research_analytics_interface import launch_research_interface

if __name__ == "__main__":
    print("🔬 Launching Health Misinformation Research Analytics Platform...")
    print(
        "📊 This interface provides comprehensive investigational tools for research teams"
    )
    print("🌐 Access at: http://localhost:7861")
    print("")

    launch_research_interface()
