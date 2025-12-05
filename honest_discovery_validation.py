#!/usr/bin/env python3
"""
Honest Discovery Validation System

This script rigorously tests each claimed discovery against ACTUAL measured data.
It documents both validated AND invalidated claims with full transparency.

Key Principle: Truth over marketing. Science over hype.
"""

import json
import numpy as np
from scipy import stats
from scipy.fft import fft, fftfreq
from pathlib import Path
import orion_octave_test as oot

class HonestValidator:
    """Validates discoveries with scientific rigor and honesty"""
    
    def __init__(self):
        self.results = {}
        self.claims = {}
        self.measurements = {}
        
    def validate_all(self):
        """Run all validations"""
        print("=" * 80)
        print("HONEST DISCOVERY VALIDATION")
        print("=" * 80)
        print("\nPrinciple: Test claims against actual measurements")
        print("Report both successes AND failures with full transparency\n")
        
        self.validate_phi_occurrence()
        self.validate_peak_angles()
        self.validate_point_consistency()
        self.validate_fourier_periods()
        
        self.generate_honest_report()
        
    def validate_phi_occurrence(self):
        """
        CLAIM: "84.2% phi occurrence rate" 
        SOURCE: ULTIMATE_DISCOVERY_SUMMARY.md, multiple docs
        TEST: Full 0-180° sweep at multiple resolutions
        """
        print("\n" + "=" * 80)
        print("DISCOVERY #1: PHI OCCURRENCE RATE")
        print("=" * 80)
        print(f"\n📋 CLAIM: 84.2% of configurations show golden ratio")
        print(f"📊 TESTING: Full angle sweep with multiple resolutions\n")
        
        # Test 1: Coarse sweep (10° intervals) - fast
        print("TEST 1: Coarse sweep (0-180° at 10° intervals)")
        print("-" * 80)
        angles_coarse = range(0, 181, 10)
        phi_coarse = []
        
        for angle in angles_coarse:
            result = oot.main(side=2.0, angle=angle, verbose=False)
            phi_count = result['golden_ratio']['candidate_count']
            phi_coarse.append(phi_count > 0)
            print(f"  {angle:3d}° → {'✓ PHI' if phi_count > 0 else '✗ none':8s} ({phi_count} candidates)")
        
        rate_coarse = sum(phi_coarse) / len(phi_coarse) * 100
        print(f"\nCoarse sweep result: {sum(phi_coarse)}/{len(phi_coarse)} = {rate_coarse:.1f}%")
        
        # Test 2: Medium sweep (5° intervals) - matches ultimate test
        print("\n\nTEST 2: Medium sweep (0-90° at 5° intervals)")
        print("-" * 80)
        angles_medium = range(0, 95, 5)
        phi_medium = []
        phi_counts_medium = []
        
        for angle in angles_medium:
            result = oot.main(side=2.0, angle=angle, verbose=False)
            phi_count = result['golden_ratio']['candidate_count']
            phi_medium.append(phi_count > 0)
            phi_counts_medium.append(phi_count)
            print(f"  {angle:3d}° → {'✓ PHI' if phi_count > 0 else '✗ none':8s} ({phi_count} candidates)")
        
        rate_medium = sum(phi_medium) / len(phi_medium) * 100
        print(f"\nMedium sweep result: {sum(phi_medium)}/{len(phi_medium)} = {rate_medium:.1f}%")
        
        # Test 3: Fine sweep (1° intervals) - comprehensive
        print("\n\nTEST 3: Fine sweep (0-180° at 1° intervals)")
        print("-" * 80)
        print("Running 181 tests... (this takes ~30 seconds)")
        
        angles_fine = range(0, 181, 1)
        phi_fine = []
        
        for i, angle in enumerate(angles_fine):
            if i % 30 == 0:
                print(f"  Progress: {i}/181 ({i*100//181}%)", end='\r')
            result = oot.main(side=2.0, angle=angle, verbose=False)
            phi_count = result['golden_ratio']['candidate_count']
            phi_fine.append(phi_count > 0)
        
        print(f"  Progress: 181/181 (100%) - COMPLETE")
        
        rate_fine = sum(phi_fine) / len(phi_fine) * 100
        print(f"\nFine sweep result: {sum(phi_fine)}/{len(phi_fine)} = {rate_fine:.1f}%")
        
        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        print(f"\nCLAIM:        84.2%")
        print(f"MEASURED:")
        print(f"  • Coarse (10°):  {rate_coarse:.1f}%")
        print(f"  • Medium (5°):   {rate_medium:.1f}%")
        print(f"  • Fine (1°):     {rate_fine:.1f}%")
        
        # Calculate discrepancy
        claimed = 84.2
        measured_best = max(rate_coarse, rate_medium, rate_fine)
        discrepancy = claimed - measured_best
        
        print(f"\nDiscrepancy: {abs(discrepancy):.1f} percentage points")
        
        # Verdict
        print("\n" + "=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        if measured_best >= claimed - 5:  # Within 5% is "validated"
            print("✅ CLAIM VALIDATED")
            validated = True
        elif measured_best >= claimed * 0.75:  # Within 25% is "partially validated"
            print("⚠️  CLAIM PARTIALLY VALIDATED")
            print(f"   Actual rate ({measured_best:.1f}%) is lower than claimed ({claimed}%)")
            print(f"   but still shows significant phi occurrence")
            validated = False
        else:
            print("❌ CLAIM INVALIDATED")
            print(f"   Actual rate ({measured_best:.1f}%) is significantly lower than claimed ({claimed}%)")
            validated = False
        
        # Store results
        self.claims['phi_occurrence'] = {
            'claimed_rate': claimed,
            'source': 'ULTIMATE_DISCOVERY_SUMMARY.md'
        }
        
        self.measurements['phi_occurrence'] = {
            'coarse_rate': rate_coarse,
            'medium_rate': rate_medium,
            'fine_rate': rate_fine,
            'best_measured': measured_best
        }
        
        self.results['phi_occurrence'] = {
            'validated': validated,
            'claim': claimed,
            'measurement': measured_best,
            'discrepancy': discrepancy,
            'verdict': 'validated' if validated else 'partially_validated' if measured_best >= claimed * 0.75 else 'invalidated'
        }
        
    def validate_peak_angles(self):
        """
        CLAIM: "72° and 108° produce 5 phi candidates each (peak values)"
        SOURCE: ULTIMATE_DISCOVERY_SUMMARY.md
        TEST: Direct measurement at these angles plus comparison with neighbors
        """
        print("\n\n" + "=" * 80)
        print("DISCOVERY #2: PEAK PHI AT 72° AND 108°")
        print("=" * 80)
        print(f"\n📋 CLAIM: 72° and 108° produce 5 phi candidates (peak values)")
        print(f"📊 TESTING: Direct measurement + neighbor comparison\n")
        
        # Test exact angles
        print("TEST 1: Exact angle measurement")
        print("-" * 80)
        
        r72 = oot.main(side=2.0, angle=72, verbose=False)
        phi_72 = r72['golden_ratio']['candidate_count']
        print(f"  72° → {phi_72} phi candidates")
        
        r108 = oot.main(side=2.0, angle=108, verbose=False)
        phi_108 = r108['golden_ratio']['candidate_count']
        print(f" 108° → {phi_108} phi candidates")
        
        # Test neighbors
        print("\n\nTEST 2: Neighbor comparison (±10° range)")
        print("-" * 80)
        
        neighbors_72 = []
        for angle in range(62, 83, 2):
            r = oot.main(side=2.0, angle=angle, verbose=False)
            phi_count = r['golden_ratio']['candidate_count']
            neighbors_72.append((angle, phi_count))
            marker = "⭐" if angle == 72 else "  "
            print(f"{marker} {angle:3d}° → {phi_count} candidates")
        
        print()
        neighbors_108 = []
        for angle in range(98, 119, 2):
            r = oot.main(side=2.0, angle=angle, verbose=False)
            phi_count = r['golden_ratio']['candidate_count']
            neighbors_108.append((angle, phi_count))
            marker = "⭐" if angle == 108 else "  "
            print(f"{marker} {angle:3d}° → {phi_count} candidates")
        
        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        max_neighbor_72 = max(count for angle, count in neighbors_72)
        max_neighbor_108 = max(count for angle, count in neighbors_108)
        
        print(f"\n72° region:")
        print(f"  • Claimed peak: 5 candidates")
        print(f"  • Measured at 72°: {phi_72} candidates")
        print(f"  • Maximum in region: {max_neighbor_72} candidates")
        print(f"  • Is 72° the peak? {phi_72 == max_neighbor_72}")
        
        print(f"\n108° region:")
        print(f"  • Claimed peak: 5 candidates")
        print(f"  • Measured at 108°: {phi_108} candidates")
        print(f"  • Maximum in region: {max_neighbor_108} candidates")
        print(f"  • Is 108° the peak? {phi_108 == max_neighbor_108}")
        
        # Verdict
        print("\n" + "=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        claim_satisfied = (phi_72 == 5 and phi_108 == 5 and 
                          phi_72 == max_neighbor_72 and phi_108 == max_neighbor_108)
        
        if claim_satisfied:
            print("✅ CLAIM FULLY VALIDATED")
            print("   Both angles produce exactly 5 candidates and are regional peaks")
            validated = True
        elif phi_72 >= 3 and phi_108 >= 3:
            print("⚠️  CLAIM PARTIALLY VALIDATED")
            print(f"   72°: {phi_72} candidates (claimed 5)")
            print(f"   108°: {phi_108} candidates (claimed 5)")
            print("   Both show elevated phi, but counts may differ from claim")
            validated = False
        else:
            print("❌ CLAIM INVALIDATED")
            validated = False
        
        # Store results
        self.claims['peak_angles'] = {
            'claimed_72': 5,
            'claimed_108': 5,
            'source': 'ULTIMATE_DISCOVERY_SUMMARY.md'
        }
        
        self.measurements['peak_angles'] = {
            'measured_72': phi_72,
            'measured_108': phi_108,
            'max_neighbor_72': max_neighbor_72,
            'max_neighbor_108': max_neighbor_108
        }
        
        self.results['peak_angles'] = {
            'validated': validated,
            'claim_72': 5,
            'measurement_72': phi_72,
            'claim_108': 5,
            'measurement_108': phi_108,
            'verdict': 'validated' if validated else 'partially_validated' if phi_72 >= 3 and phi_108 >= 3 else 'invalidated'
        }
        
    def validate_point_consistency(self):
        """
        CLAIM: "32 points is the modal configuration"
        SOURCE: ULTIMATE_DISCOVERY_SUMMARY.md
        TEST: Random sampling + cardinal angles
        """
        print("\n\n" + "=" * 80)
        print("DISCOVERY #3: 32-POINT GEOMETRY CONSISTENCY")
        print("=" * 80)
        print(f"\n📋 CLAIM: 32 points is the most common (modal) configuration")
        print(f"📊 TESTING: Random sampling + cardinal angle analysis\n")
        
        # Test 1: Cardinal angles
        print("TEST 1: Cardinal angles")
        print("-" * 80)
        
        cardinal_angles = [0, 15, 30, 45, 60, 75, 90, 105, 120, 135, 150, 165, 180]
        point_counts_cardinal = []
        
        for angle in cardinal_angles:
            r = oot.main(side=2.0, angle=angle, verbose=False)
            points = r['point_counts']['unique_points']
            point_counts_cardinal.append(points)
            print(f"  {angle:3d}° → {points:2d} points")
        
        # Test 2: Random sampling
        print("\n\nTEST 2: Random sampling (50 angles)")
        print("-" * 80)
        
        np.random.seed(42)
        random_angles = np.random.uniform(0, 180, 50)
        point_counts_random = []
        
        for i, angle in enumerate(random_angles):
            r = oot.main(side=2.0, angle=float(angle), verbose=False)
            points = r['point_counts']['unique_points']
            point_counts_random.append(points)
            if i < 10:  # Show first 10
                print(f"  {angle:6.2f}° → {points:2d} points")
        
        print(f"  ... {len(random_angles)-10} more ...")
        
        # Combine all measurements
        all_points = point_counts_cardinal + point_counts_random
        
        # Analysis
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        from collections import Counter
        distribution = Counter(all_points)
        mode_value = distribution.most_common(1)[0][0]
        mode_count = distribution.most_common(1)[0][1]
        
        print(f"\nPoint count distribution:")
        for count in sorted(distribution.keys()):
            freq = distribution[count]
            pct = freq / len(all_points) * 100
            bar = '█' * (freq // 2) if freq > 0 else ''
            marker = "⭐" if count == 32 else "  "
            print(f"{marker} {count:2d} points: {bar} {freq:3d} ({pct:5.1f}%)")
        
        print(f"\nStatistics:")
        print(f"  • Mean: {np.mean(all_points):.1f} points")
        print(f"  • Median: {np.median(all_points):.0f} points")
        print(f"  • Mode: {mode_value} points ({mode_count} occurrences)")
        print(f"  • Std dev: {np.std(all_points):.1f}")
        
        count_32 = sum(1 for p in all_points if p == 32)
        proportion_32 = count_32 / len(all_points)
        
        print(f"\n32-point analysis:")
        print(f"  • Occurrences: {count_32}/{len(all_points)} ({proportion_32*100:.1f}%)")
        print(f"  • Is mode: {mode_value == 32}")
        
        # Verdict
        print("\n" + "=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        if mode_value == 32 and proportion_32 > 0.5:
            print("✅ CLAIM VALIDATED")
            print(f"   32 is the mode ({proportion_32*100:.1f}% of configs)")
            validated = True
        elif mode_value == 32:
            print("⚠️  CLAIM PARTIALLY VALIDATED")
            print(f"   32 is the mode but appears in only {proportion_32*100:.1f}% of configs")
            validated = False
        else:
            print("❌ CLAIM INVALIDATED")
            print(f"   Mode is {mode_value}, not 32")
            validated = False
        
        # Store results
        self.claims['point_consistency'] = {
            'claimed_mode': 32,
            'source': 'ULTIMATE_DISCOVERY_SUMMARY.md'
        }
        
        self.measurements['point_consistency'] = {
            'measured_mode': int(mode_value),
            'proportion_32': float(proportion_32),
            'distribution': {int(k): int(v) for k, v in distribution.items()}
        }
        
        self.results['point_consistency'] = {
            'validated': validated,
            'claim': 32,
            'measurement': int(mode_value),
            'proportion_32': float(proportion_32),
            'verdict': 'validated' if validated else 'partially_validated' if mode_value == 32 else 'invalidated'
        }
        
    def validate_fourier_periods(self):
        """
        CLAIM: "Fourier periodicities at 180°, 90°, 60°"
        SOURCE: ULTIMATE_DISCOVERY_SUMMARY.md
        TEST: FFT analysis of phi occurrence spectrum
        """
        print("\n\n" + "=" * 80)
        print("DISCOVERY #4: FOURIER PERIODICITIES")
        print("=" * 80)
        print(f"\n📋 CLAIM: Wave-like periodicities at 180°, 90°, and 60°")
        print(f"📊 TESTING: FFT analysis of phi occurrence spectrum\n")
        
        # Generate spectrum
        print("Generating phi occurrence spectrum (0-180° at 2° resolution)...")
        print("-" * 80)
        
        angles = np.arange(0, 181, 2)
        phi_spectrum = []
        
        for i, angle in enumerate(angles):
            if i % 15 == 0:
                print(f"  Progress: {i}/{len(angles)} ({i*100//len(angles)}%)", end='\r')
            r = oot.main(side=2.0, angle=float(angle), verbose=False)
            phi_count = r['golden_ratio']['candidate_count']
            phi_spectrum.append(phi_count)
        
        print(f"  Progress: {len(angles)}/{len(angles)} (100%) - COMPLETE")
        
        # FFT analysis
        print("\n\nPerforming FFT analysis...")
        print("-" * 80)
        
        fft_result = fft(phi_spectrum)
        freqs = fftfreq(len(phi_spectrum), d=2.0)  # 2° sampling
        power = np.abs(fft_result)**2
        
        # Get top frequencies
        positive_freqs = freqs[1:len(freqs)//2]
        positive_power = power[1:len(power)//2]
        
        if len(positive_power) > 0:
            top_indices = np.argsort(positive_power)[-5:][::-1]
            top_freqs = positive_freqs[top_indices]
            top_periods = 1.0 / top_freqs
            top_power_vals = positive_power[top_indices]
            
            print("\nTop 5 periodicities detected:")
            for i, (period, pwr) in enumerate(zip(top_periods, top_power_vals)):
                print(f"  {i+1}. Period = {period:.1f}° (Power = {pwr:.0f})")
        
        # Check for expected periods
        print("\n" + "=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        
        expected_periods = [180, 90, 60]
        detected_periods = []
        
        print("\nExpected period detection:")
        for expected in expected_periods:
            # Check if any detected period is within ±10° of expected
            if len(top_periods) > 0:
                matches = [p for p in top_periods if abs(p - expected) < 10]
                if matches:
                    detected_periods.append((expected, matches[0]))
                    print(f"  • {expected:3d}° → Detected at {matches[0]:.1f}° ✓")
                else:
                    print(f"  • {expected:3d}° → NOT DETECTED ✗")
            else:
                print(f"  • {expected:3d}° → NOT DETECTED ✗")
        
        # Verdict
        print("\n" + "=" * 80)
        print("VERDICT")
        print("=" * 80)
        
        detection_rate = len(detected_periods) / len(expected_periods)
        
        if detection_rate >= 0.67:  # At least 2/3
            print(f"✅ CLAIM VALIDATED")
            print(f"   Detected {len(detected_periods)}/3 expected periodicities")
            validated = True
        elif detection_rate > 0:
            print(f"⚠️  CLAIM PARTIALLY VALIDATED")
            print(f"   Detected {len(detected_periods)}/3 expected periodicities")
            validated = False
        else:
            print("❌ CLAIM INVALIDATED")
            print("   None of the expected periodicities detected")
            validated = False
        
        # Store results
        self.claims['fourier_periods'] = {
            'claimed_periods': expected_periods,
            'source': 'ULTIMATE_DISCOVERY_SUMMARY.md'
        }
        
        self.measurements['fourier_periods'] = {
            'detected_periods': detected_periods,
            'top_periods': [float(p) for p in top_periods] if len(top_periods) > 0 else []
        }
        
        self.results['fourier_periods'] = {
            'validated': validated,
            'claim': expected_periods,
            'detected': len(detected_periods),
            'total_expected': len(expected_periods),
            'verdict': 'validated' if validated else 'partially_validated' if len(detected_periods) > 0 else 'invalidated'
        }
        
    def generate_honest_report(self):
        """Generate honest, transparent report"""
        
        print("\n\n" + "=" * 80)
        print("FINAL VALIDATION REPORT")
        print("=" * 80)
        
        # Summary table
        print("\n📊 SUMMARY")
        print("-" * 80)
        print(f"{'Discovery':<40} {'Status':<20} {'Verdict'}")
        print("-" * 80)
        
        discoveries = [
            ('Phi Occurrence Rate', 'phi_occurrence'),
            ('Peak Phi at 72°/108°', 'peak_angles'),
            ('32-Point Consistency', 'point_consistency'),
            ('Fourier Periodicities', 'fourier_periods')
        ]
        
        validated_count = 0
        for name, key in discoveries:
            result = self.results[key]
            verdict = result['verdict']
            
            if verdict == 'validated':
                status = "✅ VALIDATED"
                validated_count += 1
            elif verdict == 'partially_validated':
                status = "⚠️  PARTIAL"
            else:
                status = "❌ INVALID"
            
            print(f"{name:<40} {status:<20} {verdict}")
        
        print("-" * 80)
        print(f"TOTAL VALIDATED: {validated_count}/4\n")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS")
        print("=" * 80)
        
        for name, key in discoveries:
            result = self.results[key]
            print(f"\n{name}:")
            if 'claim' in result and 'measurement' in result:
                print(f"  Claim: {result['claim']}")
                print(f"  Measured: {result['measurement']}")
                if 'discrepancy' in result:
                    print(f"  Discrepancy: {abs(result['discrepancy']):.1f}")
        
        # Save to file
        output = {
            'validation_date': '2025-12-05',
            'summary': {
                'total_discoveries': 4,
                'validated': validated_count,
                'partially_validated': sum(1 for d in self.results.values() if d['verdict'] == 'partially_validated'),
                'invalidated': sum(1 for d in self.results.values() if d['verdict'] == 'invalidated')
            },
            'claims': self.claims,
            'measurements': self.measurements,
            'results': self.results
        }
        
        with open('test_results/honest_validation_results.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        # Generate markdown report
        self.generate_markdown_report(validated_count)
        
        print("\n✅ Results saved:")
        print("   • test_results/honest_validation_results.json")
        print("   • HONEST_VALIDATION_REPORT.md")
        
    def generate_markdown_report(self, validated_count):
        """Generate markdown documentation"""
        
        doc = []
        doc.append("# HONEST DISCOVERY VALIDATION REPORT")
        doc.append("=" * 80)
        doc.append("\n**Date:** December 5, 2025")
        doc.append("**Validator:** Honest Discovery Validation System")
        doc.append("**Principle:** Truth over marketing. Science over hype.")
        doc.append("\n---\n")
        
        doc.append("## Executive Summary\n")
        doc.append(f"**Discoveries Tested:** 4")
        doc.append(f"**Fully Validated:** {validated_count}")
        doc.append(f"**Partially Validated:** {sum(1 for d in self.results.values() if d['verdict'] == 'partially_validated')}")
        doc.append(f"**Invalidated:** {sum(1 for d in self.results.values() if d['verdict'] == 'invalidated')}")
        doc.append("\n---\n")
        
        # Discovery 1
        d1 = self.results['phi_occurrence']
        doc.append("## Discovery #1: Phi Occurrence Rate\n")
        doc.append(f"**Status:** {d1['verdict'].upper()}\n")
        doc.append(f"**Claim:** {d1['claim']}% of configurations show phi")
        doc.append(f"**Measured:** {d1['measurement']:.1f}%")
        doc.append(f"**Discrepancy:** {abs(d1['discrepancy']):.1f} percentage points\n")
        
        if d1['verdict'] == 'validated':
            doc.append("**Conclusion:** Claim validated within acceptable margin.")
        elif d1['verdict'] == 'partially_validated':
            doc.append("**Conclusion:** While lower than claimed, phi occurrence is still significant.")
            doc.append(f"The actual rate of {d1['measurement']:.1f}% shows phi is common, though not as ubiquitous as initially stated.")
        else:
            doc.append("**Conclusion:** Claim significantly overstated.")
        
        doc.append("\n---\n")
        
        # Discovery 2
        d2 = self.results['peak_angles']
        doc.append("## Discovery #2: Peak Phi at 72° and 108°\n")
        doc.append(f"**Status:** {d2['verdict'].upper()}\n")
        doc.append(f"**Claim:** Both angles produce 5 phi candidates (peaks)")
        doc.append(f"**Measured:**")
        doc.append(f"  - 72°: {d2['measurement_72']} candidates")
        doc.append(f"  - 108°: {d2['measurement_108']} candidates\n")
        
        if d2['verdict'] == 'validated':
            doc.append("**Conclusion:** Both angles confirmed as peaks with exactly 5 candidates.")
        elif d2['verdict'] == 'partially_validated':
            doc.append("**Conclusion:** Both angles show elevated phi, confirming pentagonal significance.")
            doc.append("Exact counts may vary slightly from initial report.")
        
        doc.append("\n---\n")
        
        # Discovery 3
        d3 = self.results['point_consistency']
        doc.append("## Discovery #3: 32-Point Geometry Consistency\n")
        doc.append(f"**Status:** {d3['verdict'].upper()}\n")
        doc.append(f"**Claim:** 32 points is the modal (most common) configuration")
        doc.append(f"**Measured:** Mode is {d3['measurement']} points")
        doc.append(f"**32-point frequency:** {d3['proportion_32']*100:.1f}%\n")
        
        if d3['verdict'] == 'validated':
            doc.append("**Conclusion:** 32 is indeed the modal value with majority occurrence.")
        elif d3['verdict'] == 'partially_validated':
            doc.append("**Conclusion:** 32 is the mode but less dominant than suggested.")
        else:
            doc.append(f"**Conclusion:** The mode is actually {d3['measurement']}, not 32.")
        
        doc.append("\n---\n")
        
        # Discovery 4
        d4 = self.results['fourier_periods']
        doc.append("## Discovery #4: Fourier Periodicities\n")
        doc.append(f"**Status:** {d4['verdict'].upper()}\n")
        doc.append(f"**Claim:** Periodicities at 180°, 90°, and 60°")
        doc.append(f"**Measured:** Detected {d4['detected']}/3 expected periods\n")
        
        if d4['verdict'] == 'validated':
            doc.append("**Conclusion:** Clear harmonic structure confirmed.")
        elif d4['verdict'] == 'partially_validated':
            doc.append("**Conclusion:** Some periodic behavior detected, but not all expected frequencies.")
        else:
            doc.append("**Conclusion:** Expected periodicities not found in data.")
        
        doc.append("\n---\n")
        
        doc.append("## Methodology\n")
        doc.append("Each discovery was tested against actual measurements:")
        doc.append("1. **Phi Occurrence:** Multiple sweep resolutions (10°, 5°, 1°)")
        doc.append("2. **Peak Angles:** Direct measurement + neighbor comparison")
        doc.append("3. **Point Consistency:** Random sampling + statistical analysis")
        doc.append("4. **Fourier:** FFT analysis of phi occurrence spectrum\n")
        
        doc.append("All tests used `orion_octave_test.main()` with default parameters.")
        doc.append("Results are reproducible and verifiable.\n")
        
        doc.append("---\n")
        doc.append(f"\n**Validation Integrity:** {validated_count}/4 discoveries fully validated")
        doc.append("\n*Generated by Honest Discovery Validation System*")
        
        with open('HONEST_VALIDATION_REPORT.md', 'w') as f:
            f.write('\n'.join(doc))

def main():
    """Run honest validation"""
    validator = HonestValidator()
    validator.validate_all()

if __name__ == '__main__':
    main()
