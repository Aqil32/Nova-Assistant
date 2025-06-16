import asyncio
import sys
import os
from voice.recorder import record_audio, calibrate_voice_detection, nova_recorder
from voice.stt import transcribe_audio
from ai.chat import query_ollama, set_user_context
from voice.tts import speak_text
from auth import authenticate_user, get_user_info

class NovaVoiceAssistant:
    def __init__(self):
        self.voice_threshold = 0.01  # Default voice detection threshold
        self.use_voice_wake = True
        self.continuous_mode = False
        self.session_active = True
        
    async def initialize(self):
        """Initialize Nova with user authentication and voice calibration"""
        print("🚀 Starting Nova Voice Assistant...")
        print("=" * 50)
        
        # Authenticate user
        username, is_creator = authenticate_user()
        set_user_context(username, is_creator)
        
        print(f"\n✨ Nova is ready for {username}!")
        
        # Voice setup
        setup_choice = input("\n🎛️ Voice Setup:\n1. Auto-detect voice levels\n2. Calibrate microphone\n3. Use default settings\nChoice (1-3): ").strip()
        
        if setup_choice == "1":
            print("🎤 Auto-detecting optimal voice settings...")
            self.voice_threshold = 0.01  # Start with default
        elif setup_choice == "2":
            print("🎛️ Starting microphone calibration...")
            self.voice_threshold = calibrate_voice_detection()
            print(f"✅ Calibration complete! Using threshold: {self.voice_threshold:.6f}")
        else:
            print("📊 Using default voice settings")
            self.voice_threshold = 0.01
        
        # Recording mode
        mode_choice = input("\n🎙️ Recording Mode:\n1. Voice Wake Detection (Recommended)\n2. Fixed Duration (5 seconds)\n3. Continuous Conversation\nChoice (1-3): ").strip()
        
        if mode_choice == "2":
            self.use_voice_wake = False
            print("⏱️ Using fixed 5-second recording mode")
        elif mode_choice == "3":
            self.continuous_mode = True
            print("🔄 Continuous conversation mode enabled")
        else:
            self.use_voice_wake = True
            print("🎤 Voice wake detection enabled")
        
        print("\n" + "=" * 50)
        self._print_instructions(username, is_creator)
        
    def _print_instructions(self, username, is_creator):
        """Print usage instructions based on user type and mode"""
        print(f"👋 Welcome {username}!")
        
        if self.continuous_mode:
            print("🔄 CONTINUOUS MODE:")
            print("   • Nova will keep listening after each response")
            print("   • Just start speaking when you hear the listening prompt")
            print("   • Say 'exit', 'quit', or 'stop' to end session")
        elif self.use_voice_wake:
            print("🎤 VOICE WAKE MODE:")
            print("   • Just start speaking - Nova will detect your voice")
            print("   • Stop talking and Nova will process your request")
            print("   • Say 'exit', 'quit', or 'stop' to end session")
        else:
            print("⏱️ FIXED DURATION MODE:")
            print("   • You have 5 seconds to speak after the prompt")
            print("   • Say 'exit', 'quit', or 'stop' to end session")
        
        if is_creator:
            print("👑 CREATOR PRIVILEGES:")
            print("   • Full system control commands available")
            print("   • Memory management commands enabled")
            print("   • Advanced features unlocked")
        else:
            print("🔓 STANDARD ACCESS:")
            print("   • Basic voice commands available")
            print("   • Web search and YouTube access")
            print("   • Limited system commands")
        
        print("\n💡 TIPS:")
        print("   • Speak clearly and at normal volume")
        print("   • Wait for Nova to finish speaking before your next command")
        print("   • Try: 'What time is it?', 'Search for cats', 'Open YouTube'")
        print("=" * 50)
    
    async def voice_interaction_loop(self):
        """Main voice interaction loop"""
        interaction_count = 0
        
        while self.session_active:
            try:
                interaction_count += 1
                print(f"\n🎤 [{interaction_count}] Listening for your voice...")
                
                # Record audio based on mode
                if self.use_voice_wake:
                    # Use voice wake detection
                    nova_recorder.silence_timeout = 2.0
                    nova_recorder.min_recording_duration = 0.5
                    audio_file = record_audio("input.wav", use_voice_detection=True)
                else:
                    # Use fixed duration recording
                    audio_file = record_audio("input.wav", duration=5, use_voice_detection=False)
                
                # Check if recording was successful
                if not audio_file:
                    print("⚠️ No audio recorded. Please try again.")
                    continue
                
                # Transcribe the audio
                print("🧠 Processing your speech...")
                user_input = transcribe_audio(audio_file)
                
                if not user_input or user_input.strip() == "":
                    print("❌ Could not understand speech. Please try again.")
                    continue
                
                print(f"👤 You said: {user_input}")
                
                # Check for exit commands
                exit_commands = ["exit", "quit", "stop", "goodbye", "bye"]
                if any(cmd in user_input.lower() for cmd in exit_commands):
                    print("👋 Ending Nova session...")
                    await speak_text("Goodbye! It was great talking with you.")
                    self.session_active = False
                    break
                
                # Check for system commands
                if await self._handle_system_commands(user_input):
                    continue
                
                # Process with AI
                print("🤖 Nova is thinking...")
                response = query_ollama(user_input)
                
                if response:
                    print(f"🤖 Nova: {response}")
                    
                    # Speak the response
                    await speak_text(response)
                    
                    # In continuous mode, automatically continue listening
                    if self.continuous_mode:
                        print("🔄 Continuing conversation...")
                        continue
                else:
                    print("❌ Nova couldn't generate a response. Please try again.")
                    await speak_text("I'm sorry, I couldn't understand that. Could you please try again?")
                
            except KeyboardInterrupt:
                print("\n🛑 Session interrupted by user")
                self.session_active = False
                break
            except Exception as e:
                print(f"❌ Error in interaction loop: {e}")
                await speak_text("I encountered an error. Let me try again.")
                continue
    
    async def _handle_system_commands(self, user_input):
        """Handle system-level commands"""
        user_input_lower = user_input.lower()
        
        # Voice control commands
        if "adjust volume" in user_input_lower or "change volume" in user_input_lower:
            await speak_text("Volume adjustment feature coming soon!")
            return True
        
        if "calibrate microphone" in user_input_lower or "test microphone" in user_input_lower:
            print("🎛️ Starting microphone calibration...")
            new_threshold = calibrate_voice_detection()
            self.voice_threshold = new_threshold
            await speak_text(f"Microphone calibrated successfully!")
            return True
        
        if "switch mode" in user_input_lower or "change mode" in user_input_lower:
            await self._switch_recording_mode()
            return True
        
        if "help" in user_input_lower or "what can you do" in user_input_lower:
            await self._show_help()
            return True
        
        if "status" in user_input_lower or "system status" in user_input_lower:
            await self._show_status()
            return True
        
        return False
    
    async def _switch_recording_mode(self):
        """Switch between recording modes"""
        print("\n🔄 Switching recording mode...")
        await speak_text("Which recording mode would you like?")
        
        print("1. Voice Wake Detection")
        print("2. Fixed Duration")
        print("3. Continuous Conversation")
        
        # For voice interface, we'll cycle through modes
        if self.use_voice_wake and not self.continuous_mode:
            # Currently voice wake -> switch to fixed duration
            self.use_voice_wake = False
            self.continuous_mode = False
            mode_name = "Fixed Duration"
        elif not self.use_voice_wake and not self.continuous_mode:
            # Currently fixed -> switch to continuous
            self.use_voice_wake = True
            self.continuous_mode = True
            mode_name = "Continuous Conversation"
        else:
            # Currently continuous -> switch to voice wake
            self.use_voice_wake = True
            self.continuous_mode = False
            mode_name = "Voice Wake Detection"
        
        print(f"✅ Switched to {mode_name} mode")
        await speak_text(f"Now using {mode_name} mode")
    
    async def _show_help(self):
        """Show help information"""
        help_text = """Here's what I can help you with:
        - Answer questions and have conversations
        - Search the web for information
        - Control system functions if you have permissions
        - Voice commands like 'switch mode', 'calibrate microphone'
        - Say 'exit' or 'quit' to end our session
        """
        
        print("📚 NOVA HELP:")
        print(help_text)
        await speak_text("I can help with conversations, web searches, and system commands. Say exit to end our session.")
    
    async def _show_status(self):
        """Show current system status"""
        mode_name = "Continuous" if self.continuous_mode else ("Voice Wake" if self.use_voice_wake else "Fixed Duration")
        
        status_text = f"""
🔧 NOVA STATUS:
   • Recording Mode: {mode_name}
   • Voice Threshold: {self.voice_threshold:.6f}
   • Session Active: {self.session_active}
   • Interactions: Active
        """
        
        print(status_text)
        await speak_text(f"Currently using {mode_name} recording mode. System is running normally.")
    
    async def run(self):
        """Main run method"""
        try:
            await self.initialize()
            await self.voice_interaction_loop()
        except KeyboardInterrupt:
            print("\n🛑 Nova shutting down...")
        except Exception as e:
            print(f"❌ Fatal error: {e}")
        finally:
            print("👋 Nova session ended. Goodbye!")

# Main execution functions
async def main():
    """Main async function"""
    assistant = NovaVoiceAssistant()
    await assistant.run()

def run():
    """Synchronous wrapper to run the async main function"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Nova signing off!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    run()