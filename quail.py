#!/usr/bin/env python3
"""
QuailTrail Direct Launcher
Use this script to run QuailTrail without installation

Usage:
  python quail.py --trail         # Run default pipeline
  python quail.py --nest          # Generate scaffold
  python quail.py --list          # List targets
  python quail.py --status        # Show status
"""
import sys
from pathlib import Path

# Add current directory to Python path
HERE = Path(__file__).parent.absolute()
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# Import and run the CLI
if __name__ == "__main__":
    try:
        from quail_cli import main
        sys.exit(main())
    except ImportError as e:
        print(f"❌ Failed to import QuailTrail CLI: {e}")
        print("Make sure you're in the quailtrail directory with all the required files")
        sys.exit(1)