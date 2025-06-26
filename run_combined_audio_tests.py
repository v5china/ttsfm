#!/usr/bin/env python3
"""
Test runner for combined audio functionality.

This script runs all tests for the combined audio feature and provides
a comprehensive report of the results.
"""

import unittest
import sys
import os
import time
import subprocess
from pathlib import Path
import requests


def check_server_status():
    """Check if the TTSFM web server is running."""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def check_dependencies():
    """Check if required dependencies are available."""
    dependencies = {
        'requests': 'HTTP client library',
        'ttsfm': 'TTSFM package',
        'flask': 'Web framework'
    }
    
    missing = []
    for dep, description in dependencies.items():
        try:
            __import__(dep)
        except ImportError:
            missing.append(f"{dep} ({description})")
    
    return missing


def run_unit_tests():
    """Run unit tests for combined audio functionality."""
    print("🧪 Running Unit Tests")
    print("=" * 50)
    
    # Add tests directory to path
    tests_dir = Path(__file__).parent / "tests"
    if tests_dir.exists():
        sys.path.insert(0, str(tests_dir))
    
    try:
        # Import and run unit tests
        from test_combined_audio import (
            TestTextSplitting,
            TestAudioCombination,
            TestTTSResponseCombination,
            TestErrorHandling,
            TestIntegrationScenarios,
            TestPerformanceScenarios
        )
        
        # Create test suite
        suite = unittest.TestSuite()
        
        test_classes = [
            TestTextSplitting,
            TestAudioCombination,
            TestTTSResponseCombination,
            TestErrorHandling,
            TestIntegrationScenarios,
            TestPerformanceScenarios
        ]
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
        result = runner.run(suite)
        
        return result
        
    except ImportError as e:
        print(f"❌ Could not import unit tests: {e}")
        print("Make sure the tests directory exists and contains test_combined_audio.py")
        return None


def run_integration_tests():
    """Run integration tests for combined audio endpoints."""
    print("\n🌐 Running Integration Tests")
    print("=" * 50)
    
    if not check_server_status():
        print("❌ TTSFM web server is not running on http://localhost:8000")
        print("Please start the server first:")
        print("  cd ttsfm-web && python app.py")
        return None
    
    # Add tests directory to path
    tests_dir = Path(__file__).parent / "tests"
    if tests_dir.exists():
        sys.path.insert(0, str(tests_dir))
    
    try:
        from test_combined_endpoints import TestCombinedAudioEndpoints
        
        # Create test suite
        suite = unittest.TestLoader().loadTestsFromTestCase(TestCombinedAudioEndpoints)
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
        result = runner.run(suite)
        
        return result
        
    except ImportError as e:
        print(f"❌ Could not import integration tests: {e}")
        return None


def run_manual_tests():
    """Run manual verification tests."""
    print("\n🔧 Running Manual Verification Tests")
    print("=" * 50)
    
    if not check_server_status():
        print("❌ Server not running, skipping manual tests")
        return False
    
    try:
        # Test 1: Basic functionality
        print("📝 Test 1: Basic combined audio generation...")
        response = requests.post(
            "http://localhost:8000/api/generate-combined",
            json={
                "text": "This is a test of the combined audio functionality. " * 20,
                "voice": "alloy",
                "format": "mp3",
                "max_length": 100
            },
            timeout=30
        )
        
        if response.status_code == 200:
            chunks = response.headers.get('X-Chunks-Combined', '0')
            size = len(response.content)
            print(f"   ✅ Success: {chunks} chunks, {size:,} bytes")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
        
        # Test 2: OpenAI compatibility
        print("📝 Test 2: OpenAI-compatible endpoint...")
        response = requests.post(
            "http://localhost:8000/v1/audio/speech-combined",
            json={
                "model": "gpt-4o-mini-tts",
                "input": "Testing OpenAI compatibility. " * 15,
                "voice": "nova",
                "response_format": "wav",
                "max_length": 80
            },
            timeout=30
        )
        
        if response.status_code == 200:
            chunks = response.headers.get('X-Chunks-Combined', '0')
            print(f"   ✅ Success: {chunks} chunks combined")
        else:
            print(f"   ❌ Failed: {response.status_code}")
            return False
        
        # Test 3: Error handling
        print("📝 Test 3: Error handling...")
        response = requests.post(
            "http://localhost:8000/api/generate-combined",
            json={
                "text": "",  # Empty text should fail
                "voice": "alloy",
                "format": "mp3"
            },
            timeout=10
        )
        
        if response.status_code == 400:
            print("   ✅ Success: Properly handled empty text error")
        else:
            print(f"   ❌ Failed: Expected 400, got {response.status_code}")
            return False
        
        print("✅ All manual tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Manual tests failed: {e}")
        return False


def generate_test_report(unit_result, integration_result, manual_result):
    """Generate a comprehensive test report."""
    print("\n📊 Test Report")
    print("=" * 60)
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    # Unit test results
    if unit_result:
        print(f"🧪 Unit Tests:")
        print(f"   Tests run: {unit_result.testsRun}")
        print(f"   Failures: {len(unit_result.failures)}")
        print(f"   Errors: {len(unit_result.errors)}")
        print(f"   Success rate: {((unit_result.testsRun - len(unit_result.failures) - len(unit_result.errors)) / unit_result.testsRun * 100):.1f}%")
        
        total_tests += unit_result.testsRun
        total_failures += len(unit_result.failures)
        total_errors += len(unit_result.errors)
    else:
        print("🧪 Unit Tests: SKIPPED")
    
    # Integration test results
    if integration_result:
        print(f"\n🌐 Integration Tests:")
        print(f"   Tests run: {integration_result.testsRun}")
        print(f"   Failures: {len(integration_result.failures)}")
        print(f"   Errors: {len(integration_result.errors)}")
        print(f"   Success rate: {((integration_result.testsRun - len(integration_result.failures) - len(integration_result.errors)) / integration_result.testsRun * 100):.1f}%")
        
        total_tests += integration_result.testsRun
        total_failures += len(integration_result.failures)
        total_errors += len(integration_result.errors)
    else:
        print("\n🌐 Integration Tests: SKIPPED")
    
    # Manual test results
    print(f"\n🔧 Manual Tests: {'PASSED' if manual_result else 'FAILED/SKIPPED'}")
    
    # Overall summary
    print(f"\n📈 Overall Summary:")
    print(f"   Total tests: {total_tests}")
    print(f"   Total failures: {total_failures}")
    print(f"   Total errors: {total_errors}")
    
    if total_tests > 0:
        success_rate = ((total_tests - total_failures - total_errors) / total_tests * 100)
        print(f"   Overall success rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("   🎉 EXCELLENT: Combined audio functionality is working well!")
        elif success_rate >= 75:
            print("   ✅ GOOD: Combined audio functionality is mostly working")
        elif success_rate >= 50:
            print("   ⚠️  FAIR: Some issues with combined audio functionality")
        else:
            print("   ❌ POOR: Significant issues with combined audio functionality")
    
    # Detailed failure report
    if unit_result and (unit_result.failures or unit_result.errors):
        print(f"\n🔍 Unit Test Issues:")
        for test, traceback in unit_result.failures:
            print(f"   FAILURE: {test}")
        for test, traceback in unit_result.errors:
            print(f"   ERROR: {test}")
    
    if integration_result and (integration_result.failures or integration_result.errors):
        print(f"\n🔍 Integration Test Issues:")
        for test, traceback in integration_result.failures:
            print(f"   FAILURE: {test}")
        for test, traceback in integration_result.errors:
            print(f"   ERROR: {test}")


def main():
    """Main test runner function."""
    print("🎵 TTSFM Combined Audio Test Suite")
    print("=" * 60)
    print("Testing the new combined audio generation functionality")
    print()
    
    # Check dependencies
    print("🔍 Checking Dependencies...")
    missing_deps = check_dependencies()
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nPlease install missing dependencies and try again.")
        return 1
    else:
        print("✅ All dependencies available")
    
    # Check server status
    print("\n🌐 Checking Server Status...")
    if check_server_status():
        print("✅ TTSFM web server is running")
    else:
        print("⚠️  TTSFM web server is not running")
        print("   Integration tests will be skipped")
        print("   To run integration tests, start the server:")
        print("   cd ttsfm-web && python app.py")
    
    print()
    
    # Run tests
    start_time = time.time()
    
    unit_result = run_unit_tests()
    integration_result = run_integration_tests()
    manual_result = run_manual_tests()
    
    end_time = time.time()
    
    # Generate report
    generate_test_report(unit_result, integration_result, manual_result)
    
    print(f"\n⏱️  Total test time: {end_time - start_time:.2f} seconds")
    
    # Determine exit code
    if unit_result and not unit_result.wasSuccessful():
        return 1
    if integration_result and not integration_result.wasSuccessful():
        return 1
    if manual_result is False:
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
