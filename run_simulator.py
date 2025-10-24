"""
Launch script for NoC Simulator GUI
Run this file to start the application
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import from src package
from src.gui.main_window import main

if __name__ == "__main__":
    print("=" * 60)
    print("Starting Network-on-Chip Simulator")
    print("=" * 60)
    print("\nLoading GUI...")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulator closed by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
