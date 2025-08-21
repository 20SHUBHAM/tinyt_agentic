#!/bin/bash

# Agentic Focus Group System - Startup Script

echo "🚀 Starting Agentic Focus Group System..."

# Create necessary directories
mkdir -p data/sessions data/cache static/uploads

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
fi

# Start the application
echo "🎯 Starting application..."
python main.py