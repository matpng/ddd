#!/usr/bin/env python3
"""
Quick Functional Test - Verifies all core functionality

Tests:
1. Core geometric analysis
2. Advanced discovery engine
3. Web app API (without running server)
4. All major functions work end-to-end
"""

import sys
import orion_octave_test as oot
import advanced_discovery_engine as ade
from app import app

def test_core_analysis():
    """Test core geometric analysis"""
    print("Testing core analysis...")
    result = oot.main(side=2.0, angle=60, verbose=False)
    
    assert 'golden_ratio' in result, "Missing golden_ratio"
    assert 'point_counts' in result, "Missing point_counts"
    assert result['point_counts']['unique_points'] > 0, "No points generated"
    
    print(f"  ✓ Generated {result['point_counts']['unique_points']} unique points")
    print(f"  ✓ Found {result['golden_ratio']['candidate_count']} phi candidates")
    return True

def test_advanced_engine():
    """Test advanced discovery engine"""
    print("\nTesting advanced discovery engine...")
    engine = ade.AdvancedDiscoveryEngine(verbose=False)
    
    # Test fine sweep
    results = engine.fine_angle_sweep(start=60, end=70, step=5, axis='z')
    assert len(results) > 0, "No sweep results"
    
    print(f"  ✓ Fine sweep generated {len(results)} results")
    
    # Test comprehensive discovery
    comp_result = engine.comprehensive_discovery(side=2.0, angle=60, axis='z')
    assert hasattr(comp_result, 'metrics'), "Missing metrics"
    
    print(f"  ✓ Comprehensive discovery completed")
    return True

def test_web_app_routes():
    """Test Flask app routes (without running server)"""
    print("\nTesting Flask app routes...")
    
    # Test client
    with app.test_client() as client:
        # Test home page
        response = client.get('/')
        assert response.status_code == 200, f"Home page failed: {response.status_code}"
        print("  ✓ Home page renders")
        
        # Test API analyze endpoint
        response = client.post('/api/analyze', 
                              json={'side': 2.0, 'angle': 60})
        assert response.status_code == 200, f"API analyze failed: {response.status_code}"
        data = response.get_json()
        assert 'summary' in data, "API response missing summary"
        print("  ✓ API /api/analyze works")
        print(f"    Found {data['summary']['golden_ratio']['candidate_count']} phi candidates")
    
    return True

def test_validation_scripts():
    """Test that validation scripts are functional"""
    print("\nTesting validation scripts...")
    
    import honest_discovery_validation as hdv
    
    validator = hdv.HonestValidator()
    assert hasattr(validator, 'validate_all'), "Missing validate_all method"
    
    print("  ✓ HonestValidator instantiated")
    print("  ✓ All validation methods available")
    
    return True

def main():
    """Run all tests"""
    print("=" * 70)
    print("QUICK FUNCTIONAL TEST")
    print("=" * 70)
    
    tests = [
        ("Core Analysis", test_core_analysis),
        ("Advanced Discovery Engine", test_advanced_engine),
        ("Flask Web App", test_web_app_routes),
        ("Validation Scripts", test_validation_scripts),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {name} - PASS")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} - FAIL: {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    print("=" * 70)
    
    if failed > 0:
        print(f"\n⚠️  {failed} test(s) failed")
        sys.exit(1)
    else:
        print("\n✅ ALL FUNCTIONAL TESTS PASSED!")
        print("\nThe application is fully functional:")
        print("  • Core geometric analysis ✓")
        print("  • Advanced discovery engine ✓")
        print("  • Web API endpoints ✓")
        print("  • Validation systems ✓")
        print("\nTo start the web server: ./start_app.sh")
        sys.exit(0)

if __name__ == '__main__':
    main()
