#!/usr/bin/env python3
"""
Test script for legal API endpoints
"""
import asyncio
import os
from fastapi.testclient import TestClient

# Set environment variables
os.environ['POSTGRES_HOST'] = 'localhost'
os.environ['POSTGRES_PORT'] = '5433'
os.environ['POSTGRES_DB'] = 'openhands_legal'
os.environ['POSTGRES_USER'] = 'postgres'
os.environ['POSTGRES_PASSWORD'] = ''
os.environ['LEGAL_WORKSPACE_ROOT'] = '/tmp/legal_workspace'
os.environ['DRAFT_SYSTEM_PATH'] = os.path.join(os.getcwd(), 'draft_system')

def test_legal_api():
    """Test the legal API endpoints"""
    try:
        from openhands.server.app import app
        
        client = TestClient(app)
        
        print("🧪 Testing legal system status endpoint...")
        response = client.get("/api/legal/system/status")
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Legal API is working!")
            return True
        else:
            print("❌ Legal API returned error")
            return False
            
    except Exception as e:
        print(f"❌ Error testing legal API: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_legal_api()
    if success:
        print("\n🎉 Legal document management system is ready!")
        print("You can now:")
        print("1. Start OpenHands server")
        print("2. Visit http://localhost:3000")
        print("3. Look for the mode toggle to switch to 'Legal Cases'")
    else:
        print("\n❌ Legal system test failed")
