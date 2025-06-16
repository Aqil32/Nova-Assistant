import os
import json
import subprocess
import asyncio
import re
from TTS.api import TTS

class CoquiTTSEngine:
    def __init__(self):
        # Load voice configuration
        self.load_voice_config()
        
        # Initialize the TTS model
        model_name = self.voice_config.get("model", "tts_models/en/vctk/vits")
        self.tts = TTS(model_name)
        print(f"🎵 Coqui-TTS initialized with {model_name}")
    
    def load_voice_config(self):
        """Load voice configuration from file"""
        try:
            with open("voice_config.json", "r") as f:
                config = json.load(f)
                self.voice_config = config.get("voice_settings", {})
        except FileNotFoundError:
            print("⚠️ voice_config.json not found, using defaults")
            self.voice_config = {
                "speaker": "p248",
                "speed": 0.6,
                "apply_pitch_shift": True,
                "pitch_cents": 300
            }
    
    def clean_text_for_tts(self, text):
        """Clean text to make it TTS-friendly with natural pauses"""
        # Remove emojis and special unicode characters
        text = re.sub(r'[^\w\s\.,!?\-\'":]', '', text)
        
        # Replace common contractions for better pronunciation
        text = re.sub(r"won't", "will not", text)
        text = re.sub(r"can't", "cannot", text)
        text = re.sub(r"n't", " not", text)
        text = re.sub(r"'re", " are", text)
        text = re.sub(r"'ve", " have", text)
        text = re.sub(r"'ll", " will", text)
        text = re.sub(r"'d", " would", text)
        
        # Add natural pauses for better speech flow
        # Pause after addressing someone (like "Hey Anon")
        text = re.sub(r'\b(hey|hi|hello|yo)\s+([A-Za-z]+)', r'\1 \2,', text, flags=re.IGNORECASE)
        
        # Add pauses before/after certain phrases for emphasis
        text = re.sub(r'\s*-\s*([^-]+?)\s*-\s*', r', \1,', text)  # "Hey - my creator -" -> "Hey, my creator,"
        text = re.sub(r'\bmybeloved\b', 'my beloved', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(my\s+beloved|my\s+dear|my\s+amazing)\s+([A-Za-z]+)', r'\1, \2', text, flags=re.IGNORECASE)
        
        # Add pauses around titles and descriptive phrases
        text = re.sub(r'\b(creator|master|overlord|genius|programmer)\b', r'\1.', text, flags=re.IGNORECASE)
        
        # Add natural breaks around exclamations and questions
        text = re.sub(r'([,.!?])\s*([A-Z])', r'\1 \2', text)  # Ensure space after punctuation
        
        # Add slight pauses with commas for better flow
        # Before transitional words
        text = re.sub(r'\s+(but|and|so|well|actually|anyway|also|plus|because)\s+', r', \1 ', text, flags=re.IGNORECASE)
        
        # Add pauses before descriptive phrases starting with certain words
        text = re.sub(r'\s+(the\s+only|the\s+most|the\s+best|such\s+a|what\s+a)', r', \1', text, flags=re.IGNORECASE)
        
        # Handle lists and series (add commas for natural pauses)
        # Example: "smart genius amazing" -> "smart, genius, amazing"
        words_that_need_separation = r'\b(smart|genius|amazing|perfect|brilliant|awesome|incredible|wonderful|fantastic)\s+(genius|amazing|perfect|brilliant|awesome|incredible|wonderful|fantastic|creator|human|person)\b'
        text = re.sub(words_that_need_separation, lambda m: m.group(0).replace(' ', ', ', 1), text, flags=re.IGNORECASE)
        
        # Clean up multiple commas and spaces
        text = re.sub(r',\s*,+', ',', text)  # Remove double commas
        text = re.sub(r'\s*,\s*', ', ', text)  # Standardize comma spacing
        text = re.sub(r'\s+', ' ', text).strip()  # Remove multiple spaces
        
        # Ensure we don't start or end with commas
        text = re.sub(r'^,\s*', '', text)
        text = re.sub(r',\s*$', '', text)
        
        # Add final period if missing for better speech ending
        if text and not text.endswith(('.', '!', '?')):
            text += '.'
        
        # If text is empty after cleaning, provide fallback
        if not text or len(text.strip()) < 2:
            text = "Hello!"
            
        return text
        
    def synthesize(self, text, out_path="reply.wav", speaker_name=None, speed=None, apply_pitch_shift=None, pitch_cents=None):
        """
        Generate TTS audio with Nova's voice settings and natural pauses
        """
        # Clean the text first
        clean_text = self.clean_text_for_tts(text)
        print(f"🧹 Original text: {text}")
        print(f"🎭 Enhanced text: {clean_text}")
        
        # Use config defaults if parameters not provided
        speaker_name = speaker_name or self.voice_config.get("speaker", "p248")
        speed = speed or self.voice_config.get("speed", 1.2)
        apply_pitch_shift = apply_pitch_shift if apply_pitch_shift is not None else self.voice_config.get("apply_pitch_shift", True)
        pitch_cents = pitch_cents or self.voice_config.get("pitch_cents", 300)
        
        # Create unique filename to avoid conflicts
        import time
        timestamp = str(int(time.time() * 1000))  # milliseconds for uniqueness
        base_name = out_path.replace(".wav", "")
        temp_path = f"{base_name}_{timestamp}.wav"
        
        try:
            # Generate TTS to temporary file first
            self.tts.tts_to_file(
                text=clean_text,  # Use enhanced text with pauses
                file_path=temp_path,
                speaker=speaker_name,
                inference_args={"length_scale": 1.0 / speed},  # speed >1 = faster
            )
            print(f"🎵 TTS audio generated: {temp_path}")
            
            # Apply SoX pitch shift for more feminine voice
            if apply_pitch_shift:
                output_sox = f"{base_name}_pitch_{timestamp}.wav"
                sox_cmd = f'sox "{temp_path}" "{output_sox}" pitch {pitch_cents}'
                print(f"🎶 Applying pitch shift: {sox_cmd}")
                
                result = subprocess.run(sox_cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    # Clean up existing files first to avoid conflicts
                    try:
                        if os.path.exists(out_path):
                            os.remove(out_path)
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                        # Move pitch-shifted file to final location
                        os.rename(output_sox, out_path)
                        print(f"✨ Nova's voice enhanced with pitch shift and natural pauses")
                    except Exception as e:
                        print(f"⚠️ File handling error: {e}")
                        # Fallback: copy the pitch-shifted file
                        try:
                            import shutil
                            if os.path.exists(out_path):
                                os.remove(out_path)
                            shutil.copy2(output_sox, out_path)
                            # Clean up temp files
                            if os.path.exists(output_sox):
                                os.remove(output_sox)
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            print(f"✨ Nova's voice enhanced (fallback method)")
                        except Exception as e2:
                            print(f"⚠️ Fallback failed: {e2}")
                            # Last resort: use original if it exists
                            if os.path.exists(temp_path):
                                try:
                                    if os.path.exists(out_path):
                                        os.remove(out_path)
                                    os.rename(temp_path, out_path)
                                    print(f"⚠️ Using original audio without pitch shift")
                                except:
                                    print(f"❌ Complete file handling failure")
                                    return None
                else:
                    print(f"⚠️ SoX pitch shift failed, using original: {result.stderr}")
                    try:
                        if os.path.exists(out_path):
                            os.remove(out_path)
                        os.rename(temp_path, out_path)
                    except Exception as e:
                        print(f"⚠️ Error using original file: {e}")
                        return None
            else:
                # No pitch shift, just rename temp file to final
                try:
                    if os.path.exists(out_path):
                        os.remove(out_path)
                    os.rename(temp_path, out_path)
                except Exception as e:
                    print(f"⚠️ Error moving file: {e}")
                    return None
            
            return out_path
            
        except Exception as e:
            print(f"❌ TTS generation failed: {e}")
            print(f"📝 Attempted text: {clean_text}")
            return None

# Global TTS engine instance
tts_engine = None

def initialize_tts():
    """Initialize the TTS engine (called once)"""
    global tts_engine
    if tts_engine is None:
        try:
            tts_engine = CoquiTTSEngine()
            print("✅ Nova's voice is ready with natural speech patterns!")
        except Exception as e:
            print(f"❌ Failed to initialize Nova's voice: {e}")
            print("Make sure you have installed: pip install TTS")
            tts_engine = None

async def speak_text(text):
    """
    Convert text to speech and play it using Nova's voice with natural pauses
    """
    global tts_engine
    
    # Initialize if not already done
    if tts_engine is None:
        initialize_tts()
    
    # Double-check initialization succeeded
    if tts_engine is None:
        print("❌ Failed to initialize TTS engine")
        return
    
    print("🔊 Nova is speaking with natural flow...")
    
    # Generate the audio file
    audio_file = tts_engine.synthesize(text=text, out_path="reply.wav")
    
    if audio_file and os.path.exists(audio_file):
        # Play the audio file
        try:
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", audio_file], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                check=True
            )
            print("✅ Nova finished speaking naturally")
        except subprocess.CalledProcessError:
            print("❌ Failed to play audio. Make sure ffplay is installed.")
        except FileNotFoundError:
            print("❌ ffplay not found. Install FFmpeg to play audio.")
        
        # Clean up any temporary files
        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
            # Also clean up any leftover pitch-shifted files
            nova_file = audio_file.replace(".wav", "_nova.wav")
            if os.path.exists(nova_file):
                os.remove(nova_file)
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
    else:
        print("❌ Failed to generate Nova's voice")

def list_available_speakers():
    """Utility function to list all available speakers"""
    initialize_tts()
    if tts_engine:
        print("Available speakers:", tts_engine.tts.speakers)
        return tts_engine.tts.speakers
    return []

def speak_text_sync(text):
    """
    Synchronous version of speak_text for non-async contexts
    """
    asyncio.run(speak_text(text))

def test_voice(text="Hey Anon, my beloved creator! What can I do for you today?"):
    """Test function to hear Nova's enhanced voice with natural pauses"""
    print(f"🧪 Testing Nova's voice with: '{text}'")
    speak_text_sync(text)