#!/usr/bin/env python3
"""
Local development server runner for Quantum ML Radiological Threat Detection System
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from app import create_app

if __name__ == '__main__':
    # Create Flask app
    app = create_app('development')
    
    print("=" * 60)
    print("🚀 Quantum ML Radiological Threat Detection System")
    print("=" * 60)
    print(f"📡 Server starting on: http://localhost:5000")
    print(f"🔗 MongoDB Atlas: Connected")
    print(f"🔐 Admin Login: admin@example.com / admin123")
    print(f"🌐 Frontend: Open login.html in browser")
    print("=" * 60)
    
    try:
        # Run with SocketIO support
        app.socketio.run(
            app, 
            debug=True, 
            host='0.0.0.0', 
            port=5000,
            use_reloader=True,
            log_output=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)
