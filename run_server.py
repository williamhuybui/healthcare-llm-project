#!/usr/bin/env python3
"""
Standalone server runner for the CSV to GraphQL service
"""

import uvicorn
import sys
import os

# Add the python_src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python_src'))

if __name__ == "__main__":
    print("🚀 Starting CSV to GraphQL Service (Python)...")
    print("📊 GraphQL endpoint: http://localhost:8000/graphql")
    print("🎮 GraphiQL playground: http://localhost:8000/graphql")
    print("📋 API docs: http://localhost:8000/docs")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["python_src"]
    )