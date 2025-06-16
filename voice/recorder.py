import sounddevice as sd
import numpy as np
import time
from scipy.io.wavfile import write
import threading

class NovaVoiceRecorder:
    def __init__(self, silence_timeout=2.0, min_recording_duration=1.0):
        """
        Nova's Voice Recorder with Wake Detection
        
        Args:
            silence_timeout: Seconds of silence before stopping recording
            min_recording_duration: Minimum recording duration in seconds
        """
        self.silence_timeout = silence_timeout
        self.min_recording_duration = min_recording_duration
        
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        
        # FIXED: Add recording control flags
        self.recording = []
        self.recording_started = False
        self.should_stop_recording = False
        self.recording_lock = threading.Lock()
        
        print("🎤 Nova Voice Recorder initialized")
        print(f"⏱️ Silence timeout: {self.silence_timeout}s")
        print(f"⏱️ Min recording: {self.min_recording_duration}s")
    
    def record_with_voice_detection(self, filename="input.wav", energy_threshold=0.01, max_duration=30):
        """
        FIXED: Record audio using voice activity detection with proper timeout handling
        
        Args:
            filename: Output filename
            energy_threshold: Voice detection threshold
            max_duration: Maximum recording duration in seconds
        
        Returns:
            str: Path to recorded file, or None if no audio recorded
        """
        print("🎧 Listening for your voice...")
        
        # FIXED: Reset all state
        with self.recording_lock:
            self.recording = []
            self.recording_started = False
            self.should_stop_recording = False
        
        # State tracking
        silent_chunks = 0
        speech_chunks = 0
        start_time = None
        last_speech_time = None
        
        # Detection parameters
        speech_threshold_chunks = 3  # Need 3 chunks of speech to start (300ms)
        silence_threshold_chunks = int(self.silence_timeout * 10)  # Convert to 100ms chunks
        
        print(f"🔍 Thresholds: {speech_threshold_chunks} speech chunks, {silence_threshold_chunks} silence chunks")
        
        def audio_callback(indata, frames, time_info, status):
            nonlocal silent_chunks, speech_chunks, start_time, last_speech_time
            
            if status:
                print(f"⚠️ Audio status: {status}")
            
            # FIXED: Check if we should stop
            with self.recording_lock:
                if self.should_stop_recording:
                    return
            
            # Calculate energy level (RMS)
            audio_chunk = indata.flatten()
            energy = np.sqrt(np.mean(audio_chunk**2))
            
            current_time = time.time()
            
            # Voice activity detection
            if energy > energy_threshold:
                speech_chunks += 1
                silent_chunks = 0
                last_speech_time = current_time
                
                # Start recording if we detect enough speech
                with self.recording_lock:
                    if not self.recording_started and speech_chunks >= speech_threshold_chunks:
                        print(f"\n🎙️ Voice detected! Recording started... (energy: {energy:.4f})")
                        self.recording_started = True
                        start_time = current_time
                    
                    # Add audio to recording if started
                    if self.recording_started:
                        self.recording.extend(audio_chunk)
                        
                        # Show recording progress
                        if len(self.recording) % (self.sample_rate // 4) == 0:  # Every 0.25 seconds
                            duration = len(self.recording) / self.sample_rate
                            print(f"🔴 Recording... {duration:.1f}s", end='\r')
            
            else:
                # Handle silence
                speech_chunks = max(0, speech_chunks - 1)  # Gradually decrease speech count
                
                with self.recording_lock:
                    if self.recording_started:
                        silent_chunks += 1
                        self.recording.extend(audio_chunk)  # Include silence for natural speech
                        
                        # Calculate durations
                        recording_duration = len(self.recording) / self.sample_rate
                        silence_duration = silent_chunks * 0.1  # 100ms chunks
                        time_since_last_speech = current_time - (last_speech_time or current_time)
                        
                        # FIXED: Multiple stop conditions
                        should_stop = False
                        stop_reason = ""
                        
                        # Condition 1: Silence timeout + minimum duration
                        if (silent_chunks >= silence_threshold_chunks and 
                            recording_duration >= self.min_recording_duration):
                            should_stop = True
                            stop_reason = f"Silence timeout ({silence_duration:.1f}s)"
                        
                        # Condition 2: Maximum duration reached
                        elif recording_duration >= max_duration:
                            should_stop = True
                            stop_reason = f"Maximum duration ({max_duration}s)"
                        
                        # Condition 3: Too long since last clear speech
                        elif (time_since_last_speech > self.silence_timeout * 1.5 and 
                              recording_duration >= self.min_recording_duration):
                            should_stop = True
                            stop_reason = f"Extended silence ({time_since_last_speech:.1f}s)"
                        
                        if should_stop:
                            print(f"\n⏹️ Stopping: {stop_reason}")
                            self.should_stop_recording = True
                        
                        # Show silence feedback
                        elif silent_chunks % 20 == 0:  # Every 2 seconds
                            print(f"🔇 Silence: {silence_duration:.1f}s", end='\r')
        
        # FIXED: Use proper stream management with timeout
        try:
            chunk_duration = 0.1  # 100ms chunks
            chunk_size = int(self.sample_rate * chunk_duration)
            
            # Start the audio stream
            stream = sd.InputStream(
                callback=audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=chunk_size,
                dtype=np.float32
            )
            
            with stream:
                start_wait_time = time.time()
                
                # FIXED: Proper waiting loop with multiple exit conditions
                while True:
                    time.sleep(0.1)
                    
                    with self.recording_lock:
                        # Exit if recording should stop
                        if self.should_stop_recording:
                            break
                        
                        # Exit if we have a recording and it's complete
                        if (self.recording_started and 
                            len(self.recording) > 0 and 
                            silent_chunks >= silence_threshold_chunks):
                            break
                    
                    # Overall timeout check
                    if time.time() - start_wait_time > max_duration + 10:  # Extra buffer
                        print(f"\n⏰ Overall timeout after {max_duration + 10} seconds")
                        break
                    
                    # No voice detected timeout
                    if (not self.recording_started and 
                        time.time() - start_wait_time > 10):  # 10 seconds to start speaking
                        print(f"\n⏰ No voice detected in 10 seconds")
                        break
                
        except KeyboardInterrupt:
            print("\n🛑 Recording interrupted by user")
            return None
        except Exception as e:
            print(f"\n❌ Recording error: {e}")
            return None
        
        # Process and save the recording
        with self.recording_lock:
            if self.recording and self.recording_started:
                print(f"\n⏹️ Recording stopped!")
                
                # Convert to numpy array
                audio_data = np.array(self.recording, dtype=np.float32)
                
                # Remove leading/trailing silence
                audio_data = self._trim_silence(audio_data, threshold=energy_threshold * 0.5)
                
                if len(audio_data) > 0:
                    # Normalize audio
                    if np.max(np.abs(audio_data)) > 0:
                        audio_data = audio_data * 0.8 / np.max(np.abs(audio_data))
                    
                    # Convert to int16 and save
                    audio_int16 = (audio_data * 32767).astype(np.int16)
                    write(filename, self.sample_rate, audio_int16)
                    
                    duration = len(audio_data) / self.sample_rate
                    print(f"💾 Audio saved: {filename}")
                    print(f"⏱️ Duration: {duration:.1f} seconds")
                    
                    return filename
                else:
                    print("⚠️ No audio content after processing")
                    return None
            else:
                print("❌ No voice detected. Try speaking louder or closer to the microphone.")
                return None
    
    def _trim_silence(self, audio_data, threshold=0.005):
        """Remove leading and trailing silence from audio"""
        if len(audio_data) == 0:
            return audio_data
        
        # Find start of audio (first sample above threshold)
        start_idx = 0
        for i, sample in enumerate(audio_data):
            if abs(sample) > threshold:
                start_idx = max(0, i - int(0.1 * self.sample_rate))  # Include 0.1s before
                break
        
        # Find end of audio (last sample above threshold)
        end_idx = len(audio_data)
        for i in range(len(audio_data) - 1, -1, -1):
            if abs(audio_data[i]) > threshold:
                end_idx = min(len(audio_data), i + int(0.1 * self.sample_rate))  # Include 0.1s after
                break
        
        return audio_data[start_idx:end_idx]
    
    def record_fixed_duration(self, filename="input.wav", duration=5):
        """Original fixed-duration recording (fallback method)"""
        print(f"🎙️ Recording for {duration} seconds...")
        recording = sd.rec(int(duration * self.sample_rate), 
                          samplerate=self.sample_rate, 
                          channels=self.channels)
        sd.wait()
        write(filename, self.sample_rate, recording)
        print("✅ Fixed duration recording complete.")
        return filename
    
    def calibrate_microphone(self, duration=3):
        """Calibrate microphone to determine optimal energy threshold"""
        print(f"🎛️ Calibrating microphone...")
        print(f"📢 Please stay quiet for {duration} seconds to measure background noise")
        
        # Record background noise
        background = sd.rec(int(duration * self.sample_rate), 
                           samplerate=self.sample_rate, 
                           channels=self.channels,
                           dtype=np.float32)
        sd.wait()
        
        # Calculate background energy
        background_energy = np.sqrt(np.mean(background.flatten()**2))
        
        print(f"📊 Background noise level: {background_energy:.6f}")
        
        # Recommend threshold (3-5x background noise)
        recommended_threshold = background_energy * 4
        print(f"💡 Recommended voice threshold: {recommended_threshold:.6f}")
        
        return recommended_threshold
    
    def test_voice_detection(self, threshold=None):
        """Test voice detection with real-time feedback"""
        if threshold is None:
            threshold = 0.01
        
        print(f"🧪 Testing voice detection (threshold: {threshold:.6f})")
        print("🗣️ Speak to test detection, press Ctrl+C to stop")
        
        def callback(indata, frames, time, status):
            energy = np.sqrt(np.mean(indata.flatten()**2))
            
            if energy > threshold:
                print(f"🔊 VOICE DETECTED! Energy: {energy:.6f}", end='\r')
            else:
                print(f"🔇 silence... Energy: {energy:.6f}", end='\r')
        
        try:
            with sd.InputStream(callback=callback, 
                               channels=1, 
                               samplerate=self.sample_rate,
                               blocksize=int(0.1 * self.sample_rate)):
                while True:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n✅ Voice detection test complete")

# Global recorder instance (for compatibility with existing code)
nova_recorder = NovaVoiceRecorder()

def record_audio(filename="input.wav", duration=None, use_voice_detection=True):
    """
    Main recording function - backwards compatible with existing code
    
    Args:
        filename: Output filename
        duration: If specified, use fixed duration recording
        use_voice_detection: If True, use voice detection; if False, use fixed duration
    """
    global nova_recorder
    
    if duration is not None or not use_voice_detection:
        # Use fixed duration recording (original behavior)
        duration = duration or 5
        return nova_recorder.record_fixed_duration(filename, duration)
    else:
        # Use voice detection recording (new behavior)
        return nova_recorder.record_with_voice_detection(filename)

def calibrate_voice_detection():
    """Calibrate voice detection threshold"""
    return nova_recorder.calibrate_microphone()

def test_voice_detection(threshold=None):
    """Test voice detection"""
    nova_recorder.test_voice_detection(threshold)

# Convenience functions for different recording modes
def record_with_voice_wake(filename="input.wav", sensitivity=0.01):
    """Record with voice wake detection"""
    recorder = NovaVoiceRecorder(silence_timeout=2.0, min_recording_duration=0.5)
    return recorder.record_with_voice_detection(filename, sensitivity)

def record_quick_response(filename="input.wav"):
    """Quick response recording (shorter timeouts)"""
    recorder = NovaVoiceRecorder(silence_timeout=1.5, min_recording_duration=0.3)
    return recorder.record_with_voice_detection(filename, energy_threshold=0.008)

if __name__ == "__main__":
    # Test the recording system
    print("🧪 Testing Nova Voice Recording System")
    print("=" * 50)
    
    choice = input("Choose test:\n1. Calibrate microphone\n2. Test voice detection\n3. Record with voice wake\n4. Fixed duration recording\nChoice (1-4): ")
    
    if choice == "1":
        threshold = calibrate_voice_detection()
        print(f"Use threshold: {threshold:.6f}")
    elif choice == "2":
        test_voice_detection()
    elif choice == "3":
        print("🎤 Testing voice wake recording...")
        result = record_with_voice_wake("test_wake.wav")
        if result:
            print(f"✅ Success! Recorded to {result}")
    elif choice == "4":
        print("🎤 Testing fixed duration recording...")
        result = record_audio("test_fixed.wav", duration=3, use_voice_detection=False)
        if result:
            print(f"✅ Success! Recorded to {result}")
    else:
        print("Invalid choice")