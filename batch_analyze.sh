#!/bin/bash
# Batch analysis script for exploring multiple rotation angles
#
# Usage:
#   ./batch_analyze.sh [output_dir]
#
# This script runs the Orion Octave test with various rotation angles
# and saves the results for comparison.

set -e

OUTPUT_DIR="${1:-results}"
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "Orion Octave Cubes - Batch Analysis"
echo "=========================================="
echo ""
echo "Output directory: $OUTPUT_DIR"
echo ""

# Define angles to test
ANGLES=(15 30 45 60 72 90)

for angle in "${ANGLES[@]}"; do
    echo "----------------------------------------"
    echo "Testing rotation angle: ${angle}°"
    echo "----------------------------------------"
    
    output_file="${OUTPUT_DIR}/results_${angle}deg.json"
    
    python3 orion_octave_test.py \
        --angle "$angle" \
        --output "$output_file" \
        --quiet
    
    echo "✓ Completed: ${angle}°"
    echo ""
done

echo "=========================================="
echo "Batch analysis complete!"
echo "=========================================="
echo ""
echo "Results saved in: $OUTPUT_DIR/"
echo ""
echo "Files generated:"
ls -lh "$OUTPUT_DIR"/*.json
echo ""
echo "To visualize results:"
echo "  python3 visualize.py ${OUTPUT_DIR}/results_30deg.json --summary summary.png"
echo ""
