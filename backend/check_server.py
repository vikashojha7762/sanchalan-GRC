#!/usr/bin/env python
"""
Quick script to check if backend server is running and accessible.
"""
import requests
import sys
import time

def check_server(max_attempts=5, delay=2):
    """Check if the backend server is running."""
    url = "http://localhost:8000/health"
    
    print("Checking backend server status...")
    print(f"URL: {url}")
    print("-" * 50)
    
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"Attempt {attempt}/{max_attempts}...")
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                print("✅ SUCCESS! Backend server is running!")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.json()}")
                return True
            else:
                print(f"⚠️ Server responded with status: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection refused - Server is not running")
        except requests.exceptions.Timeout:
            print(f"⏱️ Request timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        if attempt < max_attempts:
            print(f"Waiting {delay} seconds before retry...")
            time.sleep(delay)
    
    print("\n" + "=" * 50)
    print("❌ Backend server is NOT accessible")
    print("\nTo start the server, run:")
    print("  cd backend")
    print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    return False

if __name__ == "__main__":
    success = check_server()
    sys.exit(0 if success else 1)
