#!/usr/bin/env python3
"""Test Focused Accuracy System - Target: 90%+ accuracy"""

from focused_accuracy_system import FocusedAccuracySystem
import time

def test_focused_accuracy():
    """Test the focused accuracy system on diverse code samples"""
    
    system = FocusedAccuracySystem()
    
    # Test cases with expected outcomes
    test_cases = [
        # 1. Perfect Code
        ('''
import json
import os

def process_config(filename):
    """Load and process configuration"""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

data = process_config('config.json')
print(f"Loaded {len(data)} settings")
''', 'PASS', 'Perfect syntax, imports, execution'),

        # 2. Syntax Error (100% detectable)
        ('''
def broken_function()  # Missing colon
    return "hello"
''', 'FAIL', 'Clear syntax error'),

        # 3. Missing Import (90% detectable)
        ('''
def fetch_data():
    response = requests.get("http://api.example.com")
    return response.json()
''', 'FAIL', 'Missing requests import'),

        # 4. Security Issue (90% detectable)
        ('''
def dangerous_query(user_id):
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    return execute_sql(query)
''', 'FAIL', 'SQL injection vulnerability'),

        # 5. Good Code with Common Patterns
        ('''
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def log_event(message):
    timestamp = datetime.now().isoformat()
    logger.info(f"{timestamp}: {message}")
    return True

log_event("System started")
''', 'PASS', 'Good logging pattern'),

        # 6. Code Injection (90% detectable)
        ('''
def execute_user_code(code):
    return eval(code)  # Dangerous!
''', 'FAIL', 'Code injection via eval'),

        # 7. Complex but Valid Code
        ('''
import json
from typing import Dict, List, Optional

class DataProcessor:
    def __init__(self, config: Dict):
        self.config = config
        self.results: List[Dict] = []
    
    def process_item(self, item: Dict) -> Optional[Dict]:
        if self.validate_item(item):
            processed = self.transform_item(item)
            self.results.append(processed)
            return processed
        return None
    
    def validate_item(self, item: Dict) -> bool:
        required_fields = self.config.get('required_fields', [])
        return all(field in item for field in required_fields)
    
    def transform_item(self, item: Dict) -> Dict:
        return {k: str(v).strip() for k, v in item.items()}

processor = DataProcessor({'required_fields': ['name', 'id']})
result = processor.process_item({'name': 'Test', 'id': 123})
''', 'PASS', 'Complex but valid OOP code'),

        # 8. Import Issues
        ('''
from . import utils  # Relative import without package
from some_module import *  # Star import

def process():
    return utils.helper()
''', 'FAIL', 'Problematic import patterns'),

        # 9. Shell Injection
        ('''
import subprocess

def run_command(user_cmd):
    result = subprocess.run(user_cmd, shell=True)
    return result.stdout
''', 'FAIL', 'Shell injection risk'),

        # 10. Valid API Code
        ('''
import requests
import json
from typing import Optional

def api_call(endpoint: str, data: dict) -> Optional[dict]:
    try:
        response = requests.post(
            f"https://api.example.com/{endpoint}",
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"API call failed: {e}")
        return None

result = api_call("users", {"name": "John", "email": "john@example.com"})
''', 'PASS', 'Valid API interaction code')
    ]
    
    print("🎯 Testing Focused Accuracy System")
    print("=" * 60)
    
    correct = 0
    total = len(test_cases)
    
    for i, (code, expected, description) in enumerate(test_cases, 1):
        print(f"\n[Test {i}] {description}")
        print("-" * 40)
        
        start_time = time.time()
        result = system.focused_analyze(f"test_{i}.py", code)
        elapsed = time.time() - start_time
        
        actual = result['status']
        confidence = result['confidence']
        auto_mark = result.get('should_auto_mark', False)
        
        status_match = actual == expected
        if status_match:
            correct += 1
            print(f"✅ CORRECT: {actual} (expected {expected})")
        else:
            print(f"❌ WRONG: {actual} (expected {expected})")
        
        print(f"   Confidence: {confidence}%")
        print(f"   Auto-mark: {auto_mark}")
        print(f"   Time: {elapsed:.2f}s")
        
        if result['issues']:
            print(f"   Issues: {result['issues']}")
    
    accuracy = (correct / total) * 100
    print("\n" + "=" * 60)
    print(f"🏆 FOCUSED ACCURACY RESULTS:")
    print(f"   Correct: {correct}/{total}")
    print(f"   Accuracy: {accuracy:.1f}%")
    print(f"   Target: 90%+")
    
    if accuracy >= 90:
        print("✅ TARGET ACHIEVED! High accuracy with objective validation")
    else:
        print("⚠️  Target not met, but much better than subjective validation")
    
    return accuracy

if __name__ == "__main__":
    test_focused_accuracy() 