import whisper
import torch

class OptimizedSTT:
    def __init__(self):
        # Check for CUDA availability
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🚀 Loading Whisper model on {self.device.upper()}")
        
        # Use smaller, faster model for RTX 2050 4GB
        # "tiny" is fastest, "base" is good balance, "small" if you need better accuracy
        model_size = "small"  # Change to "tiny" for maximum speed
        
        # Load model with GPU acceleration
        self.model = whisper.load_model(model_size, device=self.device)
        print(f"✅ Whisper {model_size} model loaded on {self.device.upper()}")
    
    def transcribe_audio(self, file_path):
        print(f"📝 Transcribing on {self.device.upper()}...")
        
        # Use GPU-optimized parameters
        result = self.model.transcribe(
            file_path,
            fp16=True if self.device == "cuda" else False,  # Use half precision on GPU
            language="en",  # Specify language to skip detection
            task="transcribe",  # Explicit task
            verbose=False  # Reduce logging overhead
        )
        
        return result["text"]

# Global STT engine instance - THIS GOES IN stt.py
stt_engine = None

def initialize_stt():
    """Initialize the STT engine (call once at startup)"""
    global stt_engine
    if stt_engine is None:
        stt_engine = OptimizedSTT()

def transcribe_audio(file_path):
    """Main transcription function - replaces your existing one"""
    if stt_engine is None:
        initialize_stt()
    return stt_engine.transcribe_audio(file_path) # type: ignore
