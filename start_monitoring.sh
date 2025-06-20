#!/bin/bash

# Start Automatic Agent Monitoring
echo "🚀 Starting Automatic Cursor Agent Monitor..."
echo "This will automatically track EVERY code change and analyze it!"
echo ""

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ Error: OPENAI_API_KEY environment variable not set"
    echo "Please either:"
    echo "  1. Create a .env file with your API key (see config.env.template)"
    echo "  2. Export it manually: export OPENAI_API_KEY='your-api-key'"
    exit 1
fi

# Start monitoring
python auto_agent_monitor.py --watch

echo "Monitor stopped." 