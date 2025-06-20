import openai
from opik.integrations.openai import track_openai
from opik import track
import os
import json
import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
os.environ["OPIK_API_KEY"] = os.getenv("OPIK_API_KEY", "rLx8SArNCDqZ5xwZtjTKEfoys")
os.environ["OPIK_WORKSPACE"] = "anka"

# Initialize OpenAI client with tracking
openai_client = openai.OpenAI()
openai_client = track_openai(openai_client)

class CursorAgentLearningSystem:
    def __init__(self):
        self.conversation_history = []
        self.failed_suggestions = []
        self.successful_suggestions = []
        
    @track
    def log_agent_suggestion(self, 
                           user_query: str, 
                           agent_response: str, 
                           code_provided: str = "", 
                           context: str = ""):
        """Log each agent suggestion from Cursor"""
        
        suggestion_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_query": user_query,
            "agent_response": agent_response,
            "code_provided": code_provided,
            "context": context,
            "status": "pending"  # Will be updated based on user feedback
        }
        
        self.conversation_history.append(suggestion_entry)
        print(f"✅ Logged agent suggestion: {user_query[:50]}...")
        
        return suggestion_entry
    
    @track
    def mark_suggestion_failed(self, 
                             suggestion_id: int, 
                             error_details: str, 
                             error_type: str = ""):
        """Mark a suggestion as failed and log the error"""
        
        if suggestion_id < len(self.conversation_history):
            self.conversation_history[suggestion_id]["status"] = "failed"
            self.conversation_history[suggestion_id]["error_details"] = error_details
            self.conversation_history[suggestion_id]["error_type"] = error_type
            
            self.failed_suggestions.append(self.conversation_history[suggestion_id])
            
            print(f"❌ Marked suggestion {suggestion_id} as failed: {error_details}")
            
            # Automatically analyze the failure and generate cursor rules
            self._analyze_failure_and_generate_rules(self.conversation_history[suggestion_id])
    
    @track
    def mark_suggestion_successful(self, suggestion_id: int):
        """Mark a suggestion as successful"""
        
        if suggestion_id < len(self.conversation_history):
            self.conversation_history[suggestion_id]["status"] = "successful"
            self.successful_suggestions.append(self.conversation_history[suggestion_id])
            
            print(f"✅ Marked suggestion {suggestion_id} as successful")
    
    @track
    def _analyze_failure_and_generate_rules(self, failed_suggestion: Dict):
        """Analyze a failed suggestion and generate cursor rules to prevent it"""
        
        analysis_prompt = f"""
        Analyze this failed AI agent suggestion and create specific cursor rules to prevent this mistake:

        USER QUERY: {failed_suggestion['user_query']}
        AGENT RESPONSE: {failed_suggestion['agent_response']}
        CODE PROVIDED: {failed_suggestion.get('code_provided', 'N/A')}
        ERROR DETAILS: {failed_suggestion.get('error_details', 'N/A')}
        ERROR TYPE: {failed_suggestion.get('error_type', 'N/A')}
        CONTEXT: {failed_suggestion.get('context', 'N/A')}

        Generate specific cursor rules in markdown format that would prevent this exact mistake.
        Focus on:
        1. What the AI agent did wrong
        2. What it should have done instead
        3. Specific rules to prevent this pattern
        4. Code examples of correct vs incorrect approaches

        Format as markdown rules that can be added to .cursorrules file.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=1500
        )
        
        generated_rules = response.choices[0].message.content
        
        # Append to cursor rules file
        self._append_to_cursor_rules(generated_rules, failed_suggestion)
        
        return generated_rules
    
    def _append_to_cursor_rules(self, new_rules: str, failed_suggestion: Dict):
        """Append new rules to the .cursorrules file"""
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        rule_entry = f"""

# Rule Generated from Failed Suggestion - {timestamp}
# Original Query: {failed_suggestion['user_query'][:100]}...
# Error: {failed_suggestion.get('error_details', 'N/A')[:100]}...

{new_rules}

"""
        
        try:
            with open('.cursorrules', 'a', encoding='utf-8') as f:
                f.write(rule_entry)
            print(f"📝 Added new rules to .cursorrules file")
        except Exception as e:
            print(f"⚠️ Failed to update .cursorrules file: {e}")
    
    @track
    def analyze_pattern_of_failures(self):
        """Analyze patterns in failed suggestions to generate broader rules"""
        
        if len(self.failed_suggestions) < 2:
            return "Not enough failed suggestions to analyze patterns."
        
        failures_summary = []
        for failure in self.failed_suggestions:
            failures_summary.append({
                "query": failure['user_query'][:100],
                "error": failure.get('error_details', 'N/A')[:100],
                "type": failure.get('error_type', 'unknown')
            })
        
        pattern_analysis_prompt = f"""
        Analyze these patterns of AI agent failures and generate comprehensive cursor rules:

        FAILED SUGGESTIONS PATTERN:
        {json.dumps(failures_summary, indent=2)}

        Identify:
        1. Common mistake patterns
        2. Recurring error types  
        3. Areas where the AI agent consistently fails
        4. Systematic improvements needed

        Generate comprehensive cursor rules to address these patterns.
        Focus on preventing systematic mistakes rather than individual cases.
        """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": pattern_analysis_prompt}],
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def get_learning_stats(self):
        """Get statistics about agent learning"""
        
        total = len(self.conversation_history)
        successful = len(self.successful_suggestions)
        failed = len(self.failed_suggestions)
        pending = total - successful - failed
        
        return {
            "total_suggestions": total,
            "successful": successful,
            "failed": failed,
            "pending": pending,
            "success_rate": (successful / total * 100) if total > 0 else 0
        }

# Global instance for the session
learning_system = CursorAgentLearningSystem()

def log_cursor_agent_run(user_query: str, 
                        agent_response: str, 
                        code_provided: str = "", 
                        context: str = ""):
    """Easy function to log each Cursor agent interaction"""
    return learning_system.log_agent_suggestion(user_query, agent_response, code_provided, context)

def mark_failed(suggestion_id: int, error_details: str, error_type: str = ""):
    """Easy function to mark a suggestion as failed"""
    learning_system.mark_suggestion_failed(suggestion_id, error_details, error_type)

def mark_successful(suggestion_id: int):
    """Easy function to mark a suggestion as successful"""
    learning_system.mark_suggestion_successful(suggestion_id)

def get_stats():
    """Get learning statistics"""
    return learning_system.get_learning_stats()

def analyze_patterns():
    """Analyze failure patterns"""
    return learning_system.analyze_pattern_of_failures()

# Example usage for your workflow
if __name__ == "__main__":
    print("🧠 Cursor Agent Learning System Initialized")
    print("=" * 60)
    
    # Example: Log a suggestion that might fail
    suggestion_0 = log_cursor_agent_run(
        user_query="Create a Teams meeting analyzer with real-time sentiment analysis",
        agent_response="I'll create a Python script that uses OpenAI API to analyze meeting transcripts...",
        code_provided="import openai\n\ndef analyze_sentiment(text):\n    # Code here",
        context="Teams meeting analyzer project"
    )
    
    # Simulate marking it as failed
    mark_failed(0, "OpenAI API key authentication failed", "AuthenticationError")
    
    # Get learning stats
    stats = get_stats()
    print(f"\n📊 Learning Stats: {stats}")
    
    print("\n🔍 View detailed traces at: https://www.comet.com/opik")
    print("📝 New cursor rules automatically added to .cursorrules file!") 