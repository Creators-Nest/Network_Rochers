"""Run the Mesh Topology web application."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from webapp.app import create_app

if __name__ == '__main__':
    app = create_app(width=6, height=6)
    print("\n" + "="*60)
    print("Starting Mesh Topology Web Visualizer")
    print("="*60)
    print("Navigate to: http://127.0.0.1:5000")
    print("Press Ctrl+C to quit")
    print("="*60 + "\n")
    app.run(debug=True, port=5000)
