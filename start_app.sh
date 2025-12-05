#!/bin/bash
# Quick Start Script for Orion Octave Cubes Web App

set -e

echo "======================================================================"
echo "  Orion Octave Cubes - Quick Start"
echo "======================================================================"
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is required but not found"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚙️  Installing dependencies..."
    pip install -r requirements.txt
else
    echo "✓ Dependencies already installed"
fi
echo ""

# Start the web application
echo "======================================================================"
echo "  Starting Web Application"
echo "======================================================================"
echo ""
echo "The dashboard will be available at:"
echo ""
echo "  🌐 http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "======================================================================"
echo ""

python3 app.py
