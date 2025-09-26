#!/usr/bin/env python3
"""
QuailTrail - Database quality checking pipeline
Run with: python -m quail or quail command
"""
import sys
import os
from pathlib import Path

# Add the parent directory to Python path for CLI access
HERE = Path(__file__).parent.parent.absolute()
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

def main():
    """Main entry point for python -m quail"""
    # Use the QuailTrail CLI
    try:
        from .cli import main as quail_main
        return quail_main()
    except ImportError as e:
        print(f"❌ Could not import QuailTrail CLI: {e}")
        print("Usage: python -m quail --help")
        print("Make sure you're in the quailtrail directory")
        return 1

if __name__ == "__main__":
    sys.exit(main())
