# NOVA AI Assistant 🤖

Personal AI assistant that can browse the web, open websites, and chat with you via voice.

## Features

- 🌐 **Web browsing** — search Google, open websites, browse YouTube
- 🎤 **Voice recognition** — 95% accuracy using OpenAI Whisper
- 💬 **Natural conversation** — powered by Ollama + Mistral 7B
- 👑 **Creator/Guest modes** — secret phrase authentication for creator privileges
- 🖥️ **System control** — time/date, weather, app launching (creator only)
- 👁️ **Computer vision** — screen analysis, OCR, screenshot capabilities
- 🗣️ **Voice output** — Coqui TTS with anime-style voice (pitch-shifted)
- 💾 **Conversation memory** — MariaDB/MySQL database storage
- 🔮 **Multiple personas** — Neuro, Evil, No-emojis, and more

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) with Mistral 7B (`ollama pull mistral`)
- MariaDB or MySQL (optional — falls back to in-memory)
- FFmpeg (for audio playback)
- SoX (for voice pitch shifting)

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up database (optional)
# See "Database Setup" section below

# 3. Configure environment (optional)
export NOVA_DB_PASSWORD="your_password"

# 4. Run Nova!
python app.py
```

## Authentication

Nova uses a secret phrase system:
- **Creator mode** — full access (system control, app launching, etc.)
- **Guest mode** — limited to conversation, web search, YouTube

Default secret phrase: `Vira Anon Nova`
*(Change this on first run or by deleting `nova_auth.json`)*

## Personas

Switch Nova's personality in `config.json`:

| Persona | File | Description |
|---------|------|-------------|
| `neuro` | `ai/personas/neuro.py` | Chaotic, unhinged, lovable disaster |
| `evil` | `ai/personas/evil.py` | Darkly charismatic, dramatic villain |
| `no_emojis` | `ai/personas/no_emojis.py` | Sassy streamer girl, no emojis |

## Configuration

Edit `config.json`:

```json
{
  "persona": "no_emojis",
  "memory_enabled": true,
  "context_length": 5,
  "creator_name": "Aqil"
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NOVA_DB_HOST` | `localhost` | Database host |
| `NOVA_DB_USER` | `nova_user` | Database user |
| `NOVA_DB_PASSWORD` | *(empty)* | Database password |
| `NOVA_DB_NAME` | `nova_memory` | Database name |

## Database Setup

```sql
CREATE DATABASE nova_memory;
CREATE USER 'nova_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON nova_memory.* TO 'nova_user'@'localhost';
FLUSH PRIVILEGES;

USE nova_memory;

CREATE TABLE IF NOT EXISTS conversation_memory (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    username VARCHAR(50) DEFAULT 'Guest',
    is_creator BOOLEAN DEFAULT FALSE,
    user_input TEXT,
    nova_response TEXT,
    session_id VARCHAR(50) DEFAULT 'default'
);

CREATE TABLE IF NOT EXISTS memory_context (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) DEFAULT 'Guest',
    summary TEXT,
    importance_score INT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(50) DEFAULT 'default'
);
```

Then set your password:
```bash
export NOVA_DB_PASSWORD="your_password"
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Voice Input | OpenAI Whisper (small) |
| Voice Output | Coqui TTS (VCTK) + SoX pitch shift |
| AI Engine | Ollama + Mistral 7B |
| Database | MariaDB / MySQL |
| Vision | OpenCV + EasyOCR / Tesseract |
| Audio | sounddevice + scipy |

## Project Structure

```
Nova-Assistant/
├── app.py                         # Main entry point
├── auth.py                        # Creator/guest authentication
├── config.json                    # Nova's configuration
├── enhanced_system_control.py     # System control commands
├── nova_vision.py                 # Computer vision module
├── voice_config.json              # TTS voice settings
├── requirements.txt               # Python dependencies
├── ai/
│   ├── chat.py                    # Core AI chat logic
│   ├── personality.py             # Persona loading
│   └── personas/
│       ├── neuro.py               # Chaotic persona
│       ├── evil.py                # Villain persona
│       └── no_emojis.py           # No-emoji persona
└── voice/
    ├── recorder.py                # Audio recording + VAD
    ├── stt.py                     # Speech-to-text (Whisper)
    └── tts.py                     # Text-to-speech (Coqui)
```

## License

MIT
