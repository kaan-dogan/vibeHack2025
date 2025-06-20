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
from agent_learning_system import log_cursor_agent_run, mark_failed, mark_successful, learning_system
import openai
from opik.integrations.openai import track_openai
from opik import track

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
        """Automatically analyze the code for issues"""
        
        print("🔍 Auto-analyzing code quality...")
        
        analysis_prompt = f"""
        Analyze this code file that was just modified by a Cursor AI agent:
        
        File: {Path(file_path).name}
        Content (first 1000 chars):
        ```
        {content[:1000]}
        ```
        
        Quickly identify:
        1. Syntax errors or obvious bugs
        2. Missing imports or dependencies
        3. Potential runtime errors
        4. Security issues
        5. Performance problems
        
        Respond with:
        - "PASS" if code looks good
        - "FAIL: [specific issue]" if there are problems
        
        Be concise but specific.
        """
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=300
            )
            
            analysis_result = response.choices[0].message.content.strip()
            print(f"🤖 Analysis: {analysis_result}")
            
            # Auto-mark as failed if issues found
            if analysis_result.upper().startswith("FAIL"):
                print("❌ Auto-marking as FAILED due to detected issues")
                mark_failed(suggestion_id, analysis_result, "AutoDetectedIssue")
            else:
                print("✅ Code looks good - marking as successful")
                mark_successful(suggestion_id)
                
        except Exception as e:
            print(f"⚠️ Auto-analysis failed: {e}")

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