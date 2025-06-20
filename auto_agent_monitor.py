#!/usr/bin/env python3
"""
Automatic Agent Monitor - Runs after each Cursor agent code edit
This system automatically:
1. Detects when files are modified (agent suggestions)
2. Logs the changes with Opik
3. Analyzes code quality 
4. Generates cursor rules for any issues found
5. Provides continuous feedback

Usage: python auto_agent_monitor.py --watch
"""

import os
import time
import json
import hashlib
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import sys
from datetime import datetime
from dotenv import load_dotenv
from agent_learning_system import log_cursor_agent_run, mark_failed, mark_successful, learning_system
import openai
from opik.integrations.openai import track_openai
from opik import track
from accuracy_config import AccuracyConfig

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI for automatic analysis
openai_client = openai.OpenAI()
openai_client = track_openai(openai_client)

class AgentChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.file_hashes = {}
        self.last_change_time = {}
        self.change_buffer = {}  # Buffer changes for batch processing
        self.ignore_patterns = {'.git', '__pycache__', '.DS_Store', 'node_modules', 'venv'}
        
    def should_ignore_file(self, file_path):
        """Check if file should be ignored"""
        path_parts = Path(file_path).parts
        
        # Ignore certain directories and file types
        for ignore in self.ignore_patterns:
            if ignore in path_parts:
                return True
                
        # Only monitor code files
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.json', '.md'}
        if Path(file_path).suffix not in code_extensions:
            return True
            
        return False
    
    def on_modified(self, event):
        if event.is_directory or self.should_ignore_file(event.src_path):
            return
            
        file_path = event.src_path
        current_time = time.time()
        
        # Debounce rapid changes (wait 2 seconds after last change)
        self.last_change_time[file_path] = current_time
        
        # Schedule analysis after debounce period
        self.schedule_analysis(file_path)
    
    def schedule_analysis(self, file_path):
        """Schedule file analysis after debounce period"""
        def delayed_analysis():
            time.sleep(2)  # Debounce period
            
            current_time = time.time()
            if current_time - self.last_change_time.get(file_path, 0) >= 2:
                self.analyze_file_change(file_path)
        
        # Run in separate thread to avoid blocking
        import threading
        threading.Thread(target=delayed_analysis, daemon=True).start()
    
    def analyze_file_change(self, file_path):
        """Analyze a file change and log it"""
        try:
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # Calculate hash to detect actual changes
            current_hash = hashlib.md5(current_content.encode()).hexdigest()
            previous_hash = self.file_hashes.get(file_path)
            
            if current_hash == previous_hash:
                return  # No actual change
            
            self.file_hashes[file_path] = current_hash
            
            # Get diff if we have previous version
            diff_info = self.get_file_diff(file_path, current_content)
            
            print(f"\n🔍 AGENT CHANGE DETECTED: {Path(file_path).name}")
            print(f"📅 Time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"📄 File: {file_path}")
            
            # Log the change
            suggestion_id = self.log_agent_change(file_path, current_content, diff_info)
            
            # Automatically analyze the code
            self.auto_analyze_code(file_path, current_content, suggestion_id)
            
        except Exception as e:
            print(f"❌ Error analyzing file change: {e}")
    
    def get_file_diff(self, file_path, current_content):
        """Get git diff information if available"""
        try:
            # Try to get git diff
            result = subprocess.run(
                ['git', 'diff', 'HEAD', file_path],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(file_path) or '.'
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return {
                    'has_diff': True,
                    'diff': result.stdout,
                    'lines_added': result.stdout.count('\n+'),
                    'lines_removed': result.stdout.count('\n-')
                }
        except:
            pass
        
        return {'has_diff': False, 'diff': '', 'lines_added': 0, 'lines_removed': 0}
    
    def log_agent_change(self, file_path, content, diff_info):
        """Log the agent change to our learning system"""
        
        # Create a descriptive query based on the change
        file_name = Path(file_path).name
        change_description = f"Agent modified {file_name}"
        
        if diff_info['has_diff']:
            change_description += f" (+{diff_info['lines_added']} -{diff_info['lines_removed']} lines)"
        
        # Extract meaningful code snippet (first 500 chars)
        code_snippet = content[:500] + "..." if len(content) > 500 else content
        
        # Log with our learning system
        suggestion_entry = log_cursor_agent_run(
            user_query=f"File modification: {file_name}",
            agent_response=change_description,
            code_provided=code_snippet,
            context=f"File: {file_path}, Auto-detected change"
        )
        
        suggestion_id = len(learning_system.conversation_history) - 1
        print(f"📝 Logged as suggestion #{suggestion_id}")
        
        return suggestion_id
    
    @track
    def auto_analyze_code(self, file_path, content, suggestion_id):
        """Automatically analyze the code for issues with improved accuracy"""
        
        print("🔍 Auto-analyzing code quality...")
        
        # Step 1: Syntax validation for Python files
        syntax_issues = self.validate_syntax(file_path, content)
        
        # Step 2: LLM analysis with confidence scoring
        llm_analysis = self.get_llm_analysis(file_path, content)
        
        # Step 3: Combine results and determine confidence
        final_assessment = self.combine_analysis_results(syntax_issues, llm_analysis, file_path)
        
        print(f"🤖 Analysis: {final_assessment['summary']}")
        print(f"🎯 Confidence: {final_assessment['confidence']}%")
        
        # Step 4: Auto-mark only high-confidence failures, otherwise prompt user
        if final_assessment['should_auto_mark']:
            if final_assessment['status'] == 'FAIL':
                print("❌ High-confidence failure detected - Auto-marking as FAILED")
                mark_failed(suggestion_id, final_assessment['issues'], "HighConfidenceIssue")
            else:
                print("✅ High-confidence success - Auto-marking as SUCCESSFUL")
                mark_successful(suggestion_id)
        else:
            print("⚠️ Uncertain analysis - Prompting for human validation")
            self.prompt_human_validation(suggestion_id, final_assessment)
    
    def validate_syntax(self, file_path, content):
        """Validate syntax for supported file types"""
        issues = []
        
        if file_path.endswith('.py'):
            try:
                compile(content, file_path, 'exec')
                print("✅ Python syntax: VALID")
            except SyntaxError as e:
                issue = f"Python SyntaxError at line {e.lineno}: {e.msg}"
                issues.append(issue)
                print(f"❌ Python syntax: {issue}")
            except Exception as e:
                issues.append(f"Python compilation error: {str(e)}")
        
        # Add more syntax validators for other languages as needed
        # elif file_path.endswith('.js'):
        #     # Could use a JS syntax validator here
        
        return issues
    
    def get_llm_analysis(self, file_path, content):
        """Get LLM analysis with more detailed prompting"""
        
        # Use more context - full file if small, or smart truncation
        max_chars = AccuracyConfig.MAX_ANALYSIS_CHARS
        if len(content) <= max_chars:
            code_to_analyze = content
            context_note = "Full file content"
        else:
            # Smart truncation based on configuration
            if AccuracyConfig.TRUNCATION_STRATEGY == "smart":
                lines = content.split('\n')
                if len(lines) > 50:
                    # Take first 25 and last 25 lines for context
                    relevant_lines = lines[:25] + ['... (content truncated) ...'] + lines[-25:]
                    code_to_analyze = '\n'.join(relevant_lines)
                    context_note = "Truncated content (first/last 25 lines)"
                else:
                    code_to_analyze = content[:max_chars] + "..."
                    context_note = f"Truncated content (first {max_chars} chars)"
            elif AccuracyConfig.TRUNCATION_STRATEGY == "beginning":
                code_to_analyze = content[:max_chars] + "..."
                context_note = f"Truncated content (first {max_chars} chars)"
            else:  # "end"
                code_to_analyze = "..." + content[-max_chars:]
                context_note = f"Truncated content (last {max_chars} chars)"
        
        # Get focus areas from configuration
        focus_areas = AccuracyConfig.get_analysis_prompt_focus()
        focus_text = "\n".join(f"{i+1}. {area}" for i, area in enumerate(focus_areas))
        
        analysis_prompt = f"""
        Analyze this code file that was just modified by a Cursor AI agent:
        
        File: {Path(file_path).name}
        Context: {context_note}
        
        ```
        {code_to_analyze}
        ```
        
        Provide a detailed analysis focusing ONLY on these areas:
        {focus_text}
        
        IMPORTANT: Only consider the focus areas listed above. Ignore subjective issues like:
        - Code style preferences
        - Performance optimizations (unless critical)
        - Best practice suggestions (unless they cause bugs)
        
        Response format:
        CONFIDENCE: [1-100]% - How confident are you in this analysis?
        STATUS: [PASS/FAIL/UNCERTAIN]
        CRITICAL_ISSUES: [List any critical issues that would prevent code from working]
        WARNINGS: [List any concerns or improvements needed]
        REASONING: [Brief explanation of your assessment]
        
        Be conservative - only mark as FAIL if you're highly confident there are real functional issues.
        """
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=500
            )
            
            return self.parse_llm_response(response.choices[0].message.content.strip())
            
        except Exception as e:
            print(f"⚠️ LLM analysis failed: {e}")
            return {
                'confidence': 0,
                'status': 'UNCERTAIN',
                'critical_issues': [],
                'warnings': [f"LLM analysis failed: {str(e)}"],
                'reasoning': 'Analysis could not be completed'
            }
    
    def parse_llm_response(self, response_text):
        """Parse the structured LLM response"""
        result = {
            'confidence': 50,  # default
            'status': 'UNCERTAIN',
            'critical_issues': [],
            'warnings': [],
            'reasoning': response_text
        }
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('CONFIDENCE:'):
                try:
                    confidence_str = line.split(':', 1)[1].strip().replace('%', '')
                    result['confidence'] = int(confidence_str)
                except:
                    pass
            elif line.startswith('STATUS:'):
                status = line.split(':', 1)[1].strip().upper()
                if status in ['PASS', 'FAIL', 'UNCERTAIN']:
                    result['status'] = status
            elif line.startswith('CRITICAL_ISSUES:'):
                issues_text = line.split(':', 1)[1].strip()
                if issues_text and issues_text.lower() != 'none':
                    result['critical_issues'] = [issues_text]
            elif line.startswith('WARNINGS:'):
                warnings_text = line.split(':', 1)[1].strip()
                if warnings_text and warnings_text.lower() != 'none':
                    result['warnings'] = [warnings_text]
        
        return result
    
    def combine_analysis_results(self, syntax_issues, llm_analysis, file_path=""):
        """Combine syntax validation and LLM analysis results"""
        
        # Syntax errors always result in failure
        if syntax_issues:
            return {
                'status': 'FAIL',
                'confidence': 95,  # High confidence in syntax errors
                'should_auto_mark': True,
                'issues': f"Syntax errors: {'; '.join(syntax_issues)}",
                'summary': f"FAIL: Syntax errors detected - {'; '.join(syntax_issues)}"
            }
        
        # Use LLM analysis for other issues
        confidence = llm_analysis['confidence']
        status = llm_analysis['status']
        
        # Combine critical issues and warnings
        all_issues = llm_analysis['critical_issues'] + llm_analysis['warnings']
        issues_text = '; '.join(all_issues) if all_issues else 'No issues detected'
        
        # Determine if we should auto-mark based on configuration
        should_auto_mark = AccuracyConfig.should_auto_mark(status, confidence, file_path)
        
        return {
            'status': status,
            'confidence': confidence,
            'should_auto_mark': should_auto_mark,
            'issues': issues_text,
            'summary': f"{status}: {issues_text} (Confidence: {confidence}%)"
        }
    
    def prompt_human_validation(self, suggestion_id, assessment):
        """Prompt user for validation when confidence is low"""
        
        print("\n" + "="*60)
        print("🤔 HUMAN VALIDATION REQUIRED")
        print("="*60)
        print(f"Analysis Summary: {assessment['summary']}")
        print(f"Confidence Level: {assessment['confidence']}%")
        print("\nThe system is uncertain about this analysis.")
        print("Please review the code change and provide feedback.")
        print("\nOptions:")
        print("  1. Mark as SUCCESSFUL (s)")
        print("  2. Mark as FAILED (f) - you'll be prompted for error details")
        print("  3. Skip for manual review later (skip)")
        print("="*60)
        
        # For now, just log that human validation is needed
        # In a full implementation, you might use input() or a web interface
        print("⏳ Suggestion marked as PENDING - awaiting human validation")
        print(f"   Use: python track_agent.py success {suggestion_id}")
        print(f"   Or:  python track_agent.py failed {suggestion_id} 'error details'")
        print("="*60 + "\n")

class AutoAgentMonitor:
    def __init__(self):
        self.observer = None
        self.handler = AgentChangeHandler()
    
    def start_monitoring(self, path="."):
        """Start monitoring the specified path"""
        print(f"🚀 Starting Automatic Agent Monitor")
        print(f"📁 Watching: {os.path.abspath(path)}")
        print(f"🔄 Will auto-log every agent code change...")
        print(f"⚡ Will auto-analyze code quality...")
        print(f"📝 Will auto-generate cursor rules for failures...")
        print("=" * 60)
        
        self.observer = Observer()
        self.observer.schedule(self.handler, path, recursive=True)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor...")
            self.observer.stop()
        
        self.observer.join()
        
    def get_stats(self):
        """Get current monitoring stats"""
        from agent_learning_system import get_stats
        return get_stats()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Automatic Agent Monitor')
    parser.add_argument('--watch', action='store_true', 
                       help='Start watching for agent changes')
    parser.add_argument('--path', default='.', 
                       help='Path to monitor (default: current directory)')
    parser.add_argument('--stats', action='store_true',
                       help='Show current statistics')
    
    args = parser.parse_args()
    
    monitor = AutoAgentMonitor()
    
    if args.stats:
        stats = monitor.get_stats()
        print("📊 Current Agent Learning Statistics:")
        print(f"  Total suggestions: {stats['total_suggestions']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        
    elif args.watch:
        monitor.start_monitoring(args.path)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 