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
    # Try to import the new CLI
    try:
        from quail_cli import main as cli_main
        return cli_main()
    except ImportError as e:
        print(f"Warning: Could not import quail_cli: {e}")
        # Fallback to original CLI if available
        try:
            from .cli import main as old_main
            return old_main()
        except ImportError:
            print("❌ No CLI module found")
            print("Usage: python -m quail --help")
            print("Make sure you're in the quailtrail directory")
            return 1

if __name__ == "__main__":
    sys.exit(main())
