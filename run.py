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
    
    # Add the current directory to the Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Set up configuration
    print("Setting up configuration...")
    from setup_config import setup_config
    setup_config()
    
    # Print current directory and list files for debugging
    print(f"Current directory: {os.getcwd()}")
    print("Files in current directory:")
    for item in os.listdir("."):
        print(f"  {item}")
    print("Files in config directory:")
    for item in os.listdir("config"):
        print(f"  {item}")
    
    # Run the main module
    print("Running main application...")
    from src.main import main
    main()

if __name__ == "__main__":
    main()
