#!/usr/bin/env python3
"""
Simple test script to verify the JobOptimizer application works correctly.
"""

import os
import sys
import requests
import time

def test_app():
    """Test the application endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing JobOptimizer Application...")
    print("=" * 50)
    
    # Test 1: Check if app is running
    try:
        response = requests.get(f"{base_url}/login", timeout=5)
        if response.status_code == 200:
            print("✅ Application is running")
        else:
            print(f"❌ Application returned status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Application is not running. Please start it with: python app.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to application: {e}")
        return False
    
    # Test 2: Check environment variables
    print("\n🔧 Checking Environment Variables...")
    required_vars = ['SECRET_KEY', 'OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file")
    else:
        print("✅ All required environment variables are set")
    
    # Test 3: Check file structure
    print("\n📁 Checking File Structure...")
    required_files = [
        'app.py',
        'database.py',
        'requirements.txt',
        'templates/index.html',
        'templates/login.html',
        'templates/signup.html'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All required files are present")
    
    # Test 4: Check uploads directory
    print("\n📂 Checking Uploads Directory...")
    if not os.path.exists('uploads'):
        print("⚠️  Uploads directory doesn't exist, creating...")
        os.makedirs('uploads', exist_ok=True)
        print("✅ Uploads directory created")
    else:
        print("✅ Uploads directory exists")
    
    print("\n🎉 All basic tests passed!")
    print("\n📋 Next Steps:")
    print("1. Make sure your .env file contains SECRET_KEY and OPENAI_API_KEY")
    print("2. Run: python app.py")
    print("3. Open http://localhost:5000 in your browser")
    print("4. Create an account and test the functionality")
    
    return True

if __name__ == "__main__":
    success = test_app()
    sys.exit(0 if success else 1) 