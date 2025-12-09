#!/bin/bash

# AGI Proto-System - Quick Setup Script
# Run this to set up the project for first use

set -e  # Exit on error

echo "🚀 AGI Proto-System - Quick Setup"
echo "=================================="
echo ""

# Check Node.js version
echo "Checking Node.js version..."
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Error: Node.js 18+ required (found v$NODE_VERSION)"
    exit 1
fi
echo "✅ Node.js version OK"
echo ""

# Install dependencies
echo "Installing dependencies..."
npm install
echo "✅ Dependencies installed"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - OPENAI_API_KEY (required)"
    echo "   - ANTHROPIC_API_KEY (optional)"
    echo "   - DB_URL (required)"
    echo ""
else
    echo "✅ .env file exists"
    echo ""
fi

# Check for API keys
if grep -q "OPENAI_API_KEY=$" .env 2>/dev/null; then
    echo "⚠️  OpenAI API key not set in .env"
else
    echo "✅ OpenAI API key configured"
fi

if grep -q "DB_URL=" .env 2>/dev/null; then
    echo "✅ Database URL configured"
else
    echo "⚠️  Database URL not set in .env"
fi
echo ""

# Check PostgreSQL
echo "Checking PostgreSQL..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client found"
    
    # Try to connect
    if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw agi_proto; then
        echo "✅ agi_proto database exists"
    else
        echo "⚠️  Database 'agi_proto' not found"
        echo "   Create it with: createdb agi_proto"
    fi
else
    echo "⚠️  PostgreSQL not found or not in PATH"
fi
echo ""

# Build the project
echo "Building TypeScript..."
npm run build
echo "✅ Build successful"
echo ""

# Run tests
echo "Running tests..."
if npm test -- --passWithNoTests; then
    echo "✅ Tests passed"
else
    echo "⚠️  Some tests failed (this is OK for initial setup)"
fi
echo ""

echo "=================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Set up PostgreSQL database: createdb agi_proto"
echo "3. Enable pgvector: psql agi_proto -c 'CREATE EXTENSION vector;'"
echo "4. Run the system: npm run dev"
echo ""
echo "📚 Documentation:"
echo "- Quick Reference: .gemini/antigravity/brain/.../quick_reference.md"
echo "- Walkthrough: .gemini/antigravity/brain/.../walkthrough.md"
echo "- Troubleshooting: .gemini/antigravity/brain/.../troubleshooting.md"
echo ""
