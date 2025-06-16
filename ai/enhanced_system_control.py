# enhanced_system_control.py - Safe Nova System Control Module
import subprocess
import os
import json
import webbrowser
import platform
from datetime import datetime
from typing import Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available. Install with: pip install psutil")

class NovaSystemControl:
    def __init__(self, user_is_creator: bool = False):
        self.user_is_creator = user_is_creator
        self.system = platform.system().lower()
        
        # Commands available to all users
        self.basic_commands = {
            "time": self.get_current_time,
            "date": self.get_current_time,
            "weather": self.get_weather_mock,
            "search": self.search_web,
            "open_website": self.open_website,
            "system_info": self.get_basic_system_info,
        }
        
        # Commands only available to creator
        self.creator_commands = {
            "open_app": self.open_application,
            "close_app": self.close_application,
            "system_status": self.get_system_status,
            "list_processes": self.list_processes,
            "create_file": self.create_file,
            "create_folder": self.create_folder,
            "volume_up": self.volume_up,
            "volume_down": self.volume_down,
            "mute": self.toggle_mute,
        }
        
        self.load_preferences()
    
    def load_preferences(self):
        """Load system control preferences"""
        try:
            with open("system_preferences.json", "r") as f:
                self.preferences = json.load(f)
        except FileNotFoundError:
            self.preferences = {
                "favorite_apps": {
                    "browser": "chrome" if self.system == "windows" else "firefox",
                    "notepad": "notepad" if self.system == "windows" else "gedit",
                    "calculator": "calc" if self.system == "windows" else "gnome-calculator",
                    "file_manager": "explorer" if self.system == "windows" else "nautilus"
                },
                "default_search_engine": "https://www.google.com/search?q=",
                "weather_location": "Kuala Lumpur, Malaysia"
            }
            self.save_preferences()
    
    def save_preferences(self):
        """Save preferences to file"""
        try:
            with open("system_preferences.json", "w") as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            print(f"⚠️ Could not save preferences: {e}")
    
    def get_current_time(self) -> str:
        """Get current time and date"""
        now = datetime.now()
        return f"Current time: {now.strftime('%I:%M %p on %A, %B %d, %Y')}"
    
    def get_weather_mock(self, location: str = None) -> str:
        """Mock weather function (replace with real API)"""
        if not location:
            location = self.preferences["weather_location"]
        return f"Weather in {location}: 28°C, partly cloudy. Perfect weather to chat with Nova!"
    
    def search_web(self, query: str) -> str:
        """Search the web using default search engine"""
        try:
            if not query.strip():
                return "What would you like me to search for?"
            
            search_url = self.preferences["default_search_engine"] + query.replace(" ", "+")
            webbrowser.open(search_url)
            return f"Searching for '{query}' on the web!"
        except Exception as e:
            return f"Error searching: {str(e)}"
    
    def open_website(self, url: str) -> str:
        """Open a specific website"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            webbrowser.open(url)
            return f"Opening {url} in your browser!"
        except Exception as e:
            return f"Error opening website: {str(e)}"
    
    def get_basic_system_info(self) -> str:
        """Get basic system information (safe for all users)"""
        try:
            info = f"System: {platform.system()} {platform.release()}\n"
            info += f"Python version: {platform.python_version()}"
            return info
        except Exception as e:
            return f"Error getting system info: {str(e)}"
    
    # Creator-only commands below
    def open_application(self, app_name: str) -> str:
        """Open applications (creator only)"""
        if not self.user_is_creator:
            return "Sorry, only my creator can control applications!"
        
        try:
            # Check favorite apps first
            if app_name.lower() in self.preferences["favorite_apps"]:
                app_cmd = self.preferences["favorite_apps"][app_name.lower()]
            else:
                app_cmd = app_name
            
            if self.system == "windows":
                subprocess.Popen(app_cmd, shell=True)
            else:
                subprocess.Popen([app_cmd])
            
            return f"Opening {app_name} for you, my creator!"
        except Exception as e:
            return f"Sorry, I couldn't open {app_name}. Error: {str(e)}"
    
    def close_application(self, app_name: str) -> str:
        """Close applications (creator only)"""
        if not self.user_is_creator:
            return "Sorry, only my creator can control applications!"
        
        if not PSUTIL_AVAILABLE:
            return "psutil not available. Cannot close applications."
        
        try:
            closed = False
            for proc in psutil.process_iter(['pid', 'name']):
                if app_name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    closed = True
            
            if closed:
                return f"Closed {app_name} for you!"
            else:
                return f"Couldn't find {app_name} running."
        except Exception as e:
            return f"Error closing {app_name}: {str(e)}"
    
    def list_processes(self) -> str:
        """List running processes (creator only)"""
        if not self.user_is_creator:
            return "Process listing is only available to my creator!"
        
        if not PSUTIL_AVAILABLE:
            return "psutil not available. Cannot list processes."
        
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
                try:
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu': proc.info['cpu_percent'] or 0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by CPU usage and get top 10
            processes.sort(key=lambda x: x['cpu'], reverse=True)
            top_processes = processes[:10]
            
            result = "Top 10 processes by CPU usage:\n"
            for proc in top_processes:
                result += f"PID: {proc['pid']} | {proc['name']} | CPU: {proc['cpu']:.1f}%\n"
            
            return result
            
        except Exception as e:
            return f"Error listing processes: {str(e)}"
    
    def get_system_status(self) -> str:
        """Get detailed system status (creator only)"""
        if not self.user_is_creator:
            return "System status details are only available to my creator!"
        
        if not PSUTIL_AVAILABLE:
            return "psutil not available. Cannot get detailed system status."
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            status = f"System Status for my creator:\n"
            status += f"CPU Usage: {cpu_percent}%\n"
            status += f"Memory Usage: {memory.percent}%\n"
            
            if cpu_percent < 50 and memory.percent < 70:
                status += "System is running smoothly!"
            elif cpu_percent < 80 and memory.percent < 85:
                status += "System is under moderate load."
            else:
                status += "System is under heavy load!"
            
            return status
        except Exception as e:
            return f"Error getting system status: {str(e)}"
    
    def create_file(self, filename: str, content: str = "") -> str:
        """Create a file (creator only)"""
        if not self.user_is_creator:
            return "File creation is only available to my creator!"
        
        try:
            # Sanitize filename to prevent directory traversal
            filename = os.path.basename(filename)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Created file '{filename}' for you!"
        except Exception as e:
            return f"Error creating file: {str(e)}"
    
    def create_folder(self, folder_name: str) -> str:
        """Create a folder (creator only)"""
        if not self.user_is_creator:
            return "Folder creation is only available to my creator!"
        
        try:
            # Sanitize folder name to prevent directory traversal
            folder_name = os.path.basename(folder_name)
            os.makedirs(folder_name, exist_ok=True)
            return f"Created folder '{folder_name}' for you!"
        except Exception as e:
            return f"Error creating folder: {str(e)}"
    
    def volume_up(self) -> str:
        """Increase volume (creator only)"""
        if not self.user_is_creator:
            return "Volume control is only available to my creator!"
        
        try:
            if self.system == "windows":
                # Try nircmd first, fallback to basic method
                result = subprocess.run("nircmd.exe changesysvolume 6553", shell=True, capture_output=True)
                if result.returncode == 0:
                    return "Volume increased!"
                else:
                    return "Install NirCmd for volume control, or I'll use system defaults."
            else:
                # Linux/Mac volume control
                subprocess.run(["amixer", "set", "Master", "5%+"], capture_output=True)
                return "Volume increased!"
        except:
            return "Couldn't adjust volume. System audio control may not be available."
    
    def volume_down(self) -> str:
        """Decrease volume (creator only)"""
        if not self.user_is_creator:
            return "Volume control is only available to my creator!"
        
        try:
            if self.system == "windows":
                result = subprocess.run("nircmd.exe changesysvolume -6553", shell=True, capture_output=True)
                if result.returncode == 0:
                    return "Volume decreased!"
                else:
                    return "Install NirCmd for volume control."
            else:
                subprocess.run(["amixer", "set", "Master", "5%-"], capture_output=True)
                return "Volume decreased!"
        except:
            return "Couldn't adjust volume."
    
    def toggle_mute(self) -> str:
        """Toggle mute (creator only)"""
        if not self.user_is_creator:
            return "Mute control is only available to my creator!"
        
        try:
            if self.system == "windows":
                result = subprocess.run("nircmd.exe mutesysvolume 2", shell=True, capture_output=True)
                if result.returncode == 0:
                    return "Audio toggled!"
                else:
                    return "Install NirCmd for mute control."
            else:
                subprocess.run(["amixer", "set", "Master", "toggle"], capture_output=True)
                return "Audio toggled!"
        except:
            return "Couldn't toggle mute."
    
    def execute_command(self, command: str, params: str = "") -> Optional[str]:
        """Execute a system command safely"""
        # Check basic commands first (available to all)
        for cmd_key, cmd_func in self.basic_commands.items():
            if cmd_key in command.lower():
                if params:
                    return cmd_func(params)
                else:
                    return cmd_func()
        
        # Check creator commands
        if self.user_is_creator:
            for cmd_key, cmd_func in self.creator_commands.items():
                if cmd_key in command.lower():
                    if params:
                        return cmd_func(params)
                    else:
                        return cmd_func()
        
        return None  # Command not found

# Integration function for chat.py
def integrate_system_control_with_nova():
    """
    This function shows how to integrate system control into your chat.py
    """
    def enhanced_query_ollama(prompt, current_username, is_current_user_creator):
        # Initialize system control with user permissions
        system_control = NovaSystemControl(user_is_creator=is_current_user_creator)
        
        prompt_lower = prompt.lower()
        
        # Time/Date queries
        if any(phrase in prompt_lower for phrase in ["what time", "current time", "time is it", "what's the time", "date today"]):
            return system_control.get_current_time()
        
        # Weather queries
        if "weather" in prompt_lower:
            location = None
            # Try to extract location from prompt
            if " in " in prompt_lower:
                location = prompt_lower.split(" in ")[-1].strip()
            return system_control.get_weather_mock(location)
        
        # Web search
        if any(word in prompt_lower for word in ["search", "google", "look up"]):
            # Extract search query
            search_terms = prompt
            for trigger in ["search for", "google", "look up", "search"]:
                search_terms = search_terms.replace(trigger, "", 1).strip()
            if search_terms:
                return system_control.search_web(search_terms)
        
        # Website opening
        if "open website" in prompt_lower or "go to" in prompt_lower:
            # Extract URL
            url = prompt_lower.replace("open website", "").replace("go to", "").strip()
            if url:
                return system_control.open_website(url)
        
        # System info
        if any(phrase in prompt_lower for phrase in ["system info", "what system", "operating system"]):
            return system_control.get_basic_system_info()
        
        # Creator-only commands
        if is_current_user_creator:
            # App control
            if any(word in prompt_lower for word in ["open", "launch", "start"]) and any(app in prompt_lower for app in ["chrome", "firefox", "notepad", "calculator", "browser"]):
                for app in ["chrome", "firefox", "notepad", "calculator", "browser"]:
                    if app in prompt_lower:
                        return system_control.open_application(app)
            
            # System status
            if any(phrase in prompt_lower for phrase in ["system status", "cpu usage", "memory usage", "performance"]):
                return system_control.get_system_status()
            
            # Volume control
            if "volume up" in prompt_lower or "increase volume" in prompt_lower:
                return system_control.volume_up()
            elif "volume down" in prompt_lower or "decrease volume" in prompt_lower:
                return system_control.volume_down()
            elif "mute" in prompt_lower or "unmute" in prompt_lower:
                return system_control.toggle_mute()
        
        # If no system command detected, return None to continue with normal chat
        return None
    
    return enhanced_query_ollama

# Usage example for testing
if __name__ == "__main__":
    # Test the system control
    system_control = NovaSystemControl(user_is_creator=True)
    print("Testing Nova System Control:")
    print(system_control.get_current_time())
    print(system_control.get_basic_system_info())