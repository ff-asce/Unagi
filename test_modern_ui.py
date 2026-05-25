#!/usr/bin/env python3
"""Quick test of modern UI components."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.textual_app import UnagiApp

if __name__ == "__main__":
    print("Testing modern UI import and initialization...")
    try:
        app = UnagiApp()
        print("✓ UnagiApp initialized successfully")
        print("✓ All components loaded")
        print("\nTo run the full UI, use: python main.py")
        print("(Make sure config.yaml has ui.mode set to 'modern')")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
