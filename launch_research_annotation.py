#!/usr/bin/env python3
"""
Launch script for the Community Resilience Research Annotation Interface
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(__file__))

from gradio_app.enhanced_annotation_interface import EnhancedAnnotationInterface

if __name__ == "__main__":
    print("🔬 Launching Community Resilience Research Interface...")
    print("📊 This interface now tracks research expertise development")
    print("🤝 Focus: Analyzing supportive community interactions")
    print("🌐 Access at: http://localhost:7861")
    print("")
    print("🎯 Research Areas Tracked:")
    print("  • Peer Support Analysis")
    print("  • Knowledge Broker Identification")
    print("  • Cultural Bridging Analysis")
    print("  • Health Information Quality Assessment")
    print("  • Network Analysis")
    print("  • Community Engagement Research")
    print("")

    # Initialize interface with some sample data
    interface = EnhancedAnnotationInterface(limit=50)
    interface.launch(share=False)
