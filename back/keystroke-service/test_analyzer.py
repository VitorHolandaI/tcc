"""
Tests for the KeyloggerAnalyzer class.

Tests the analysis logic that processes keystroke data to detect suspicious behavior.
This is the core analysis engine based on Roberto's code (tccRoberto/analyzer.py).
"""
import json
import os
import tempfile
import pytest
from datetime import datetime, timedelta


import sys
sys.path.insert(0, os.path.dirname(__file__))

from analyzer import KeyloggerAnalyzer


def _create_temp_json(events):
    """Helper: create a temporary JSON file with keystroke events"""
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w') as f:
        json.dump(events, f)
    return path


def _generate_normal_typing(n=50, start_time=None):
    """Generate realistic normal typing events"""
    if start_time is None:
        start_time = datetime(2024, 1, 1, 12, 0, 0)

    events = []
    current_time = start_time
    text = "def hello_world():\n    print('hello world')\n\nhello_world()\n" * (n // 50 + 1)

    for i in range(n):
        flight_time = 0.15 + (i % 5) * 0.02 if i > 0 else None
        hold_time = 0.08 + (i % 3) * 0.01

        if i > 0:
            current_time += timedelta(seconds=flight_time)

        char = text[i % len(text)]
        events.append({
            "key": char,
            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "application": "Browser",
            "flight_time": round(flight_time, 3) if flight_time else None,
            "hold_time": round(hold_time, 3),
            "command_type": None
        })

    return events


def _generate_suspicious_typing(n=50, paste_count=10):
    """Generate typing events with many paste commands (suspicious)"""
    events = _generate_normal_typing(n)
    base_time = datetime.strptime(events[-1]["timestamp"], "%Y-%m-%d %H:%M:%S.%f")

    for i in range(paste_count):
        base_time += timedelta(seconds=0.1)
        events.append({
            "key": "v",
            "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
            "application": "Browser",
            "flight_time": 0.1,
            "hold_time": 0.05,
            "command_type": "paste"
        })

    return events


class TestTypingMetrics:
    """Tests for calculate_typing_metrics()"""

    def test_normal_typing_metrics(self):
        """Normal typing should produce reasonable metrics"""
        events = _generate_normal_typing(30)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            metrics = analyzer.calculate_typing_metrics()

            assert metrics["total_events"] == 30
            assert metrics["hold_time_avg"] > 0
            assert metrics["hold_time_std"] >= 0
            assert metrics["flight_time_avg"] > 0
            assert metrics["flight_time_std"] >= 0
        finally:
            os.remove(path)

    def test_empty_data_metrics(self):
        """Empty data should return zeros"""
        path = _create_temp_json([])
        try:
            analyzer = KeyloggerAnalyzer(path)
            metrics = analyzer.calculate_typing_metrics()

            assert metrics["total_events"] == 0
            assert metrics["hold_time_avg"] == 0
            assert metrics["flight_time_avg"] == 0
        finally:
            os.remove(path)

    def test_single_event_metrics(self):
        """Single event should work without errors"""
        events = [{
            "key": "a",
            "timestamp": "2024-01-01 12:00:00.000",
            "application": "Browser",
            "flight_time": None,
            "hold_time": 0.1,
            "command_type": None
        }]
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            metrics = analyzer.calculate_typing_metrics()

            assert metrics["total_events"] == 1
            assert metrics["hold_time_avg"] == 0.1
        finally:
            os.remove(path)

    def test_events_without_hold_time_skipped(self):
        """Events without hold_time should be skipped in metrics"""
        events = [
            {"key": "a", "timestamp": "2024-01-01 12:00:00.000",
             "application": "Browser", "flight_time": None, "hold_time": None, "command_type": None},
            {"key": "b", "timestamp": "2024-01-01 12:00:00.200",
             "application": "Browser", "flight_time": 0.2, "hold_time": 0.1, "command_type": None},
        ]
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            metrics = analyzer.calculate_typing_metrics()
            assert metrics["total_events"] == 1  # Only event with hold_time
        finally:
            os.remove(path)


class TestSuspiciousCommands:
    """Tests for analyze_suspicious_commands()"""

    def test_no_suspicious_commands(self):
        """Normal typing should have 0% suspicious commands"""
        events = _generate_normal_typing(30)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            result = analyzer.analyze_suspicious_commands()

            assert result["total_commands"] == 0
            assert result["suspicious_percentage"] == 0
            assert result["command_counts"] == {}
        finally:
            os.remove(path)

    def test_paste_detection(self):
        """Paste commands should be detected as suspicious"""
        events = [
            {"key": "a", "timestamp": "2024-01-01 12:00:00.000",
             "application": "Browser", "flight_time": None, "hold_time": 0.1, "command_type": None},
            {"key": "v", "timestamp": "2024-01-01 12:00:00.200",
             "application": "Browser", "flight_time": 0.2, "hold_time": 0.05, "command_type": "paste"},
            {"key": "b", "timestamp": "2024-01-01 12:00:00.400",
             "application": "Browser", "flight_time": 0.2, "hold_time": 0.1, "command_type": None},
        ]
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            result = analyzer.analyze_suspicious_commands()

            assert result["total_commands"] == 1
            assert "paste" in result["command_counts"]
            assert result["command_counts"]["paste"] == 1
            assert result["suspicious_percentage"] > 0
        finally:
            os.remove(path)

    def test_multiple_command_types(self):
        """Multiple command types should all be detected"""
        events = [
            {"key": "a", "timestamp": "2024-01-01 12:00:00.000",
             "application": "Browser", "flight_time": None, "hold_time": 0.1, "command_type": None},
            {"key": "c", "timestamp": "2024-01-01 12:00:00.100",
             "application": "Browser", "flight_time": 0.1, "hold_time": 0.05, "command_type": "copy"},
            {"key": "v", "timestamp": "2024-01-01 12:00:00.200",
             "application": "Browser", "flight_time": 0.1, "hold_time": 0.05, "command_type": "paste"},
            {"key": "x", "timestamp": "2024-01-01 12:00:00.300",
             "application": "Browser", "flight_time": 0.1, "hold_time": 0.05, "command_type": "cut"},
            {"key": "Backspace", "timestamp": "2024-01-01 12:00:00.400",
             "application": "Browser", "flight_time": 0.1, "hold_time": 0.05, "command_type": "backspace"},
            {"key": "ArrowLeft", "timestamp": "2024-01-01 12:00:00.500",
             "application": "Browser", "flight_time": 0.1, "hold_time": 0.05, "command_type": "cursor_movement"},
        ]
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            result = analyzer.analyze_suspicious_commands()

            assert result["total_commands"] == 5  # copy, paste, cut, backspace, cursor_movement
            assert "copy" in result["command_counts"]
            assert "paste" in result["command_counts"]
            assert "cut" in result["command_counts"]
            assert "backspace" in result["command_counts"]
            assert "cursor_movement" in result["command_counts"]
        finally:
            os.remove(path)

    def test_high_suspicious_percentage(self):
        """Many paste commands should result in high suspicious %"""
        events = _generate_suspicious_typing(10, paste_count=20)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            result = analyzer.analyze_suspicious_commands()

            # 20 paste commands out of 30 total = ~66%
            assert result["suspicious_percentage"] > 50
        finally:
            os.remove(path)

    def test_command_sequences_detected(self):
        """Consecutive suspicious commands form sequences"""
        events = [
            {"key": "a", "timestamp": "2024-01-01 12:00:00.000",
             "application": "Browser", "flight_time": None, "hold_time": 0.1, "command_type": None},
            {"key": "v", "timestamp": "2024-01-01 12:00:00.100",
             "application": "Browser", "flight_time": 0.1, "hold_time": 0.05, "command_type": "paste"},
            {"key": "v", "timestamp": "2024-01-01 12:00:00.200",
             "application": "Browser", "flight_time": 0.1, "hold_time": 0.05, "command_type": "paste"},
            {"key": "v", "timestamp": "2024-01-01 12:00:00.300",
             "application": "Browser", "flight_time": 0.1, "hold_time": 0.05, "command_type": "paste"},
            {"key": "b", "timestamp": "2024-01-01 12:00:00.400",
             "application": "Browser", "flight_time": 0.1, "hold_time": 0.1, "command_type": None},
        ]
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            result = analyzer.analyze_suspicious_commands()

            assert result["command_sequences"] >= 1
        finally:
            os.remove(path)


class TestManhattanDistance:
    """Tests for calculate_manhattan_distance()"""

    def test_single_application(self):
        """Events from single application should have one entry"""
        events = _generate_normal_typing(20)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            app_metrics = analyzer.calculate_manhattan_distance()

            assert "Browser" in app_metrics
            assert app_metrics["Browser"]["event_count"] == 20
            assert app_metrics["Browser"]["typing_rate"] > 0
        finally:
            os.remove(path)

    def test_multiple_applications_suspicious(self):
        """Events from many different applications should be flagged"""
        events = []
        base_time = datetime(2024, 1, 1, 12, 0, 0)

        for i, app in enumerate(["Browser", "VSCode", "Terminal", "Chrome", "Notepad", "Slack"]):
            for j in range(5):
                idx = i * 5 + j
                current_time = base_time + timedelta(seconds=idx * 0.2)
                events.append({
                    "key": chr(97 + (idx % 26)),
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                    "application": app,
                    "flight_time": 0.2 if idx > 0 else None,
                    "hold_time": 0.1,
                    "command_type": None
                })

        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            app_metrics = analyzer.calculate_manhattan_distance()

            assert len(app_metrics) == 6
        finally:
            os.remove(path)


class TestSequenceManhattan:
    """Tests for _calculate_sequence_manhattan()"""

    def test_empty_sequence(self):
        """Empty sequence should return 0"""
        events = _generate_normal_typing(5)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            result = analyzer._calculate_sequence_manhattan([])
            assert result == 0.0
        finally:
            os.remove(path)

    def test_single_event_sequence(self):
        """Single event sequence should return 0"""
        events = _generate_normal_typing(5)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            single = [{
                "key": "v", "timestamp": "2024-01-01 12:00:00.000",
                "application": "Browser", "flight_time": 0.1, "hold_time": 0.05,
                "command_type": "paste"
            }]
            result = analyzer._calculate_sequence_manhattan(single)
            assert result == 0.0
        finally:
            os.remove(path)

    def test_multi_event_sequence_distance(self):
        """Multiple events should produce non-zero distance"""
        events = _generate_normal_typing(5)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            sequence = [
                {"key": "v", "timestamp": "2024-01-01 12:00:00.000",
                 "application": "Browser", "flight_time": 0.1, "hold_time": 0.05,
                 "command_type": "paste"},
                {"key": "v", "timestamp": "2024-01-01 12:00:01.000",
                 "application": "Browser", "flight_time": 1.0, "hold_time": 0.05,
                 "command_type": "paste"},
            ]
            result = analyzer._calculate_sequence_manhattan(sequence)
            assert result > 0
        finally:
            os.remove(path)


class TestOutlierCount:
    """Tests for calculate_outlier_count()"""

    def test_consistent_typing_no_outliers(self):
        """Consistent typing should have few/no outliers"""
        events = _generate_normal_typing(50)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            outliers = analyzer.calculate_outlier_count()

            assert outliers["hold_time_outliers"] >= 0
            assert outliers["flight_time_outliers"] >= 0
        finally:
            os.remove(path)

    def test_events_with_extreme_values(self):
        """Events with extreme hold/flight times should be detected as outliers"""
        events = _generate_normal_typing(100)
        base_time = datetime.strptime(events[-1]["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
        for i in range(10):
            base_time += timedelta(seconds=0.2)
            events.append({
                "key": "z",
                "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
                "application": "Browser",
                "flight_time": 50.0,  # Extremely long flight time
                "hold_time": 25.0,    # Extremely long hold time
                "command_type": None
            })

        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            outliers = analyzer.calculate_outlier_count()

            assert outliers["hold_time_outliers"] > 0 or outliers["flight_time_outliers"] > 0
        finally:
            os.remove(path)


class TestGenerateReport:
    """Tests for generate_report()"""

    def test_normal_behavior_report(self):
        """Normal typing should produce a report with COMPORTAMENTO NORMAL"""
        events = _generate_normal_typing(50)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            report = analyzer.generate_report()

            assert "typing_metrics" in report
            assert "suspicious_commands" in report
            assert "application_metrics" in report
            assert "text_segments" in report
            assert "is_suspicious" in report
            assert "conclusion" in report
            assert report["typing_metrics"]["total_events"] > 0
        finally:
            os.remove(path)

    def test_suspicious_behavior_report(self):
        """Many paste commands should produce suspicious report"""
        events = _generate_suspicious_typing(20, paste_count=30)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            report = analyzer.generate_report()

            assert report["is_suspicious"] is True
            assert report["conclusion"] == "ATENÇÃO NECESSÁRIA"
            assert len(report["suspicious_reasons"]) > 0
        finally:
            os.remove(path)

    def test_report_has_all_required_fields(self):
        """Report should contain all required fields"""
        events = _generate_normal_typing(30)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            report = analyzer.generate_report()

            required_fields = [
                "file_analyzed", "analysis_date", "typing_metrics",
                "suspicious_commands", "application_metrics", "text_segments",
                "is_suspicious", "suspicious_typing_ratio", "suspicious_reasons",
                "outlier_counts", "conclusion"
            ]
            for field in required_fields:
                assert field in report, f"Missing field: {field}"
        finally:
            os.remove(path)


class TestTextSegments:
    """Tests for analyze_text_segments()"""

    def test_basic_text_segmentation(self):
        """Continuous typing should form text segments"""
        events = _generate_normal_typing(30)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            segments = analyzer.analyze_text_segments()

            assert len(segments) > 0
            typing_segments = [s for s in segments if s["type"] == "typing"]
            assert len(typing_segments) > 0
        finally:
            os.remove(path)

    def test_pause_creates_new_segment(self):
        """A 2+ second pause should create a new text segment"""
        events = [
            {"key": "a", "timestamp": "2024-01-01 12:00:00.000",
             "application": "Browser", "flight_time": None, "hold_time": 0.1, "command_type": None},
            {"key": "b", "timestamp": "2024-01-01 12:00:00.200",
             "application": "Browser", "flight_time": 0.2, "hold_time": 0.1, "command_type": None},
            # 3 second pause
            {"key": "c", "timestamp": "2024-01-01 12:00:03.200",
             "application": "Browser", "flight_time": 3.0, "hold_time": 0.1, "command_type": None},
            {"key": "d", "timestamp": "2024-01-01 12:00:03.400",
             "application": "Browser", "flight_time": 0.2, "hold_time": 0.1, "command_type": None},
        ]
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            segments = analyzer.analyze_text_segments()

            typing_segments = [s for s in segments if s["type"] == "typing"]
            assert len(typing_segments) >= 2
        finally:
            os.remove(path)


class TestFormatKey:
    """Tests for _format_key() method"""

    def test_regular_character(self):
        """Regular characters should return themselves"""
        events = _generate_normal_typing(5)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            assert analyzer._format_key("a") == "a"
            assert analyzer._format_key("z") == "z"
            assert analyzer._format_key("1") == "1"
        finally:
            os.remove(path)

    def test_special_keys(self):
        """Special keys should be formatted correctly"""
        events = _generate_normal_typing(5)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            assert analyzer._format_key("Key.space") == " "
            assert "←" in analyzer._format_key("Key.backspace")
            assert "↵" in analyzer._format_key("Key.enter")
        finally:
            os.remove(path)

    def test_modifier_keys_empty(self):
        """Modifier keys should return empty string"""
        events = _generate_normal_typing(5)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            assert analyzer._format_key("Key.shift") == ""
            assert analyzer._format_key("Key.ctrl") == ""
            assert analyzer._format_key("Key.alt") == ""
        finally:
            os.remove(path)

    def test_copy_paste_keys(self):
        """Copy/paste related keys should be formatted with brackets"""
        events = _generate_normal_typing(5)
        path = _create_temp_json(events)
        try:
            analyzer = KeyloggerAnalyzer(path)
            assert analyzer._format_key("c") == "[C]"
            assert analyzer._format_key("v") == "[V]"
            assert analyzer._format_key("x") == "[X]"
        finally:
            os.remove(path)
