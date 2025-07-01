#!/usr/bin/env python3
"""Test script to demonstrate logging behavior."""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from util.logging_util import get_logger

def test_logging_behavior():
    """Test logging with different configurations."""
    
    print("=== Testing Logging Behavior ===\n")
    
    # Test 1: Console only
    print("1. Testing console-only logging:")
    logger1 = get_logger("test.console", log_to_file=False)
    logger1.info("This log goes to CONSOLE ONLY")
    logger1.error("This error goes to CONSOLE ONLY")
    
    # Test 2: Console + File
    print("\n2. Testing console + file logging:")
    logger2 = get_logger("test.both", log_to_file=True)
    logger2.info("This log goes to BOTH console AND file")
    logger2.error("This error goes to BOTH console AND file")
    
    # Check if log file was created
    log_file = Path("logs/app.log")
    if log_file.exists():
        print(f"\n✅ Log file created: {log_file}")
        print(f"📄 Log file size: {log_file.stat().st_size} bytes")
        
        # Read and show file contents
        with open(log_file, 'r') as f:
            content = f.read()
            print(f"\n📋 Log file contents:\n{content}")
    else:
        print(f"\n❌ Log file not found: {log_file}")

if __name__ == "__main__":
    test_logging_behavior() 