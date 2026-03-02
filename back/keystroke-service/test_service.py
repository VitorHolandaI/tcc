#!/usr/bin/env python3
"""
Simple test script for Keystroke Analysis Service
"""
import json
import os
import sys

try:
    from analyzer import KeyloggerAnalyzer
    print(" analyzer.py imported successfully")
except ImportError as e:
    print(f" Failed to import analyzer.py: {e}")
    sys.exit(1)

try:
    from report_generator import ReportGenerator
    print(" report_generator.py imported successfully")
except ImportError as e:
    print(f" Failed to import report_generator.py: {e}")
    sys.exit(1)

try:
    from config import config
    print(" config.py imported successfully")
    print(f" - Service Port: {config.SERVICE_PORT}")
    print(f" - Database URL: {config.DATABASE_URL}")
except ImportError as e:
    print(f" Failed to import config.py: {e}")
    sys.exit(1)

try:
    from database import Base, engine, KeystrokeAnalysis
    print(" database.py imported successfully")
    print(f" - Tables: {list(Base.metadata.tables.keys())}")
except ImportError as e:
    print(f" Failed to import database.py: {e}")
    sys.exit(1)

print("\nTesting analyzer with sample keystroke data...")

sample_data = [
    {
        "key": "a",
        "press_time": 1000,
        "release_time": 1100,
        "hold_time": 100,
        "flight_time": 0
    },
    {
        "key": "b",
        "press_time": 1200,
        "release_time": 1290,
        "hold_time": 90,
        "flight_time": 100
    },
    {
        "key": "ctrl+v",
        "press_time": 1400,
        "release_time": 1450,
        "hold_time": 50,
        "flight_time": 110,
        "command_type": "paste"
    }
]

temp_file = "/tmp/test_keystroke.json"
with open(temp_file, 'w') as f:
    json.dump(sample_data, f, indent=4)

try:
    analyzer = KeyloggerAnalyzer(temp_file)
    print(" KeyloggerAnalyzer initialized")

    typing_metrics = analyzer.calculate_typing_metrics()
    print(f" Typing metrics calculated:")
    print(f" - Total events: {typing_metrics['total_events']}")
    print(f" - Hold time avg: {typing_metrics['hold_time_avg']}ms")
    print(f" - Flight time avg: {typing_metrics['flight_time_avg']}ms")

    suspicious_commands = analyzer.analyze_suspicious_commands()
    print(f" Suspicious commands analyzed:")
    print(f" - Total commands: {suspicious_commands['total_commands']}")
    print(f" - Suspicious %: {suspicious_commands['suspicious_percentage']}%")
    print(f" - Command counts: {suspicious_commands['command_counts']}")

    os.remove(temp_file)
    print(" Cleanup successful")

except Exception as e:
    print(f" Analyzer test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("All tests passed!")
print("="*50)
print("\nTo start the service:")
print(" python main.py")
print("\nOr with Docker:")
print(" docker-compose up keystroke-service")
