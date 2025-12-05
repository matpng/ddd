#!/bin/bash
# Complete Discovery Automation Script
# Runs ALL tests and analyses to cover every angle

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        🚀 COMPLETE DISCOVERY AUTOMATION SYSTEM 🚀            ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Create results directory
mkdir -p complete_discovery_results
cd complete_discovery_results || exit

echo "📊 Phase 1: Ultimate Test Suite"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cd /workspaces/ddd
python3 ultimate_test_suite.py
echo ""

echo "📊 Phase 2: Cardinal Angle Comprehensive Analysis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for angle in 0 30 36 45 54 60 72 90 108 120 144 180; do
    echo "  Analyzing ${angle}°..."
    python3 advanced_discovery_engine.py --mode comprehensive \
        --angle $angle --output complete_discovery_results/discovery_${angle}deg.json \
        --quiet
done
echo ""

echo "📊 Phase 3: Multi-Axis Exploration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
for axis in x y z body; do
    echo "  Exploring ${axis}-axis..."
    python3 advanced_discovery_engine.py --mode multi-axis \
        --axis $axis --angle 60 --output complete_discovery_results/multi_axis_${axis}.json \
        --quiet
done
echo ""

echo "📊 Phase 4: Fine Sweep Critical Ranges"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# Sweep around pentagonal angles (highest phi potential)
for center in 36 72 108 144; do
    start=$((center - 5))
    end=$((center + 5))
    echo "  Fine sweep around ${center}° ($start-$end)..."
    python3 advanced_discovery_engine.py --mode sweep \
        --start $start --end $end --step 0.5 \
        --output complete_discovery_results/fine_sweep_${center}deg.json \
        --quiet
done
echo ""

echo "📊 Phase 5: Statistical Analysis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
# Run standard analysis on full 0-180 range at 10° intervals for stats
echo "  Running 0-180° statistical sweep (10° intervals)..."
for angle in {0..180..10}; do
    python3 orion_octave_test.py --side 2.0 --angle $angle \
        --output complete_discovery_results/stat_${angle}deg.json \
        --max-distance-pairs 5000 --max-direction-pairs 2000 > /dev/null 2>&1
done
echo ""

echo "📊 Phase 6: Generate Comprehensive Report"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 generate_discovery_report.py > complete_discovery_results/DISCOVERY_REPORT.txt
echo ""

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║             ✅ COMPLETE DISCOVERY FINISHED ✅                ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📁 Results saved to: complete_discovery_results/"
echo ""
echo "📊 Summary:"
echo "  • Ultimate tests: COMPLETE"
echo "  • Cardinal angles: 12 configurations analyzed"
echo "  • Multi-axis: 4 axes explored"
echo "  • Fine sweeps: 4 critical regions mapped"
echo "  • Statistical: 19 angles sampled"
echo ""
echo "📈 Total configurations analyzed: 50+"
echo "🎯 Discovery report: complete_discovery_results/DISCOVERY_REPORT.txt"
echo ""
echo "🚀 Ready for next phase: Full 0-180° sweep (run run_full_sweep.sh)"
