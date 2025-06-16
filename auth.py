import hashlib
import getpass
import json
import os
from typing import Optional, Tuple

class NovaAuth:
    def __init__(self):
        self.auth_file = "nova_auth.json"
        self.secret_phrase_hash = None
        self.current_user = None
        self.is_creator = False
        self.load_auth_config()
    
    def load_auth_config(self):
        """Load authentication configuration or create default"""
        try:
            if os.path.exists(self.auth_file):
                with open(self.auth_file, 'r') as f:
                    auth_data = json.load(f)
                    self.secret_phrase_hash = auth_data.get("secret_phrase_hash")
            else:
                # First run - set up the secret phrase
                self.setup_secret_phrase()
        except Exception as e:
            print(f"❌ Error loading auth config: {e}")
            self.setup_secret_phrase()
    
    def setup_secret_phrase(self):
        """Set up the secret phrase for the creator (first time setup)"""
        print("\n🔐 FIRST TIME SETUP - Nova Authentication")
        print("=" * 50)
        print("Setting up creator authentication...")
        print("Default secret phrase: 'Vira Anon Nova'")
        print("You can change this or keep the default.")
        print()
        
        while True:
            choice = input("Use default phrase? (y/n): ").lower().strip()
            if choice in ['y', 'yes']:
                secret_phrase = "Vira Anon Nova"
                break
            elif choice in ['n', 'no']:
                secret_phrase = getpass.getpass("Enter your custom secret phrase: ").strip()
                if secret_phrase:
                    confirm = getpass.getpass("Confirm secret phrase: ").strip()
                    if secret_phrase == confirm:
                        break
                    else:
                        print("❌ Phrases don't match. Try again.")
                else:
                    print("❌ Secret phrase cannot be empty.")
            else:
                print("Please enter 'y' or 'n'")
        
        # Hash and save the secret phrase
        self.secret_phrase_hash = self.hash_phrase(secret_phrase)
        self.save_auth_config()
        print("✅ Creator authentication set up successfully!")
        print("=" * 50)
    
    def hash_phrase(self, phrase: str) -> str:
        """Hash the secret phrase using SHA-256 with salt"""
        salt = "nova_creator_salt_2024"  # Fixed salt for consistency
        return hashlib.sha256((phrase + salt).encode()).hexdigest()
    
    def save_auth_config(self):
        """Save authentication configuration"""
        try:
            auth_data = {
                "secret_phrase_hash": self.secret_phrase_hash,
                "setup_complete": True
            }
            with open(self.auth_file, 'w') as f:
                json.dump(auth_data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving auth config: {e}")
    
    def verify_creator(self, phrase: str) -> bool:
        """Verify if the provided phrase matches the creator's secret phrase"""
        if not self.secret_phrase_hash:
            return False
        
        input_hash = self.hash_phrase(phrase)
        return input_hash == self.secret_phrase_hash
    
    def authenticate(self) -> Tuple[str, bool]:
        """
        Authenticate user and return (username, is_creator)
        Returns: (username, is_creator_boolean)
        """
        print("\n🎭 Nova Voice Assistant - User Authentication")
        print("=" * 50)
        print("Enter secret phrase to login as Creator (Anon)")
        print("Or press ENTER to continue as Guest")
        print("=" * 50)
        
        try:
            # Use getpass to hide the input (like a password)
            phrase = getpass.getpass("Secret Phrase (or ENTER for guest): ").strip()
            
            if not phrase:
                # Guest login
                print("👤 Logged in as: Guest")
                print("🔓 Access Level: Standard User")
                self.current_user = "Guest"
                self.is_creator = False
                return "Guest", False
            
            # Check if phrase matches creator's secret
            if self.verify_creator(phrase):
                print("👑 Logged in as: Anon (Creator)")
                print("🔑 Access Level: Full Creator Access")
                print("✨ Nova will recognize you as her beloved creator!")
                self.current_user = "Anon"
                self.is_creator = True
                return "Anon", True
            else:
                print("❌ Invalid secret phrase")
                print("👤 Logged in as: Normal User")
                print("🔓 Access Level: Standard User")
                self.current_user = "User"
                self.is_creator = False
                return "User", False
                
        except KeyboardInterrupt:
            print("\n\n👋 Authentication cancelled. Exiting...")
            exit(0)
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            print("👤 Defaulting to Guest access")
            self.current_user = "Guest"
            self.is_creator = False
            return "Guest", False
    
    def get_current_user_info(self) -> dict:
        """Get current user information"""
        return {
            "username": self.current_user,
            "is_creator": self.is_creator,
            "access_level": "Creator" if self.is_creator else "Standard"
        }
    
    def reset_auth(self):
        """Reset authentication (for testing or changing secret phrase)"""
        try:
            if os.path.exists(self.auth_file):
                os.remove(self.auth_file)
            print("✅ Authentication reset. Run again to set up new secret phrase.")
        except Exception as e:
            print(f"❌ Error resetting auth: {e}")

# Global auth instance
nova_auth = NovaAuth()

def authenticate_user() -> Tuple[str, bool]:
    """
    Main authentication function
    Returns: (username, is_creator)
    """
    return nova_auth.authenticate()

def get_user_info() -> dict:
    """Get current authenticated user info"""
    return nova_auth.get_current_user_info()

def is_creator() -> bool:
    """Check if current user is the creator"""
    return nova_auth.is_creator

def get_username() -> str:
    """Get current username"""
    return nova_auth.current_user or "Guest"

# CLI utility functions
def reset_authentication():
    """Reset authentication system (for admin use)"""
    nova_auth.reset_auth()

if __name__ == "__main__":
    # Test the authentication system
    print("🧪 Testing Nova Authentication System")
    username, creator_status = authenticate_user()
    print(f"\n📊 Test Results:")
    print(f"Username: {username}")
    print(f"Is Creator: {creator_status}")
    print(f"User Info: {get_user_info()}")