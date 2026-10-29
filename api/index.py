"""
Vercel Serverless Function Entry Point for X-Ray Execution Agent
File: api/index.py
"""

import os
import sys

# Ensure repository root is on sys.path so app, tracer, presets_data can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app import app
