#!/usr/bin/env python3
"""
Simple script to track Cursor agent suggestions and learn from failures.
Usage after each agent interaction:

# To log a suggestion:
python track_agent.py log "your query" "agent response" --code "code provided"

# To mark as failed:
python track_agent.py failed 0 "error details" --type "ErrorType"

# To mark as successful:
python track_agent.py success 0

# To get stats:
python track_agent.py stats
"""

import sys
import argparse
from agent_learning_system import (
    log_cursor_agent_run, 
    mark_failed, 
    mark_successful, 
    get_stats, 
    analyze_patterns
)

def main():
    parser = argparse.ArgumentParser(description='Track Cursor Agent Learning')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Log command
    log_parser = subparsers.add_parser('log', help='Log an agent suggestion')
    log_parser.add_argument('query', help='User query')
    log_parser.add_argument('response', help='Agent response')
    log_parser.add_argument('--code', default='', help='Code provided by agent')
    log_parser.add_argument('--context', default='', help='Context of the suggestion')
    
    # Failed command
    failed_parser = subparsers.add_parser('failed', help='Mark suggestion as failed')
    failed_parser.add_argument('id', type=int, help='Suggestion ID')
    failed_parser.add_argument('error', help='Error details')
    failed_parser.add_argument('--type', default='', help='Error type')
    
    # Success command
    success_parser = subparsers.add_parser('success', help='Mark suggestion as successful')
    success_parser.add_argument('id', type=int, help='Suggestion ID')
    
    # Stats command
    subparsers.add_parser('stats', help='Get learning statistics')
    
    # Patterns command
    subparsers.add_parser('patterns', help='Analyze failure patterns')
    
    args = parser.parse_args()
    
    if args.command == 'log':
        suggestion = log_cursor_agent_run(
            args.query, 
            args.response, 
            args.code, 
            args.context
        )
        print(f"📝 Logged suggestion #{len(learning_system.conversation_history)-1}")
        
    elif args.command == 'failed':
        mark_failed(args.id, args.error, getattr(args, 'type', ''))
        
    elif args.command == 'success':
        mark_successful(args.id)
        
    elif args.command == 'stats':
        stats = get_stats()
        print("📊 Agent Learning Statistics:")
        print(f"  Total suggestions: {stats['total_suggestions']}")
        print(f"  Successful: {stats['successful']}")
        print(f"  Failed: {stats['failed']}")
        print(f"  Pending: {stats['pending']}")
        print(f"  Success rate: {stats['success_rate']:.1f}%")
        
    elif args.command == 'patterns':
        patterns = analyze_patterns()
        print("🔍 Failure Pattern Analysis:")
        print(patterns)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    # Import here to avoid circular import
    from agent_learning_system import learning_system
    main() 