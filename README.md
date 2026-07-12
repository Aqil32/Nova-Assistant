# Nova AI Assistant 🤖

Personal AI assistant by **Aqil** — inspired by JARVIS and Neuro-sama. Voice-controlled, web-browsing, system-controlling digital companion.

> **⚠️ Security Notice:** Never commit `nova_auth.json` or any `.env` file to version control. The `.gitignore` already protects these.

---

## ✨ Features

| Feature | Details | Access |
|---------|---------|--------|
| 🎤 **Voice Chat** | Speak naturally, Nova talks back | All users |
| 🌐 **Web Search** | Google, YouTube, open websites | All users |
| 💬 **AI Conversation** | Ollama + Mistral 7B with memory | All users |
| 👑 **Creator Mode** | Secret phrase unlocks full controls | Creator only |
| 🖥️ **System Control** | Launch apps, volume, file creation | Creator only |
| 👁️ **Screen Vision** | Screenshots, OCR, screen description | All users |
| 🗣️ **Voice Output** | Coqui TTS with anime-style pitch shift | All users |
| 💾 **Conversation Memory** | MariaDB/MySQL (falls back to in-memory) | All users |
| 🎭 **Personas** | Neuro, Evil, No-emojis, and more | Configurable |

---

## 📋 Requirements

- **Python** 3.10+
- **[Ollama](https://ollama.com)** with Mistral 7B
- **FFmpeg** — audio playback
- **SoX** — voice pitch shifting
- **MariaDB/MySQL** — *(optional, falls back to in-memory)*
- **CUDA-capable GPU** — *(optional, for faster Whisper/TTS)*

### Install System Dependencies (Linux)

```bash
sudo apt install ffmpeg sox
```

### Install System Dependencies (Windows)

Download from:
- [FFmpeg](https://ffmpeg.org/download.html)
- [SoX](http://sox.sourceforge.net/)

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Aqil32/Nova-Assistant.git
cd Nova-Assistant

# Recommended: create a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Setup Ollama

```bash
# Install Ollama (if not already)
curl -fsSL https://ollama.com/install.sh | sh

# Pull Mistral 7B model
ollama pull mistral

# Make sure Ollama is running
ollama serve
```

### 3. Setup Database (Optional)

See [Database Setup](#database-setup) section below.

### 4. Configure Environment (Optional)

Copy this into `.env` or export directly:

```bash
export NOVA_DB_PASSWORD="your_secure_password"
```

### 5. Run Nova!

```bash
python app.py
```

---

## 🔐 Authentication

Nova uses a **secret phrase** system:

| Role | Access |
|------|--------|
| 👑 **Creator** (`Anon`) | Full system control, app launching, file operations |
| 👤 **Guest** (`Guest`) | Conversation, web search, YouTube, screen view |

### Secret Commands

Say these to Nova during conversation:

| Command | Effect | Requires Creator? |
|---------|--------|:---:|
| `nova reset yourself` | Wipes conversation memory | ✅ |
| `nova go quiet` | Silent mode (Nova stops talking back) | ✅ |
| `praise your creator` | Nova brags about Aqil | ❌ |

### Change Secret Phrase

Delete `nova_auth.json` and restart Nova — it will prompt for a new one.

---

## 🎭 Personas

Switch Nova's personality in `config.json`:

| Persona | Vibe |
|---------|------|
| `neuro` 🌀 | Chaotic, unhinged, lovable disaster — like a sassy streamer |
| `evil` 😈 | Darkly charismatic, dramatic villain (all bark, no bite!) |
| `no_emojis` 🎙️ | Confident, cocky, streamer-girl energy — no emojis in text |

```json
{
  "persona": "no_emojis",
  "memory_enabled": true,
  "context_length": 5,
  "creator_name": "Aqil"
}
```

---

## ⚙️ Configuration

### `config.json`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `persona` | string | `"no_emojis"` | Active personality (`neuro`, `evil`, `no_emojis`) |
| `memory_enabled` | bool | `true` | Save conversation history to DB |
| `context_length` | int | `5` | Number of past exchanges to remember |
| `creator_name` | string | `"Aqil"` | Your name (used in personality prompts) |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NOVA_DB_HOST` | `localhost` | Database host |
| `NOVA_DB_USER` | `nova_user` | Database user |
| `NOVA_DB_PASSWORD` | *(empty)* | Database password |
| `NOVA_DB_NAME` | `nova_memory` | Database name |

### `voice_config.json`

| Key | Default | Description |
|-----|---------|-------------|
| `speaker` | `p248` | VCTK voice ID (see alternatives below) |
| `speed` | `0.3` | Speech speed (lower = slower) |
| `apply_pitch_shift` | `true` | Apply anime-style pitch boost |
| `pitch_cents` | `270` | Pitch shift amount (higher = cuter) |

Pitch presets: `cute` (400), `normal` (300), `mature` (200), `deep` (100)

---

## 🎤 Recording Modes

On startup, Nova offers 3 recording modes:

| Mode | How It Works | Best For |
|------|-------------|----------|
| **Voice Wake** (1) | Nova detects when you speak and stops when you pause | Hands-free, natural flow |
| **Fixed Duration** (2) | Records exactly 5 seconds each turn | Quiet environments |
| **Continuous** (3) | Keeps listening after each reply | Long conversations |

---

## 🗄️ Database Setup

```sql
CREATE DATABASE nova_memory;
CREATE USER 'nova_user'@'localhost' IDENTIFIED BY 'your_secure_password';
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

Then either export the password:

```bash
export NOVA_DB_PASSWORD="your_secure_password"
```

Or add to a `.env` file (auto-loaded if present):

```
NOVA_DB_PASSWORD=your_secure_password
```

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Ollama not found** | Install Ollama: `curl -fsSL https://ollama.com/install.sh \| sh` |
| **Microphone not working** | Check `pulseaudio` / `pipewire`: `pactl info` |
| **Whisper too slow** | Edit `voice/stt.py` → change `model_size = "tiny"` |
| **No audio output** | Install FFmpeg: `sudo apt install ffmpeg` |
| **Pitch shift not working** | Install SoX: `sudo apt install sox` |
| **Database error** | Check MariaDB is running: `systemctl status mariadb` |
| **"Module not found"** | Activate venv: `source venv/bin/activate && pip install -r requirements.txt` |

---

## 📁 Project Structure

```
Nova-Assistant/
├── app.py                         # 🚀 Main entry point
├── auth.py                        # 🔐 Creator/guest authentication
├── config.json                    # ⚙️ Nova's configuration
├── enhanced_system_control.py     # 🖥️ System control commands
├── nova_vision.py                 # 👁️ Computer vision module
├── voice_config.json              # 🗣️ TTS voice settings
├── requirements.txt               # 📦 Python dependencies
├── .gitignore                     # 🛡️ Safe files to ignore
│
├── ai/
│   ├── chat.py                    # 💬 Core AI chat + Ollama integration
│   ├── personality.py             # 🎭 Persona loader
│   └── personas/
│       ├── neuro.py               # 🌀 Chaotic persona
│       ├── evil.py                # 😈 Villain persona
│       └── no_emojis.py           # 🎙️ Sassy streamer persona
│
└── voice/
    ├── recorder.py                # 🎤 Audio recording + VAD
    ├── stt.py                     # 📝 Speech-to-text (Whisper)
    └── tts.py                     # 🔊 Text-to-speech (Coqui)
```

---

## 🧠 Tech Stack

| Component | Technology |
|-----------|-----------|
| Speech-to-Text | OpenAI Whisper (`small`, GPU-accelerated) |
| Text-to-Speech | Coqui TTS (VCTK vits) + SoX pitch shift |
| AI Engine | Ollama + Mistral 7B |
| Conversation Memory | MariaDB / MySQL + in-memory fallback |
| Computer Vision | OpenCV, EasyOCR, Tesseract, PyAutoGUI |
| Audio Capture | sounddevice + WebRTC VAD |
| Audio Processing | scipy, NumPy, SoX |

---

## 🙌 Credits

Created by **Aqil** — first AI project, inspired by **JARVIS** and **Neuro-sama**.

---

## 📄 License

MIT
