# vibeHack2025
Teams meeting analyzer with real-time sentiment analysis and AI agent monitoring

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp config.env.template .env
   # Edit .env with your actual API keys
   ```

3. **Start monitoring:**
   ```bash
   ./start_monitoring.sh
   ```

## Features

- **Automatic Agent Monitoring** - Tracks every Cursor AI suggestion
- **Real-time Code Analysis** - Uses GPT-4o-mini to analyze code quality  
- **Auto-generated Cursor Rules** - Creates rules from failed suggestions
- **Opik Integration** - Full observability and tracing
- **Security Detection** - Identifies vulnerabilities and unsafe patterns

## API Keys Required

- **OpenAI API Key** - For code analysis
- **Opik API Key** - For monitoring and tracing 