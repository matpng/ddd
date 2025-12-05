#!/usr/bin/env python3
"""
Automated Render deployment via API
Docs: https://api-docs.render.com/
"""

import requests
import os
import sys

# Get API key from environment
API_KEY = os.getenv('RENDER_API_KEY')
if not API_KEY:
    print("❌ Set RENDER_API_KEY environment variable")
    print("Get it from: https://dashboard.render.com/u/settings#api-keys")
    sys.exit(1)

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

def trigger_deploy(service_id):
    """Trigger manual deploy for a service"""
    url = f'https://api.render.com/v1/services/{service_id}/deploys'
    
    response = requests.post(url, headers=HEADERS, json={'clearCache': 'clear'})
    
    if response.status_code == 201:
        deploy = response.json()
        print(f"✅ Deploy triggered!")
        print(f"   Deploy ID: {deploy['id']}")
        print(f"   Status: {deploy['status']}")
        print(f"   View at: https://dashboard.render.com/")
        return deploy
    else:
        print(f"❌ Deploy failed: {response.status_code}")
        print(f"   {response.text}")
        return None

def get_service_id_by_name(service_name):
    """Find service ID by name"""
    url = 'https://api.render.com/v1/services'
    
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        services = response.json()
        for service in services:
            if service['service']['name'] == service_name:
                return service['service']['id']
    
    print(f"❌ Service '{service_name}' not found")
    return None

def create_web_service():
    """Create a new web service (one-time setup)"""
    url = 'https://api.render.com/v1/services'
    
    payload = {
        "type": "web_service",
        "name": "orion-octave-cubes",
        "repo": "https://github.com/matpng/ddd",
        "autoDeploy": "yes",
        "branch": "main",
        "buildCommand": "chmod +x build.sh && ./build.sh",
        "startCommand": "chmod +x start.sh && ./start.sh",
        "envVars": [
            {"key": "FLASK_ENV", "value": "production"},
            {"key": "SECRET_KEY", "value": "96bf55f8d6c44ae4dcbecf2b7f7e0558540152dd8bfb09fda4e62b5b4ad6b4a1"},
            {"key": "FLASK_HOST", "value": "0.0.0.0"},
            {"key": "PORT", "value": "10000"},
            {"key": "MAX_DISTANCE_PAIRS", "value": "50000"},
            {"key": "MAX_DIRECTION_PAIRS", "value": "25000"},
            {"key": "LOG_LEVEL", "value": "INFO"},
            {"key": "CACHE_MAX_SIZE", "value": "100"}
        ],
        "serviceDetails": {
            "plan": "starter",  # or "free"
            "region": "oregon",
            "env": "python"
        }
    }
    
    response = requests.post(url, headers=HEADERS, json=payload)
    
    if response.status_code == 201:
        service = response.json()
        print(f"✅ Service created!")
        print(f"   Service ID: {service['service']['id']}")
        print(f"   URL: {service['service']['serviceDetails']['url']}")
        return service
    else:
        print(f"❌ Creation failed: {response.status_code}")
        print(f"   {response.text}")
        return None

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python deploy_render.py create          # Create new service")
        print("  python deploy_render.py deploy <name>   # Trigger deploy")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'create':
        create_web_service()
    elif command == 'deploy':
        service_name = sys.argv[2] if len(sys.argv) > 2 else 'orion-octave-cubes'
        service_id = get_service_id_by_name(service_name)
        if service_id:
            trigger_deploy(service_id)
    else:
        print(f"Unknown command: {command}")
