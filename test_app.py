#!/usr/bin/env python3
"""
Test suite for Orion Octave Cubes application
Validates core functionality and API endpoints
"""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:5000"
TEST_RESULTS = []

def test_result(name, passed, message=""):
    """Record test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    TEST_RESULTS.append({
        'name': name,
        'passed': passed,
        'message': message
    })
    print(f"{status}: {name}")
    if message:
        print(f"    {message}")

def test_home_page():
    """Test if home page loads"""
    try:
        response = requests.get(BASE_URL, timeout=5)
        passed = response.status_code == 200 and "Orion Octave Cubes" in response.text
        test_result("Home page loads", passed)
        return passed
    except Exception as e:
        test_result("Home page loads", False, str(e))
        return False

def test_static_files():
    """Test if static files are accessible"""
    files = [
        "/static/css/style.css",
        "/static/js/app.js"
    ]
    
    for file_path in files:
        try:
            response = requests.get(f"{BASE_URL}{file_path}", timeout=5)
            passed = response.status_code == 200
            test_result(f"Static file: {file_path}", passed)
        except Exception as e:
            test_result(f"Static file: {file_path}", False, str(e))

def test_api_analyze():
    """Test analysis API endpoint"""
    try:
        data = {
            "side": 2.0,
            "angle": 30.0,
            "max_distance_pairs": 5000,
            "max_direction_pairs": 2000
        }
        
        print("\n  Running analysis (this may take 5-10 seconds)...")
        response = requests.post(
            f"{BASE_URL}/api/analyze",
            json=data,
            timeout=30
        )
        
        passed = response.status_code == 200
        
        if passed:
            result = response.json()
            passed = result.get('success', False) and 'cache_key' in result
            
            if passed:
                cache_key = result['cache_key']
                summary = result['summary']
                
                # Validate summary structure
                required_keys = ['configuration', 'point_counts', 'distance_stats', 
                               'golden_ratio', 'special_angles', 'icosahedral_check']
                all_present = all(key in summary for key in required_keys)
                
                test_result("API Analysis", all_present, 
                          f"Cache key: {cache_key}, Points: {summary['point_counts']['unique_points']}")
                return cache_key if all_present else None
            else:
                test_result("API Analysis", False, "Missing expected fields in response")
                return None
        else:
            test_result("API Analysis", False, f"Status code: {response.status_code}")
            return None
            
    except Exception as e:
        test_result("API Analysis", False, str(e))
        return None

def test_api_plots(cache_key):
    """Test plot generation endpoints"""
    if not cache_key:
        test_result("API Plots", False, "No cache key available")
        return
    
    plot_types = ['3d', 'distances', 'angles', 'summary']
    
    for plot_type in plot_types:
        try:
            print(f"\n  Generating {plot_type} plot...")
            response = requests.get(
                f"{BASE_URL}/api/plot/{plot_type}/{cache_key}",
                timeout=30
            )
            
            passed = (response.status_code == 200 and 
                     response.headers.get('Content-Type') == 'image/png')
            
            if passed:
                size_kb = len(response.content) / 1024
                test_result(f"Plot generation: {plot_type}", True, 
                          f"Size: {size_kb:.1f} KB")
            else:
                test_result(f"Plot generation: {plot_type}", False, 
                          f"Status: {response.status_code}")
                
        except Exception as e:
            test_result(f"Plot generation: {plot_type}", False, str(e))

def test_api_download(cache_key):
    """Test JSON download endpoint"""
    if not cache_key:
        test_result("API Download", False, "No cache key available")
        return
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/download/{cache_key}",
            timeout=10
        )
        
        passed = response.status_code == 200
        
        if passed:
            # Try to parse JSON
            try:
                data = response.json()
                has_required = all(key in data for key in 
                                 ['configuration', 'points', 'distances'])
                test_result("API Download", has_required, 
                          f"Data size: {len(response.content)} bytes")
            except json.JSONDecodeError as e:
                test_result("API Download", False, f"Invalid JSON response: {str(e)}")
            except Exception as e:
                test_result("API Download", False, f"Unexpected error: {str(e)}")
        else:
            test_result("API Download", False, f"Status: {response.status_code}")
            
    except Exception as e:
        test_result("API Download", False, str(e))

def test_cli_tool():
    """Test command-line interface"""
    import subprocess
    
    try:
        # Test basic CLI execution
        result = subprocess.run(
            ['python3', 'orion_octave_test.py', '--quiet', '--angle', '45', 
             '--max-distance-pairs', '5000', '--max-direction-pairs', '2000',
             '--output', 'test_output.json'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd='/workspaces/ddd'
        )
        
        passed = result.returncode == 0
        
        if passed:
            # Check if output file was created
            output_file = Path('/workspaces/ddd/test_output.json')
            if output_file.exists():
                with open(output_file) as f:
                    data = json.load(f)
                passed = 'configuration' in data and 'points' in data
                output_file.unlink()  # Clean up
                test_result("CLI Tool", passed, "Output file created and valid")
            else:
                test_result("CLI Tool", False, "Output file not created")
        else:
            test_result("CLI Tool", False, f"Exit code: {result.returncode}")
            
    except Exception as e:
        test_result("CLI Tool", False, str(e))

def print_summary():
    """Print test summary"""
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for t in TEST_RESULTS if t['passed'])
    total = len(TEST_RESULTS)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {percentage:.1f}%")
    
    if total - passed > 0:
        print("\nFailed Tests:")
        for test in TEST_RESULTS:
            if not test['passed']:
                print(f"  ✗ {test['name']}")
                if test['message']:
                    print(f"    {test['message']}")
    
    print("\n" + "="*70)
    
    return passed == total

def main():
    """Run all tests"""
    print("="*70)
    print("Orion Octave Cubes - Test Suite")
    print("="*70)
    print("\nTesting web application functionality...\n")
    
    # Basic connectivity tests
    if not test_home_page():
        print("\n⚠️  Warning: Server may not be running!")
        print("Start the server with: ./start_app.sh\n")
        return False
    
    test_static_files()
    
    # API tests
    print("\n" + "-"*70)
    print("API Endpoint Tests")
    print("-"*70)
    
    cache_key = test_api_analyze()
    
    if cache_key:
        test_api_plots(cache_key)
        test_api_download(cache_key)
    
    # CLI tests
    print("\n" + "-"*70)
    print("Command-Line Tool Tests")
    print("-"*70)
    
    test_cli_tool()
    
    # Summary
    all_passed = print_summary()
    
    if all_passed:
        print("\n🎉 All tests passed! The application is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    return all_passed

if __name__ == '__main__':
    import sys
    sys.exit(0 if main() else 1)
