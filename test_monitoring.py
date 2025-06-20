import openai
from opik.integrations.openai import track_openai
from opik import track
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
os.environ["OPIK_API_KEY"] = os.getenv("OPIK_API_KEY", "rLx8SArNCDqZ5xwZtjTKEfoys")
os.environ["OPIK_WORKSPACE"] = "anka"

# Initialize OpenAI client with tracking
openai_client = openai.OpenAI()
openai_client = track_openai(openai_client)

@track
def analyze_teams_code(code_snippet):
    """Analyze code for Teams meeting analyzer project"""
    
    prompt = f"""
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
    
    Provide specific suggestions for improvement and identify potential bugs.
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",  # Using gpt-4o-mini as specified
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    
    return response.choices[0].message.content

@track
def generate_cursor_rules_from_analysis(analysis_result):
    """Generate cursor rules based on code analysis"""
    
    prompt = f"""
    Based on this code analysis:
    
    {analysis_result}
    
    Generate specific cursor IDE rules that would prevent these issues.
    Format as markdown rules that can be added to .cursorrules file.
    
    Focus on:
    - Error handling patterns
    - API usage best practices
    - Security considerations
    - Performance optimizations
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    
    return response.choices[0].message.content

# Sample Teams meeting code to analyze
SAMPLE_CODE = '''
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
    # Basic concern detection
    concerns = []
    worry_words = ["worried", "concerned", "problem", "issue", "trouble"]
    
    for message in conversation:
        if any(word in message.lower() for word in worry_words):
            concerns.append(message)
    return concerns

def suggest_responses(concern):
    # TODO: Add AI-powered response suggestions
    return ["I understand your concern.", "Let's discuss this further."]
'''

if __name__ == "__main__":
    print("🚀 Testing Teams Meeting Analyzer Code Monitoring")
    print("=" * 60)
    
    # Step 1: Analyze the sample code
    print("\n📊 Step 1: Analyzing sample code...")
    analysis = analyze_teams_code(SAMPLE_CODE)
    print("Analysis Result:")
    print(analysis)
    
    # Step 2: Generate cursor rules based on analysis
    print("\n📝 Step 2: Generating cursor rules...")
    cursor_rules = generate_cursor_rules_from_analysis(analysis)
    print("Generated Cursor Rules:")
    print(cursor_rules)
    
    print("\n✅ Monitoring Complete!")
    print("🔍 View your traces at: https://www.comet.com/opik")
    print("📈 All LLM calls are now being tracked and analyzed!") 