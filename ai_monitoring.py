import anthropic
import openai
from opik.integrations.anthropic import track_anthropic
from opik.integrations.openai import track_openai
from opik import track
import os
import json
from datetime import datetime

# Configuration
os.environ["OPIK_API_KEY"] = "rLx8SArNCDqZ5xwZtjTKEfoys" 
os.environ["OPIK_WORKSPACE"] = "anka"

# Set up API keys (you'll need to add your actual keys)
# os.environ["ANTHROPIC_API_KEY"] = "your_anthropic_key_here"
# os.environ["OPENAI_API_KEY"] = "your_openai_key_here"

# Initialize clients with tracking (with error handling)
try:
    anthropic_client = anthropic.Anthropic()
    anthropic_client = track_anthropic(anthropic_client)
    anthropic_available = True
except Exception as e:
    print(f"Anthropic client not available: {e}")
    anthropic_available = False

try:
    openai_client = openai.OpenAI()
    openai_client = track_openai(openai_client)
    openai_available = True
except Exception as e:
    print(f"OpenAI client not available: {e}")
    openai_available = False

class AICodeAnalyzer:
    def __init__(self):
        self.common_errors = []
        self.cursor_rules = []
    
    @track
    def analyze_code_suggestion(self, code_snippet, context="general"):
        """Analyze a code suggestion for potential issues"""
        
        if not anthropic_available:
            return "Anthropic API not available. Please set ANTHROPIC_API_KEY environment variable."
        
        # Use Claude to analyze the code
        claude_response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{
                "role": "user", 
                "content": f"""
                Analyze this code snippet for potential issues, bugs, or improvements:
                
                Context: {context}
                
                Code:
                ```
                {code_snippet}
                ```
                
                Please identify:
                1. Potential bugs or security issues
                2. Code quality problems
                3. Performance concerns
                4. Best practice violations
                5. Suggested improvements
                
                Format your response as JSON with categories.
                """
            }],
        )
        
        return claude_response.content[0].text
    
    @track
    def generate_cursor_rules(self, error_patterns):
        """Generate cursor rules based on common error patterns"""
        
        if not openai_available:
            return "OpenAI API not available. Please set OPENAI_API_KEY environment variable."
        
        prompt = f"""
        Based on these common error patterns in our codebase:
        {json.dumps(error_patterns, indent=2)}
        
        Generate specific cursor IDE rules that would prevent these errors.
        Format as markdown rules that can be added to .cursorrules file.
        
        Focus on:
        - Type safety rules
        - API usage patterns
        - Security best practices
        - Performance optimizations
        - Code structure guidelines
        """
        
        gpt_response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-4o-mini as specified in user rules
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )
        
        return gpt_response.choices[0].message.content
    
    @track
    def analyze_teams_meeting_code(self, code_snippet):
        """Specific analysis for Teams meeting analyzer code"""
        
        analysis_prompt = f"""
        Analyze this code snippet from a Microsoft Teams meeting analyzer project:
        
        ```
        {code_snippet}
        ```
        
        Focus on:
        1. Microsoft Graph API usage patterns
        2. Real-time processing efficiency
        3. Error handling for live meetings
        4. Privacy and security considerations
        5. LLM integration best practices
        6. Overlay UI performance issues
        
        Provide specific suggestions for improvement.
        """
        
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": analysis_prompt}],
        )
        
        return response.content[0].text

# Example usage for your Teams meeting analyzer
def test_haiku_generation():
    """Test the basic setup with your original haiku example"""
    if not anthropic_available:
        print("Anthropic API not available. Please set ANTHROPIC_API_KEY environment variable.")
        return "API not available"
    
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a haiku about AI engineering."}],
    )
    print("Haiku Response:", response.content[0].text)
    return response.content[0].text

# Example Teams meeting analyzer code to analyze
SAMPLE_TEAMS_CODE = '''
import openai
from opik import track

@track
def analyze_meeting_sentiment(transcript_chunk):
    """Analyze sentiment of meeting transcript"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"Analyze the sentiment of this meeting transcript: {transcript_chunk}"
            }]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: {e}")
        return "neutral"

def detect_concerns(conversation):
    # TODO: Implement concern detection
    concerns = []
    for message in conversation:
        if "worried" in message.lower() or "concerned" in message.lower():
            concerns.append(message)
    return concerns
'''

if __name__ == "__main__":
    analyzer = AICodeAnalyzer()
    
    # Test basic functionality
    print("=== Testing Haiku Generation ===")
    test_haiku_generation()
    
    print("\n=== Analyzing Sample Teams Code ===")
    analysis = analyzer.analyze_teams_meeting_code(SAMPLE_TEAMS_CODE)
    print("Code Analysis:", analysis)
    
    print("\n=== Opik Dashboard ===")
    print("View your traces at: https://www.comet.com/opik")
    print("All AI calls are now being tracked and can be analyzed!") 