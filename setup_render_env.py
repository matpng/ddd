#!/usr/bin/env python3
"""
Quick Setup Script for Render Environment Variables
Generates secure tokens and displays configuration instructions
"""

import secrets
import sys

def generate_tokens():
    """Generate secure tokens for the application"""
    
    print("=" * 70)
    print("RENDER ENVIRONMENT VARIABLE SETUP")
    print("=" * 70)
    print()
    
    # Generate AGI API Token
    agi_token = secrets.token_urlsafe(32)
    
    print("[COPY THESE VALUES TO RENDER DASHBOARD]")
    print()
    print("1. AGI_API_TOKEN")
    print(f"   Value: {agi_token}")
    print()
    
    # Optional: Generate additional tokens
    alternate_token = secrets.token_urlsafe(32)
    print("2. Optional Backup Token (for rotation)")
    print(f"   Value: {alternate_token}")
    print()
    
    print("=" * 70)
    print("RENDER CONFIGURATION STEPS:")
    print("=" * 70)
    print()
    print("1. Go to: https://dashboard.render.com")
    print("2. Select your 'ddd' service")
    print("3. Click 'Environment' tab")
    print("4. Click 'Add Environment Variable'")
    print("5. Add:")
    print("   Key: AGI_API_TOKEN")
    print(f"   Value: {agi_token}")
    print("6. Click 'Save Changes'")
    print()
    print("Render will automatically redeploy with the new variable.")
    print()
    
    print("=" * 70)
    print("TESTING AUTHENTICATED ENDPOINTS:")
    print("=" * 70)
    print()
    print("After deployment completes, test with:")
    print()
    print(f'export AGI_API_TOKEN="{agi_token}"')
    print()
    print('curl -H "Authorization: Bearer $AGI_API_TOKEN" \\')
    print('     https://ddd-lwhl.onrender.com/api/agi/health')
    print()
    
    print("=" * 70)
    print("AGI SYSTEM INTEGRATION:")
    print("=" * 70)
    print()
    print("Add to your agi-proto-system/.env file:")
    print()
    print(f'AGI_API_TOKEN={agi_token}')
    print('DISCOVERY_API_URL=https://ddd-lwhl.onrender.com')
    print()
    
    # Save to local .env file
    try:
        with open('.env.render', 'w') as f:
            f.write(f"# Generated {secrets.token_hex(4)}\n")
            f.write(f"AGI_API_TOKEN={agi_token}\n")
            f.write(f"BACKUP_TOKEN={alternate_token}\n")
        print("[SUCCESS] Tokens saved to: .env.render (git-ignored)")
        print()
    except Exception as e:
        print(f"[WARNING] Could not save tokens to file: {e}")
    
    print("=" * 70)
    print("IMPORTANT SECURITY NOTES:")
    print("=" * 70)
    print()
    print("* Keep these tokens SECRET")
    print("* Never commit tokens to git")
    print("* Rotate tokens periodically")
    print("* .env.render is in .gitignore")
    print()

if __name__ == "__main__":
    try:
        generate_tokens()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)
