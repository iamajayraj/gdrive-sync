#!/usr/bin/env python3
"""
Entry point script for Render deployment.
"""

import os
import sys
import subprocess

def main():
    """Run the main application."""
    print("Starting Google Drive Sync application...")
    
    # Add the src directory to the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Run the main module
    from src.main import main
    main()

if __name__ == "__main__":
    main()
