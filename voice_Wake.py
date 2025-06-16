import numpy as np
import sounddevice as sd
import threading
import time
import queue
from scipy.io.wavfile import write
import webrtcvad
from collections import deque

class FixedVoiceWakeDetector:
    def __init__(self, wake_words=None, silence_timeout=2.0, min_recording_duration=1.0):
        """
        Fixed Voice wake detection system for Nova with aggressive debugging
        """
        self.wake_words = wake_words or ["nova", "hey nova", "ok nova"]
        self.silence_timeout = silence_timeout
        self.min_recording_duration = min_recording_duration
        
        # Audio settings
        self.sample_rate = 16000
        self.channels = 1
        self.frame_duration_ms = 20  # 20ms frames
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)  # 320 samples
        
        # Voice Activity Detection - FIXED: Use less aggressive mode
        self.vad = webrtcvad.Vad(0)  # Mode 0 is LEAST aggressive
        
        # Recording state
        self.is_listening = False
        self.is_recording = False
        self.recording_complete = False
        self.audio_buffer = deque(maxlen=int(10 * self.sample_rate / self.frame_size))
        self.recording_buffer = []
        
        # Threading
        self.audio_queue = queue.Queue(maxsize=50)
        self.stop_event = threading.Event()
        self.recording_result = None
        
        # FIXED: More conservative thresholds
        self.energy_threshold = 0.003  # Lower threshold
        self.background_energy = 0.001
        self.vad_enabled = True  # Can disable VAD if problematic
        
        # FIXED: Force stop mechanisms
        self.force_stop_after_seconds = 15  # Hard stop after 15 seconds
        self.recording_start_time = None
        
        print("🎤 DEBUGGING Voice Wake Detector initialized")
        print(f"🔊 Wake words: {', '.join(self.wake_words)}")
        print(f"⏱️ Silence timeout: {self.silence_timeout}s")
        print(f"🚨 Force stop after: {self.force_stop_after_seconds}s")
    
    def preprocess_audio_for_vad(self, audio_chunk):
        """Preprocess audio chunk for VAD"""
        # Convert float32 to int16
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        
        # Ensure exact frame size
        if len(audio_int16) != self.frame_size:
            if len(audio_int16) < self.frame_size:
                audio_int16 = np.pad(audio_int16, (0, self.frame_size - len(audio_int16)), 'constant')
            else:
                audio_int16 = audio_int16[:self.frame_size]
        
        return audio_int16
    
    def is_speech_vad(self, audio_chunk):
        """VAD with fallback - FIXED: More conservative"""
        try:
            if not self.vad_enabled:
                return self.is_speech_energy(audio_chunk)
            
            audio_int16 = self.preprocess_audio_for_vad(audio_chunk)
            audio_bytes = audio_int16.tobytes()
            
            vad_result = self.vad.is_speech(audio_bytes, self.sample_rate)
            energy_result = self.is_speech_energy(audio_chunk)
            
            # FIXED: Both VAD AND energy must agree for speech detection
            # This prevents false positives from either method
            return vad_result and energy_result
            
        except Exception as e:
            print(f"⚠️ VAD error: {e}")
            return self.is_speech_energy(audio_chunk)
    
    def is_speech_energy(self, audio_chunk):
        """Energy-based speech detection"""
        energy = np.sqrt(np.mean(audio_chunk ** 2))
        threshold = max(self.energy_threshold, self.background_energy * 4)
        return energy > threshold
    
    def audio_callback(self, indata, frames, time, status):
        """Audio callback with overflow protection"""
        if status:
            print(f"⚠️ Audio status: {status}")
        
        try:
            # Clear queue if full
            if self.audio_queue.full():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    pass
            
            self.audio_queue.put(indata.copy(), block=False)
            
        except Exception as e:
            print(f"⚠️ Callback error: {e}")
    
    def process_audio_stream(self):
        """FIXED: Aggressive debugging and multiple stop conditions"""
        consecutive_silence = 0
        consecutive_speech = 0
        total_frames_processed = 0
        
        speech_frames_for_wake = 10  # Need 200ms of speech to start
        silence_frames_to_stop = int(self.silence_timeout * 1000 / self.frame_duration_ms)
        
        print(f"🔍 DEBUGGING - Need {speech_frames_for_wake} speech frames to start")
        print(f"🔍 DEBUGGING - Need {silence_frames_to_stop} silence frames to stop")
        
        # Calibrate background noise first
        self._calibrate_background_noise()
        
        while not self.stop_event.is_set():
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                audio_chunk = audio_chunk.flatten()
                
                # Process in VAD frame sizes
                for i in range(0, len(audio_chunk), self.frame_size):
                    frame = audio_chunk[i:i + self.frame_size]
                    if len(frame) < self.frame_size:
                        continue
                    
                    total_frames_processed += 1
                    self.audio_buffer.append(frame)
                    
                    # Check for speech
                    has_speech = self.is_speech_vad(frame)
                    energy = np.sqrt(np.mean(frame ** 2))
                    
                    # DEBUGGING: Show real-time detection
                    if total_frames_processed % 25 == 0:  # Every 500ms
                        status = "🔊 SPEECH" if has_speech else "🔇 silence"
                        print(f"{status} | Energy: {energy:.6f} | Frames: {total_frames_processed}")
                    
                    # Handle speech detection
                    if has_speech:
                        consecutive_speech += 1
                        consecutive_silence = 0
                        
                        # Start recording
                        if not self.is_recording and consecutive_speech >= speech_frames_for_wake:
                            print(f"\n🎙️ WAKE DETECTED! Starting recording after {consecutive_speech} speech frames")
                            self.start_recording()
                        
                        if self.is_recording:
                            self.recording_buffer.append(frame)
                    
                    else:
                        consecutive_silence += 1
                        consecutive_speech = 0
                        
                        if self.is_recording:
                            self.recording_buffer.append(frame)
                            
                            # DEBUGGING: Show silence progress
                            if consecutive_silence % 25 == 0:
                                silence_seconds = consecutive_silence * self.frame_duration_ms / 1000
                                recording_seconds = len(self.recording_buffer) * self.frame_duration_ms / 1000
                                print(f"🔇 SILENCE: {silence_seconds:.1f}s / {self.silence_timeout}s | Recording: {recording_seconds:.1f}s")
                            
                            # MULTIPLE STOP CONDITIONS
                            recording_duration = len(self.recording_buffer) * self.frame_duration_ms / 1000
                            silence_duration = consecutive_silence * self.frame_duration_ms / 1000
                            
                            should_stop = False
                            stop_reason = ""
                            
                            # Condition 1: Silence timeout + minimum duration
                            if (consecutive_silence >= silence_frames_to_stop and 
                                recording_duration >= self.min_recording_duration):
                                should_stop = True
                                stop_reason = f"Silence timeout ({silence_duration:.1f}s >= {self.silence_timeout}s)"
                            
                            # Condition 2: Force stop after maximum time
                            elif recording_duration >= self.force_stop_after_seconds:
                                should_stop = True
                                stop_reason = f"Force stop ({recording_duration:.1f}s >= {self.force_stop_after_seconds}s)"
                            
                            # Condition 3: Too much silence relative to recording
                            elif (silence_duration > self.silence_timeout * 1.5 and 
                                  recording_duration >= self.min_recording_duration):
                                should_stop = True
                                stop_reason = f"Excessive silence ({silence_duration:.1f}s)"
                            
                            if should_stop:
                                print(f"\n⏹️ STOPPING RECORDING: {stop_reason}")
                                print(f"📊 Final stats - Recording: {recording_duration:.1f}s, Silence: {silence_duration:.1f}s")
                                self.stop_recording()
                                break
                
            except queue.Empty:
                # Handle queue timeout
                if self.is_recording and self.recording_start_time:
                    elapsed = time.time() - self.recording_start_time
                    if elapsed > self.force_stop_after_seconds:
                        print(f"\n⏰ FORCE STOPPING after {elapsed:.1f}s (queue timeout)")
                        self.stop_recording()
                continue
            except Exception as e:
                print(f"❌ Processing error: {e}")
                continue
    
    def _calibrate_background_noise(self):
        """Quickly calibrate background noise"""
        print("📊 Calibrating background noise...")
        background_samples = []
        calibration_frames = 25  # 0.5 seconds
        
        start_time = time.time()
        while len(background_samples) < calibration_frames and time.time() - start_time < 2:
            try:
                audio_chunk = self.audio_queue.get(timeout=0.1)
                audio_chunk = audio_chunk.flatten()
                
                for i in range(0, len(audio_chunk), self.frame_size):
                    frame = audio_chunk[i:i + self.frame_size]
                    if len(frame) == self.frame_size:
                        energy = np.sqrt(np.mean(frame ** 2))
                        background_samples.append(energy)
                        if len(background_samples) >= calibration_frames:
                            break
            except queue.Empty:
                continue
        
        if background_samples:
            self.background_energy = np.mean(background_samples)
            adaptive_threshold = self.background_energy * 5
            
            # Update threshold if background is louder than default
            if adaptive_threshold > self.energy_threshold:
                self.energy_threshold = adaptive_threshold
            
            print(f"📊 Background: {self.background_energy:.6f}, Threshold: {self.energy_threshold:.6f}")
        else:
            print("⚠️ Could not calibrate background noise")
    
    def start_recording(self):
        """Start recording with timestamp"""
        if not self.is_recording:
            self.is_recording = True
            self.recording_complete = False
            self.recording_buffer = []
            self.recording_start_time = time.time()
            
            # Add pre-buffer
            prebuffer_frames = int(0.3 * 1000 / self.frame_duration_ms)  # 300ms
            if len(self.audio_buffer) >= prebuffer_frames:
                pre_audio = list(self.audio_buffer)[-prebuffer_frames:]
                self.recording_buffer.extend(pre_audio)
                print(f"📝 Added {len(pre_audio)} frames pre-buffer")
    
    def stop_recording(self):
        """Stop recording with cleanup"""
        if self.is_recording:
            self.is_recording = False
            self.recording_complete = True
            self.recording_start_time = None
            
            if self.recording_buffer:
                audio_data = np.concatenate(self.recording_buffer)
                # Trim excessive silence
                audio_data = self._trim_silence(audio_data)
                self.recording_result = audio_data
                
                duration = len(audio_data) / self.sample_rate
                print(f"✅ Recording complete: {duration:.1f}s ({len(audio_data)} samples)")
                return audio_data
        return None
    
    def _trim_silence(self, audio_data):
        """Trim silence from ends"""
        if len(audio_data) == 0:
            return audio_data
        
        threshold = self.background_energy * 2
        
        # Find start (skip initial silence)
        start_idx = 0
        for i in range(len(audio_data)):
            if abs(audio_data[i]) > threshold:
                start_idx = max(0, i - int(0.1 * self.sample_rate))
                break
        
        # Find end (skip trailing silence)
        end_idx = len(audio_data)
        for i in range(len(audio_data) - 1, -1, -1):
            if abs(audio_data[i]) > threshold:
                end_idx = min(len(audio_data), i + int(0.2 * self.sample_rate))
                break
        
        trimmed = audio_data[start_idx:end_idx]
        print(f"✂️ Trimmed: {len(audio_data)} -> {len(trimmed)} samples")
        return trimmed
    
    def listen_for_wake_word(self, timeout=30):
        """Main listening function with debugging"""
        print("=" * 60)
        print("👂 DEBUGGING MODE - Starting wake word detection")
        print(f"💬 Say: {', '.join(self.wake_words)}")
        print(f"⏰ Timeout: {timeout}s, Force stop: {self.force_stop_after_seconds}s")
        print("=" * 60)
        
        self.is_listening = True
        self.recording_complete = False
        self.recording_result = None
        self.stop_event.clear()
        
        # Start processing thread
        processing_thread = threading.Thread(target=self.process_audio_stream, daemon=True)
        processing_thread.start()
        
        try:
            with sd.InputStream(
                callback=self.audio_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.frame_size,
                dtype=np.float32
            ):
                start_time = time.time()
                
                while self.is_listening and not self.recording_complete:
                    time.sleep(0.1)
                    
                    if time.time() - start_time > timeout:
                        print(f"\n⏰ MAIN TIMEOUT after {timeout}s")
                        break
                
                self.stop_listening()
                processing_thread.join(timeout=1.0)
                
                print("=" * 60)
                return self.recording_result
                
        except KeyboardInterrupt:
            print("\n🛑 Interrupted by user")
            self.stop_listening()
            return None
        except Exception as e:
            print(f"❌ Stream error: {e}")
            self.stop_listening()
            return None
    
    def stop_listening(self):
        """Stop all activities"""
        self.is_listening = False
        self.is_recording = False
        self.stop_event.set()
        print("🔇 All detection stopped")
    
    def save_recording(self, audio_data, filename="debug_recording.wav"):
        """Save with debug info"""
        if audio_data is not None and len(audio_data) > 0:
            # Normalize
            audio_data = audio_data - np.mean(audio_data)
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:
                audio_data = audio_data * 0.8 / max_val
            
            audio_int16 = (audio_data * 32767).astype(np.int16)
            write(filename, self.sample_rate, audio_int16)
            
            duration = len(audio_data) / self.sample_rate
            print(f"💾 SAVED: {filename} ({duration:.1f}s, {len(audio_data)} samples)")
            return filename
        else:
            print("❌ No audio data to save")
            return None

# Test function with debugging
def test_debug_wake_detection():
    """Test with full debugging output"""
    print("🧪 DEBUGGING Wake Word Detection")
    print("🚨 This will show detailed detection info")
    
    detector = FixedVoiceWakeDetector(
        silence_timeout=3.0,  # 3 seconds silence
        min_recording_duration=1.0
    )
    
    try:
        audio_data = detector.listen_for_wake_word(timeout=45)
        
        if audio_data is not None:
            filename = detector.save_recording(audio_data, "debug_wake_test.wav")
            if filename:
                print(f"✅ SUCCESS! Check {filename}")
            else:
                print("❌ Failed to save recording")
        else:
            print("❌ No audio recorded")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
    finally:
        detector.stop_listening()

if __name__ == "__main__":
    test_debug_wake_detection()