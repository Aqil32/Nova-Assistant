# NOVA AI Assistant

## Overview
Personal AI assistant that can browse web, open web and chat with you via voice.

## Features
- 🌐 Web browsing
- 🎤 Voice recognition
- 💬 Natural language processing
- 🖥️ System control (ALPHA)

## Technologies
- Python
- Ollama
- Mistral 7B
- MariaDB
- Coqui TTS
- Whisper

## Achievements
- ✅ 95% voice recognition accuracy using Whisper
- ✅ Save the conversation to database
- ✅ Zero-dependency local AI

- # Database Setup for Nova

## Prerequisites
- MariaDB or MySQL server installed and running
- Access to create databases and users

## SQL Installation Commands

### 1. Connect to your MariaDB/MySQL server as root 
```bash
mysql -u root -p
```

### 2. Create the Nova database
```sql
CREATE DATABASE nova_memory;
```

### 3. Create a dedicated user for Nova
```sql
CREATE USER 'nova_user'@'localhost' IDENTIFIED BY 'admin';
```

### 4. Grant permissions to the Nova user
```sql
GRANT ALL PRIVILEGES ON nova_memory.* TO 'nova_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Switch to the Nova database
```sql
USE nova_memory;
```

### 6. Create the conversation memory table
```sql
CREATE TABLE IF NOT EXISTS conversation_memory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(50) DEFAULT 'Guest',
    is_creator BOOLEAN DEFAULT FALSE,
    user_input TEXT,
    nova_response TEXT,
    session_id VARCHAR(50) DEFAULT 'default'
);
```

### 7. Create the memory context table for long-term memory
```sql
CREATE TABLE IF NOT EXISTS memory_context (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) DEFAULT 'Guest',
    summary TEXT,
    importance_score INT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(50) DEFAULT 'default'
);
```

### 8. Verify table creation
```sql
SHOW TABLES;
DESCRIBE conversation_memory;
DESCRIBE memory_context;
```

### 9. Exit MySQL
```sql
EXIT;
```

## Configuration

After running these commands, update your `chat.py` database configuration:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'nova_user',
    'password': '2307054irsyad',  # Change this to your chosen password
    'database': 'nova_memory'
}
```

## Security Notes

⚠️ **Important**: Change the default password `'2307054irsyad'` to something more secure:

```sql
ALTER USER 'nova_user'@'localhost' IDENTIFIED BY 'your_secure_password_here';
```

Then update the password in your `chat.py` file accordingly.

## Testing the Connection

You can test the database connection by running:
```bash
mysql -u nova_user -p nova_memory
```

Enter your password when prompted. If successful, you should see the MySQL prompt with the `nova_memory` database selected.
