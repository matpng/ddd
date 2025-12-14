#!/usr/bin/env python3
"""
Render Blueprint Deployment Helper
Helps you deploy using Render Blueprint with proper SECRET_KEY setup
"""

import secrets
import sys

def generate_secret_key():
    """Generate a secure SECRET_KEY"""
    return secrets.token_hex(32)

def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70 + "\n")

def main():
    print_header("RENDER BLUEPRINT DEPLOYMENT HELPER")
    
    print("This script helps you deploy to Render using Blueprint (render.yaml)")
    print()
    
    # Check if render.yaml exists
    try:
        with open('render.yaml', 'r', encoding='utf-8') as f:
            content = f.read()
            if 'generateValue: true' in content:
                print("[OK] render.yaml is configured for auto-generated SECRET_KEY")
            else:
                print("[WARN] render.yaml may need SECRET_KEY configuration")
    except FileNotFoundError:
        print("[ERROR] render.yaml not found!")
        sys.exit(1)
    
    print()
    print_header("DEPLOYMENT OPTIONS")
    
    print("Choose your deployment approach:\n")
    
    print("[1] FRESH BLUEPRINT DEPLOY (Recommended)")
    print("   - Deletes existing service")
    print("   - Creates new service via Blueprint")
    print("   - AUTO-GENERATES SECRET_KEY")
    print()
    
    print("[2] UPDATE EXISTING SERVICE")
    print("   - Keeps existing service")
    print("   - Manually add SECRET_KEY")
    print("   - Then trigger redeploy")
    print()
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        print_header("OPTION 1: FRESH BLUEPRINT DEPLOY")
        print("Steps to deploy:")
        print()
        print("1. Delete existing service (if any):")
        print("   - Go to https://dashboard.render.com")
        print("   - Click your 'orion-octave-cubes' service")
        print("   - Settings > Delete Web Service")
        print()
        print("2. Deploy with Blueprint:")
        print("   - Click 'New' > 'Blueprint'")
        print("   - Connect repository: matpng/ddd")
        print("   - Render detects render.yaml automatically")
        print("   - Click 'Apply'")
        print()
        print("3. Blueprint will:")
        print("   [+] Create the web service")
        print("   [+] AUTO-GENERATE SECRET_KEY")
        print("   [+] Set all environment variables from render.yaml")
        print("   [+] Start deployment")
        print()
        print("[OK] No manual SECRET_KEY setup needed with this option!")
        
    elif choice == "2":
        secret_key = generate_secret_key()
        
        print_header("OPTION 2: UPDATE EXISTING SERVICE")
        print("Your generated SECRET_KEY:")
        print()
        print(f"  {secret_key}")
        print()
        print("Steps to update:")
        print()
        print("1. Add SECRET_KEY to Render:")
        print("   - Go to https://dashboard.render.com")
        print("   - Select 'orion-octave-cubes' service")
        print("   - Click 'Environment' tab")
        print("   - Add new environment variable:")
        print(f"     Key: SECRET_KEY")
        print(f"     Value: {secret_key}")
        print("   - Click 'Save Changes'")
        print()
        print("2. Trigger deploy:")
        print("   - Render will auto-deploy after saving")
        print("   - OR click 'Manual Deploy' > 'Deploy latest commit'")
        print()
        
    else:
        print("\n[ERROR] Invalid choice. Please run again and select 1 or 2.")
        sys.exit(1)
    
    print()
    print_header("VERIFICATION")
    print("After deployment completes (2-5 minutes):")
    print()
    print("1. Check deployment logs in Render dashboard")
    print("2. Visit health endpoint:")
    print("   curl https://your-app.onrender.com/health")
    print()
    print("3. Expected response:")
    print('   {"success": true, "status": "ok"}')
    print()
    
    print_header("TROUBLESHOOTING")
    print("If deployment still fails:")
    print()
    print("- Check Render logs for specific errors")
    print("- Verify FLASK_ENV=production is set")
    print("- Ensure SECRET_KEY is present in Environment tab")
    print("- Try Option 1 (fresh deploy) if Option 2 doesn't work")
    print()
    print("For more help, see: BLUEPRINT_DEPLOY_FIX.md")
    print()

if __name__ == '__main__':
    main()
