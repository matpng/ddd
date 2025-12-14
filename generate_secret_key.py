#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for production deployment.
Run this and copy the output to your Render environment variables.
"""

import secrets

if __name__ == '__main__':
    secret_key = secrets.token_hex(32)
    
    print("=" * 70)
    print("SECURE SECRET_KEY GENERATED")
    print("=" * 70)
    print()
    print("Copy the following value to your Render Dashboard:")
    print()
    print(f"  {secret_key}")
    print()
    print("Steps:")
    print("  1. Go to https://dashboard.render.com")
    print("  2. Select your 'orion-octave-cubes' service")
    print("  3. Click 'Environment' tab")
    print("  4. Add or update the SECRET_KEY variable")
    print("  5. Paste the value above")
    print("  6. Click 'Save Changes'")
    print()
    print("=" * 70)
