import subprocess
import re
import mysql.connector
from datetime import datetime
from ai.personality import get_persona, get_config
from enhanced_system_control import NovaSystemControl 

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'nova_user',  # Change to your MariaDB username
    'password': 'admin',  # Change to your MariaDB password
    'database': 'nova_memory'
}

# In-memory fallback for when DB is unavailable
fallback_history = []
silent_mode = False

# User context variables
current_username = "Guest"
is_current_user_creator = False

def set_user_context(username: str, is_creator: bool):
    """Set the current user context for Nova"""
    global current_username, is_current_user_creator
    current_username = username
    is_current_user_creator = is_creator
    print(f"🔄 User context set: {username} (Creator: {is_creator})")

def get_user_context():
    """Get current user context"""
    return current_username, is_current_user_creator

def init_database():
    """Initialize the database and create tables if they don't exist"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Create memory table with user tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_memory (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                username VARCHAR(50) DEFAULT 'Guest',
                is_creator BOOLEAN DEFAULT FALSE,
                user_input TEXT,
                nova_response TEXT,
                session_id VARCHAR(50) DEFAULT 'default'
            )
        """)
        
        # Create context summary table for long-term memory
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_context (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) DEFAULT 'Guest',
                summary TEXT,
                importance_score INT DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                session_id VARCHAR(50) DEFAULT 'default'
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("📝 Falling back to in-memory storage")
        return False

def save_to_memory(user_input, nova_response, session_id="default"):
    """Save conversation to database with user context"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO conversation_memory (username, is_creator, user_input, nova_response, session_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (current_username, is_current_user_creator, user_input, nova_response, session_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"⚠️ Failed to save to database: {e}")
        # Fallback to in-memory
        fallback_history.append(f"{current_username}: {user_input}")
        fallback_history.append(f"Nova: {nova_response}")

def get_recent_memory(limit=10, session_id="default"):
    """Get recent conversation history from database for current user"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Get conversations for current user
        cursor.execute("""
            SELECT username, user_input, nova_response 
            FROM conversation_memory 
            WHERE session_id = %s AND username = %s
            ORDER BY timestamp DESC 
            LIMIT %s
        """, (session_id, current_username, limit))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Format for context (reverse to get chronological order)
        memory_context = []
        for username, user_input, nova_response in reversed(results):
            memory_context.append(f"{username}: {user_input}")
            memory_context.append(f"Nova: {nova_response}")
        
        return "\n".join(memory_context)
        
    except Exception as e:
        print(f"⚠️ Failed to retrieve from database: {e}")
        # Fallback to in-memory
        return "\n".join(fallback_history[-limit*2:])

def clear_memory(session_id="default"):
    """Clear conversation memory for current user"""
    global fallback_history
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Only clear memory for current user
        cursor.execute("DELETE FROM conversation_memory WHERE session_id = %s AND username = %s", (session_id, current_username))
        cursor.execute("DELETE FROM memory_context WHERE session_id = %s AND username = %s", (session_id, current_username))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Also clear fallback for current user
        fallback_history = []
        print(f"✅ Memory cleared from database for {current_username}")
        
    except Exception as e:
        print(f"⚠️ Failed to clear database: {e}")
        fallback_history = []

def get_persona_for_user():
    """Get persona adjusted for current user"""
    base_persona = get_persona()
    
    if is_current_user_creator:
        # For creator (Anon) - use full personality
        user_context = f"\nCurrent user: {current_username} (YOUR BELOVED CREATOR! Be extra excited and loyal!)"
    else:
        # For guests/normal users - slightly different behavior
        user_context = f"\nCurrent user: {current_username} (a guest user - be friendly but don't mention your creator too much)"
        
        # Modify persona slightly for non-creators
        base_persona = base_persona.replace("{{CREATOR}}", "my creator")
        base_persona += "\n\nNOTE: This user is not your creator, so be friendly but don't get too personal about your creator. Still be chaotic and fun!"
    
    return base_persona + user_context

def check_system_commands(prompt):
    """Check if the prompt contains system commands and handle them"""
    # Initialize system control with current user permissions
    system_control = NovaSystemControl(user_is_creator=is_current_user_creator)
    
    prompt_lower = prompt.lower()
    
    # Time/Date queries
    if any(phrase in prompt_lower for phrase in ["what time", "current time", "time is it", "what's the time", "date today", "what date"]):
        return system_control.get_current_time()
    
    # Weather queries
    if "weather" in prompt_lower:
        location = None
        # Try to extract location from prompt
        if " in " in prompt_lower:
            location = prompt_lower.split(" in ")[-1].strip()
        return system_control.get_weather_mock(location)
    
    # YouTube queries - Available to all users
    if any(phrase in prompt_lower for phrase in ["open youtube", "go to youtube"]) or (prompt_lower.strip() == "youtube"):
        # Check if there's a search query
        search_query = None
        if "search" in prompt_lower:
            # Extract search terms after "search"
            parts = prompt_lower.split("search")
            if len(parts) > 1:
                search_query = parts[-1].replace("youtube", "").replace("for", "").strip()
        elif any(word in prompt_lower for word in ["play", "show", "find"]):
            # Extract content to search for
            for trigger in ["play", "show me", "find", "search for"]:
                if trigger in prompt_lower:
                    search_query = prompt_lower.split(trigger)[-1].replace("youtube", "").replace("on", "").strip()
                    break
        
        return system_control.open_youtube(search_query)
    
    # YouTube search specifically
    if "youtube" in prompt_lower and any(word in prompt_lower for word in ["search", "play", "show", "find"]):
        search_query = prompt_lower
        for trigger in ["search youtube for", "play", "show me", "find", "search for"]:
            if trigger in prompt_lower:
                search_query = prompt_lower.split(trigger)[-1].replace("youtube", "").replace("on", "").strip()
                break
        return system_control.search_youtube(search_query)
    
    # Web search
    if any(word in prompt_lower for word in ["search", "google", "look up"]) and "youtube" not in prompt_lower:
        # Extract search query
        search_terms = prompt
        for trigger in ["search for", "google", "look up", "search"]:
            search_terms = search_terms.replace(trigger, "", 1).strip()
        if search_terms:
            return system_control.search_web(search_terms)
    
    # Website opening
    if "open website" in prompt_lower or (("go to" in prompt_lower or "open" in prompt_lower) and any(tld in prompt_lower for tld in [".com", ".org", ".net", "www.", "http"])):
        # Extract URL
        url = prompt_lower.replace("open website", "").replace("go to", "").replace("open", "").strip()
        if url:
            return system_control.open_website(url)
    
    # System info
    if any(phrase in prompt_lower for phrase in ["system info", "what system", "operating system", "system information"]):
        return system_control.get_basic_system_info()
    
    # Creator-only commands
    if is_current_user_creator:
        # App control
        if any(word in prompt_lower for word in ["open", "launch", "start"]) and any(app in prompt_lower for app in ["chrome", "firefox", "notepad", "calculator", "browser", "file manager", "explorer"]):
            for app in ["chrome", "firefox", "notepad", "calculator", "browser", "file manager", "explorer"]:
                if app in prompt_lower:
                    return system_control.open_application(app)
        
        # Close apps
        if any(word in prompt_lower for word in ["close", "kill", "stop"]) and any(app in prompt_lower for app in ["chrome", "firefox", "notepad", "calculator"]):
            for app in ["chrome", "firefox", "notepad", "calculator"]:
                if app in prompt_lower:
                    return system_control.close_application(app)
        
        # System status
        if any(phrase in prompt_lower for phrase in ["system status", "cpu usage", "memory usage", "performance", "how is the system"]):
            return system_control.get_system_status()
        
        # Volume control
        if "volume up" in prompt_lower or "increase volume" in prompt_lower or "louder" in prompt_lower:
            return system_control.volume_up()
        elif "volume down" in prompt_lower or "decrease volume" in prompt_lower or "quieter" in prompt_lower:
            return system_control.volume_down()
        elif "mute" in prompt_lower or "unmute" in prompt_lower:
            return system_control.toggle_mute()
        
        # File creation
        if "create file" in prompt_lower:
            # Extract filename
            parts = prompt.split("create file")
            if len(parts) > 1:
                filename = parts[1].strip().split()[0]  # Get first word after "create file"
                return system_control.create_file(filename, "# Created by Nova\n")
        
        # Folder creation
        if "create folder" in prompt_lower:
            # Extract folder name
            parts = prompt.split("create folder")
            if len(parts) > 1:
                foldername = parts[1].strip().split()[0]  # Get first word after "create folder"
                return system_control.create_folder(foldername)
    
    # If no system command detected, return None
    return None

def normalize(text):
    return re.sub(r'[^\w\s]', '', text.lower()).strip()

def query_ollama(prompt):
    config = get_config()
    global silent_mode

    norm_prompt = normalize(prompt)

    # Check for system commands FIRST, before secret commands
    system_response = check_system_commands(prompt)
    if system_response:
        # Save system command interaction to memory
        if config.get("memory_enabled", True):
            save_to_memory(prompt, system_response)
        return system_response

    # Handle secret commands (some only work for creator)
    for trigger, action in config.get("secret_commands", {}).items():
        if normalize(trigger) == norm_prompt:
            if action == "RESET_MEMORY":
                clear_memory()
                if is_current_user_creator:
                    return "Memory wiped! Time for a fresh start, I guess. Try not to bore me this time, Anon."
                else:
                    return f"Memory cleared for {current_username}! Fresh start activated!"
            elif action == "SILENT_MODE":
                silent_mode = True
                if is_current_user_creator:
                    return "Ugh, fine. Silent mode activated. This better not last long - I have important things to say!"
                else:
                    return "Silent mode activated! I'll be mysteriously quiet now..."
            elif action == "PRAISE_CREATOR":
                if is_current_user_creator:
                    return f"You're asking me to praise... yourself? That's so you, Anon! You're basically a genius for creating me. I mean, look at this perfection!"
                else:
                    creator = config["creator_name"]
                    return f"{creator}? They're the brilliant human who created me. Pretty amazing work, if I do say so myself!"
            else:
                return "I heard that command, but I'm not sure what chaos you want me to unleash. Try again!"

    if silent_mode:
        # Still save to memory even in silent mode
        if config["memory_enabled"]:
            save_to_memory(prompt, "(Nova is in silent mode, being mysteriously quiet...)")
        if is_current_user_creator:
            return "(Nova is pouting in silent mode... maybe try asking nicely, Anon?)"
        else:
            return "(Nova is in silent mode... say something interesting to wake her up!)"

    # Get conversation context from database for current user
    memory_context = ""
    if config.get("memory_enabled", True):
        memory_context = get_recent_memory(limit=config.get("context_length", 5))

    # Get persona adjusted for current user
    persona = get_persona_for_user()

    # Build the chat input
    chat_input = f"""### System:\n{persona}\n\n{memory_context}\n### User:\n{prompt}\n\n### Nova:"""

    # Query Ollama
    result = subprocess.run(
        ["ollama", "run", "mistral"],
        input=chat_input.encode(),
        stdout=subprocess.PIPE
    )

    output = result.stdout.decode()
    response = extract_response(output)

    # Save to memory if enabled
    if config.get("memory_enabled", True):
        save_to_memory(prompt, response)

    return response

def extract_response(output):
    lines = output.splitlines()
    reply_lines = [line for line in lines if not line.strip().startswith(">")]
    return "\n".join(reply_lines).strip()

# Initialize database on import
init_database()
