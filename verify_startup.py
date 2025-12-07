#!/usr/bin/env python3
"""
Startup Verification Script
Checks all dependencies and configurations before running the app
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("  ⚠️  WARNING: Python 3.8+ recommended")
        return False
    return True

def check_dependencies():
    """Check required Python packages."""
    required = [
        'flask',
        'numpy',
        'scipy',
        'matplotlib',
        'sklearn',
        'gunicorn',
        'psutil',
        'requests'
    ]
    
    missing = []
    for package in required:
        try:
            if package == 'sklearn':
                __import__('sklearn')
            else:
                __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt")
        return False
    return True

def check_directories():
    """Check required directories exist."""
    required_dirs = [
        'autonomous_discoveries',
        'test_results',
        'static',
        'static/css',
        'static/js',
        'templates'
    ]
    
    for directory in required_dirs:
        path = Path(directory)
        if path.exists():
            print(f"✓ {directory}/")
        else:
            print(f"✗ {directory}/ - CREATING")
            path.mkdir(parents=True, exist_ok=True)
    return True

def check_files():
    """Check required files exist."""
    required_files = [
        'app.py',
        'orion_octave_test.py',
        'config.py',
        'discovery_manager.py',
        'daemon_monitor.py',
        'ml_integration.py',
        'requirements.txt',
        'templates/index.html',
        'static/js/app.js',
        'static/css/style.css'
    ]
    
    missing = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            missing.append(file_path)
    
    if missing:
        print(f"\n⚠️  Missing files: {', '.join(missing)}")
        return False
    return True

def check_env_vars():
    """Check environment variables."""
    env_vars = {
        'FLASK_ENV': 'development',
        'ENABLE_AUTONOMOUS': 'true',
        'DISCOVERY_INTERVAL': '3600'
    }
    
    for var, default in env_vars.items():
        value = os.environ.get(var, default)
        print(f"  {var}={value}")
    
    return True

def test_imports():
    """Test critical imports."""
    try:
        print("\nTesting imports...")
        from flask import Flask, jsonify
        print("✓ Flask imports")
        
        from orion_octave_test import main
        print("✓ Orion Octave imports")
        
        from discovery_manager import DiscoveryManager
        print("✓ Discovery Manager imports")
        
        from daemon_monitor import daemon_monitor
        print("✓ Daemon Monitor imports")
        
        from ml_integration import initialize_ml_integration
        print("✓ ML Integration imports")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def check_port():
    """Check if port 5000 is available."""
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5000))
        sock.close()
        
        if result == 0:
            print("⚠️  Port 5000 is already in use")
            print("   Another instance may be running")
            return False
        else:
            print("✓ Port 5000 available")
            return True
    except Exception as e:
        print(f"  Could not check port: {e}")
        return True

def main():
    """Run all checks."""
    print("=" * 70)
    print("Orion Octave Cubes - Startup Verification")
    print("=" * 70)
    
    results = {}
    
    print("\n1. Python Version")
    print("-" * 70)
    results['python'] = check_python_version()
    
    print("\n2. Dependencies")
    print("-" * 70)
    results['dependencies'] = check_dependencies()
    
    print("\n3. Directories")
    print("-" * 70)
    results['directories'] = check_directories()
    
    print("\n4. Required Files")
    print("-" * 70)
    results['files'] = check_files()
    
    print("\n5. Environment Variables")
    print("-" * 70)
    results['env'] = check_env_vars()
    
    print("\n6. Import Tests")
    print("-" * 70)
    results['imports'] = test_imports()
    
    print("\n7. Port Availability")
    print("-" * 70)
    results['port'] = check_port()
    
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for check, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {check.capitalize()}")
    
    print(f"\nScore: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 All checks passed! Ready to start the application.")
        print("\nRun: python app.py")
        return 0
    else:
        print("\n⚠️  Some checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
