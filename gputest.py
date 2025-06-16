import subprocess
import sys

def install_gpu_support():
    """Install GPU-optimized packages for CUDA 12.8"""
    
    print("🚀 Installing GPU support for Nova Voice Assistant...")
    print("Target: CUDA 12.8, RTX 2050 4GB")
    
    # CUDA 12.8 compatible PyTorch
    torch_cmd = [
        sys.executable, "-m", "pip", "install", 
        "torch==2.1.0", "torchaudio==2.1.0", 
        "--index-url", "https://download.pytorch.org/whl/cu121"  # CUDA 12.1 compatible
    ]
    
    commands = [
        torch_cmd,
        [sys.executable, "-m", "pip", "install", "openai-whisper"],
        [sys.executable, "-m", "pip", "install", "TTS>=0.21.0"],
        [sys.executable, "-m", "pip", "install", "sounddevice", "scipy"],
    ]
    
    for cmd in commands:
        print(f"Running: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True)
            print("✅ Success!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed: {e}")
            return False
    
    print("\n🎯 Testing GPU availability...")
    test_gpu()
    return True

def test_gpu():
    """Test GPU availability"""
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU: {torch.cuda.get_device_name(0)}")
            print(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f} GB")
        else:
            print("⚠️ CUDA not available - will use CPU")
    except ImportError:
        print("❌ PyTorch not installed")

if __name__ == "__main__":
    install_gpu_support()