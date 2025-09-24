#!/usr/bin/env python3
"""
MongoDB Atlas URI Generator
Helps generate a properly formatted MongoDB Atlas connection string
"""
import urllib.parse

def generate_mongo_uri():
    """Generate MongoDB Atlas URI with user input."""
    print("🔧 MongoDB Atlas URI Generator")
    print("=" * 50)
    
    # Get user inputs
    print("\n📋 Please provide the following information from your MongoDB Atlas dashboard:")
    
    # Cluster information
    cluster_host = input("🌐 Cluster Host (e.g., cluster0.xwl3hiq.mongodb.net): ").strip()
    if not cluster_host:
        cluster_host = "cluster0.xwl3hiq.mongodb.net"  # Default from current config
    
    # User credentials
    username = input("👤 Database Username: ").strip()
    if not username:
        username = "dattatraykshirsagar23_db_user"  # Default from current config
    
    password = input("🔑 Database Password: ").strip()
    if not password:
        password = "Datta@2005"  # Default from current config
    
    # Database name
    database = input("🗄️  Database Name (default: radiological_detection): ").strip()
    if not database:
        database = "radiological_detection"
    
    # URL encode the password to handle special characters
    encoded_password = urllib.parse.quote_plus(password)
    
    # Generate the URI
    mongo_uri = f"mongodb+srv://{username}:{encoded_password}@{cluster_host}/{database}"
    
    print("\n" + "=" * 50)
    print("✅ Generated MongoDB URI:")
    print(f"MONGO_URI={mongo_uri}")
    print("=" * 50)
    
    print("\n📝 To update your .env file:")
    print("1. Open your .env file")
    print("2. Replace the MONGO_URI line with the one above")
    print("3. Save the file")
    print("4. Run 'python test_mongo.py' to test the connection")
    
    return mongo_uri

def create_env_backup_and_update(new_uri):
    """Create backup of .env and update with new URI."""
    import os
    import shutil
    from datetime import datetime
    
    env_file = '.env'
    if os.path.exists(env_file):
        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f'.env.backup_{timestamp}'
        shutil.copy2(env_file, backup_file)
        print(f"📁 Backup created: {backup_file}")
        
        # Read current .env
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update MONGO_URI line
        updated_lines = []
        uri_updated = False
        for line in lines:
            if line.startswith('MONGO_URI='):
                updated_lines.append(f'MONGO_URI={new_uri}\n')
                uri_updated = True
            else:
                updated_lines.append(line)
        
        # If MONGO_URI wasn't found, add it
        if not uri_updated:
            updated_lines.append(f'MONGO_URI={new_uri}\n')
        
        # Write updated .env
        with open(env_file, 'w') as f:
            f.writelines(updated_lines)
        
        print(f"✅ Updated {env_file} with new MongoDB URI")
        return True
    else:
        print(f"❌ {env_file} not found")
        return False

if __name__ == "__main__":
    new_uri = generate_mongo_uri()
    
    print("\n🤖 Would you like me to automatically update your .env file? (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice in ['y', 'yes']:
        create_env_backup_and_update(new_uri)
    else:
        print("👍 Please manually update your .env file with the generated URI")
