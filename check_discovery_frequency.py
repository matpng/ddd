#!/usr/bin/env python3
"""Discovery Frequency Analysis"""
import json
from pathlib import Path
from datetime import datetime

# Load index
with open('autonomous_discoveries/index.json', 'r') as f:
    data = json.load(f)

print("=" * 80)
print("DISCOVERY FREQUENCY & UPDATE ANALYSIS")
print("=" * 80)

print(f"\nTotal Discoveries: {data['total_discoveries']}")
print(f"Last Updated: {data['last_updated']}")
if 'created_at' in data:
    print(f"Index Created: {data['created_at']}")

discs = data.get('discoveries', [])
print(f"\nDiscoveries in Index: {len(discs)}")

# Count by type
types = {}
for d in discs:
    dtype = d.get('type', 'unknown')
    types[dtype] = types.get(dtype, 0) + 1

print("\nDiscoveries by Type:")
for dtype, count in sorted(types.items()):
    print(f"  {dtype}: {count}")

# Check daemon status
print("\n" + "=" * 80)
print("DAEMON CONFIGURATION")
print("=" * 80)

# Parse daemon config
import re
daemon_file = Path('autonomous_discovery_daemon.py')
if daemon_file.exists():
    content = daemon_file.read_text(encoding='utf-8')
    
    # Find cycle delay
    cycle_match = re.search(r'cycle_delay:\s*int\s*=\s*(\d+)', content)
    if cycle_match:
        cycle_delay = int(cycle_match.group(1))
        print(f"\nDefault Cycle Delay: {cycle_delay} seconds ({cycle_delay/3600:.1f} hours)")
    
    # Find mode defaults
    if '--delay' in content:
        print("\nCommand line options:")
        print("  --mode: continuous | single")
        print("  --delay: custom cycle delay in seconds")

print("\n" + "=" * 80)
print("WEB APP UPDATE FREQUENCY")
print("=" * 80)

# Check web app refresh rates
templates_file = Path('templates/discoveries.html')
if templates_file.exists():
    html_content = templates_file.read_text(encoding='utf-8')
    
    # Find setInterval calls
    intervals = re.findall(r'setInterval\((\w+),\s*(\d+)\)', html_content)
    if intervals:
        print("\nAuto-refresh intervals:")
        for func, ms in intervals:
            seconds = int(ms) / 1000
            print(f"  {func}(): every {seconds:.0f} seconds ({seconds/60:.1f} minutes)")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
DISCOVERY GENERATION:
- Daemon runs in "continuous" mode by default
- Default cycle delay: 3600 seconds (1 hour)
- Each cycle generates multiple discoveries across 4 modes:
  1. angle_sweep (z-axis): 180+ angles analyzed
  2. multi_axis_scan: 4 axes × angles
  3. parameter_exploration: Various parameters
  4. critical_angle_analysis: Special angles
- Total time per cycle: ~10-30 minutes depending on complexity
- Net result: New discoveries every ~1 hour when daemon is running

WEB APP UPDATES:
- Status check: every 30 seconds
- Discovery list refresh: every 60 seconds (1 minute)
- Manual refresh available via "🔄 Refresh" button
- Real-time updates when daemon is active

CURRENT STATUS:
""")

# Check if daemon is running
print(f"- Last discovery update: {data['last_updated']}")
last_update = datetime.fromisoformat(data['last_updated'].replace('Z', '+00:00'))
now = datetime.utcnow()
time_since = (now - last_update).total_seconds()

if time_since < 300:  # 5 minutes
    print(f"- Status: ✅ RECENTLY ACTIVE ({time_since/60:.1f} minutes ago)")
elif time_since < 3600:  # 1 hour
    print(f"- Status: ⚠️  POSSIBLY ACTIVE ({time_since/60:.1f} minutes ago)")
else:
    print(f"- Status: ❌ LIKELY INACTIVE ({time_since/3600:.1f} hours ago)")

print("\nTo start continuous discovery generation:")
print("  bash discovery_service.sh start")
print("\nTo run a single cycle:")
print("  python autonomous_discovery_daemon.py --mode single")
print("\nTo check daemon status:")
print("  bash discovery_service.sh status")
print("=" * 80)
