import json
import importlib

# Load config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

creator = CONFIG.get("creator_name", "my creator")

# Load selected persona module
persona_module = importlib.import_module(f"ai.personas." + CONFIG["persona"])

def get_persona():
    return persona_module.SYSTEM_PROMPT.replace("{{CREATOR}}", creator)

def get_config():
    return CONFIG
