#!/usr/bin/env python3
"""
Comprehensive App Health Check
Tests all critical endpoints and functionality
"""

import requests
import json
import sys
from datetime import datetime

# Base URL - change to your deployment URL
BASE_URL = "https://the-codex-x6hs.onrender.com"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"{text}")
    print(f"{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")

def test_endpoint(name, url, expected_keys=None, method='GET'):
    """Test an API endpoint"""
    try:
        if method == 'GET':
            response = requests.get(url, timeout=30)
        else:
            response = requests.post(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check expected keys
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    print_warning(f"{name}: Missing keys {missing_keys}")
                    return False, data
            
            print_success(f"{name}: OK")
            return True, data
        else:
            print_error(f"{name}: HTTP {response.status_code}")
            return False, None
            
    except Exception as e:
        print_error(f"{name}: {str(e)}")
        return False, None

def main():
    print_header("🔍 COMPREHENSIVE APP HEALTH CHECK")
    print(f"Target: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = {
        'passed': 0,
        'failed': 0,
        'warnings': 0
    }
    
    # Test 1: Basic Health
    print_header("1. BASIC HEALTH CHECKS")
    success, _ = test_endpoint("Health endpoint", f"{BASE_URL}/health", ['success', 'status'])
    results['passed' if success else 'failed'] += 1
    
    success, _ = test_endpoint("Healthz endpoint", f"{BASE_URL}/healthz", ['success', 'status'])
    results['passed' if success else 'failed'] += 1
    
    # Test 2: Page Accessibility
    print_header("2. PAGE ACCESSIBILITY")
    for page in ['/', '/discoveries', '/admin']:
        try:
            response = requests.get(f"{BASE_URL}{page}", timeout=30)
            if response.status_code == 200:
                print_success(f"Page {page}: Accessible")
                results['passed'] += 1
            else:
                print_error(f"Page {page}: HTTP {response.status_code}")
                results['failed'] += 1
        except Exception as e:
            print_error(f"Page {page}: {str(e)}")
            results['failed'] += 1
    
    # Test 3: Discovery API
    print_header("3. DISCOVERY API ENDPOINTS")
    
    # Get daemon status
    success, daemon_data = test_endpoint(
        "Daemon status",
        f"{BASE_URL}/api/daemon/health",
        ['running', 'discoveries_today', 'total_discoveries']
    )
    results['passed' if success else 'failed'] += 1
    
    # Get latest discoveries
    success, latest_data = test_endpoint(
        "Latest discoveries",
        f"{BASE_URL}/api/discoveries/latest?count=10",
        ['success', 'discoveries']
    )
    results['passed' if success else 'failed'] += 1
    
    # Get all discoveries
    success, all_data = test_endpoint(
        "All discoveries",
        f"{BASE_URL}/api/discoveries/all",
        ['success', 'total', 'discoveries']
    )
    results['passed' if success else 'failed'] += 1
    
    # Get discovery stats
    success, stats_data = test_endpoint(
        "Discovery statistics",
        f"{BASE_URL}/api/discoveries/stats",
        ['success', 'stats']
    )
    results['passed' if success else 'failed'] += 1
    
    # Test 4: Specific Discovery Access
    print_header("4. INDIVIDUAL DISCOVERY TESTS")
    
    if latest_data and 'discoveries' in latest_data and len(latest_data['discoveries']) > 0:
        test_discovery = latest_data['discoveries'][0]
        disc_id = test_discovery.get('id')
        
        if disc_id:
            print(f"Testing with discovery ID: {disc_id}")
            
            # Test discovery retrieval
            success, disc_data = test_endpoint(
                "Get discovery by ID",
                f"{BASE_URL}/api/discoveries/{disc_id}",
                ['success', 'discovery']
            )
            results['passed' if success else 'failed'] += 1
            
            if disc_data and 'discovery' in disc_data:
                discovery = disc_data['discovery']
                
                # Validate discovery structure
                required_fields = ['id', 'type', 'timestamp', 'data']
                missing = [f for f in required_fields if f not in discovery]
                
                if missing:
                    print_warning(f"Discovery missing fields: {missing}")
                    results['warnings'] += 1
                else:
                    print_success("Discovery has all required fields")
                    results['passed'] += 1
                
                # Check data structure
                if 'data' in discovery:
                    data = discovery['data']
                    if 'summary' in data:
                        print_success("Discovery has summary data")
                        summary = data['summary']
                        print(f"  - Unique points: {summary.get('unique_points', 'N/A')}")
                        print(f"  - Golden ratio: {summary.get('golden_ratio_candidates', 'N/A')}")
                        print(f"  - Unique distances: {summary.get('unique_distances', 'N/A')}")
                    else:
                        print_warning("Discovery missing summary data")
                        results['warnings'] += 1
                    
                    if 'title' in data:
                        print_success(f"Discovery has title: '{data['title']}'")
                    else:
                        print_warning("Discovery missing title (will use fallback)")
                        results['warnings'] += 1
            
            # Test PDF download endpoint (don't download, just check it's accessible)
            try:
                response = requests.head(f"{BASE_URL}/api/discoveries/{disc_id}/paper", timeout=30)
                if response.status_code in [200, 302]:
                    print_success("PDF download endpoint: Accessible")
                    results['passed'] += 1
                else:
                    print_error(f"PDF download endpoint: HTTP {response.status_code}")
                    results['failed'] += 1
            except Exception as e:
                print_error(f"PDF download endpoint: {str(e)}")
                results['failed'] += 1
            
            # Test JSON download
            try:
                response = requests.get(f"{BASE_URL}/api/discoveries/download/{disc_id}", timeout=30)
                if response.status_code == 200:
                    print_success("JSON download: OK")
                    results['passed'] += 1
                else:
                    print_error(f"JSON download: HTTP {response.status_code}")
                    results['failed'] += 1
            except Exception as e:
                print_error(f"JSON download: {str(e)}")
                results['failed'] += 1
        else:
            print_error("No discovery ID found in latest discoveries")
            results['failed'] += 1
    else:
        print_warning("No discoveries available for testing")
        results['warnings'] += 1
    
    # Test 5: Discovery Types
    print_header("5. DISCOVERY TYPE VALIDATION")
    
    if all_data and 'discoveries' in all_data:
        discoveries = all_data['discoveries']
        types = set()
        
        for disc in discoveries:
            if 'type' in disc:
                types.add(disc['type'])
        
        print(f"Found {len(discoveries)} total discoveries")
        print(f"Discovery types: {', '.join(types) if types else 'None'}")
        
        if types:
            print_success(f"Discovered {len(types)} unique types")
            results['passed'] += 1
        else:
            print_warning("No discovery types found")
            results['warnings'] += 1
    
    # Test 6: Daemon Status
    print_header("6. DAEMON STATUS CHECK")
    
    if daemon_data:
        print(f"Daemon running: {daemon_data.get('running', 'Unknown')}")
        print(f"Discoveries today: {daemon_data.get('discoveries_today', 0)}")
        print(f"Total discoveries: {daemon_data.get('total_discoveries', 0)}")
        print(f"Last discovery: {daemon_data.get('last_discovery', 'Never')}")
        
        if daemon_data.get('running'):
            print_success("Daemon is ACTIVE")
            results['passed'] += 1
        else:
            print_warning("Daemon is INACTIVE")
            results['warnings'] += 1
    
    # Final Report
    print_header("📊 FINAL REPORT")
    
    total_tests = results['passed'] + results['failed'] + results['warnings']
    success_rate = (results['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"Total Tests: {total_tests}")
    print(f"{Colors.GREEN}Passed: {results['passed']}{Colors.END}")
    print(f"{Colors.RED}Failed: {results['failed']}{Colors.END}")
    print(f"{Colors.YELLOW}Warnings: {results['warnings']}{Colors.END}")
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if results['failed'] == 0:
        print(f"\n{Colors.GREEN}✓ ALL CRITICAL TESTS PASSED!{Colors.END}")
        return 0
    else:
        print(f"\n{Colors.RED}✗ SOME TESTS FAILED - CHECK LOGS{Colors.END}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
