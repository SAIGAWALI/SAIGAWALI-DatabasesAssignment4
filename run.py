#!/usr/bin/env python3
"""
Simple Flask app launcher
Run with: python run.py
"""

import sys
import os

# Add the Module_B directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
from app.main import app

if __name__ == '__main__':
    print("=" * 60)
    print("Starting Doctor Management System")
    print("=" * 60)
    print("\nServer running on: http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='localhost', port=5000)
