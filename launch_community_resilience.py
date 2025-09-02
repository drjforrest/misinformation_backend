#!/usr/bin/env python3
"""
Launch script for the Community Resilience Analysis Interface
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from gradio_app.community_resilience_interface import (
    launch_community_resilience_interface,
)

if __name__ == "__main__":
    print("🤝 Launching Community Resilience & Social Capital Analysis Platform...")
    print("🏥 This interface analyzes supportive digital health ecosystems")
    print("🌐 Access at: http://localhost:7862")
    print("")
    print("📊 Research Focus Areas:")
    print("  • Peer support patterns and social capital")
    print("  • Knowledge brokers and community influencers")
    print("  • Cultural adaptation of health information")
    print("  • Community resilience indicators")
    print("")

    launch_community_resilience_interface()
