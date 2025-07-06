#!/usr/bin/env python3
"""
Setup script for JobOptimizer application.
This script helps users configure the application properly.
"""

import os
import secrets
import sys

def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)

def create_env_file():
    """Create a .env file with proper configuration"""
    env_content = f"""# Required for security - Generated automatically
SECRET_KEY={generate_secret_key()}

# Required for AI functionality - Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Database URL for production (Supabase)
# DATABASE_URL=your_supabase_database_url_here

# Optional: Flask configuration
FLASK_DEBUG=False
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env file with secure configuration")
    print("⚠️  Please add your OpenAI API key to the .env file")

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'flask',
        'flask-login',
        'flask-wtf',
        'flask-limiter',
        'openai',
        'PyPDF2',
        'python-dotenv',
        'werkzeug'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies are installed")
        return True

def create_uploads_directory():
    """Create uploads directory if it doesn't exist"""
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
        print("✅ Created uploads directory")
    else:
        print("✅ Uploads directory exists")

def main():
    """Main setup function"""
    print("🚀 JobOptimizer Setup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create uploads directory
    create_uploads_directory()
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        create_env_file()
    else:
        print("✅ .env file already exists")
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file and add your OpenAI API key")
    print("2. Run: python init_db.py")
    print("3. Run: python app.py")
    print("4. Open http://localhost:5000 in your browser")

if __name__ == "__main__":
    main() 