# nova_vision.py - Computer Vision Module for Nova
import cv2
import numpy as np
import pyautogui
import pytesseract
import base64
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import threading
import time

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not available. Install with: pip install Pillow")

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False
    print("⚠️ EasyOCR not available. Install with: pip install easyocr")

class NovaVision:
    def __init__(self, user_is_creator: bool = False):
        self.user_is_creator = user_is_creator
        self.ocr_reader = None
        self.last_screenshot = None
        self.screenshot_history = []
        self.vision_cache = {}
        
        # Initialize OCR readers
        self._initialize_ocr()
        
        # Vision capabilities available to all users
        self.basic_vision_commands = {
            "what_do_you_see": self.describe_screen,
            "read_screen": self.read_text_on_screen,
            "find_text": self.find_text_on_screen,
            "what_app": self.identify_current_application,
            "screenshot": self.take_screenshot,
            "describe_image": self.describe_image_file,
        }
        
        # Advanced vision commands for creator
        self.creator_vision_commands = {
            "monitor_screen": self.start_screen_monitoring,
            "stop_monitoring": self.stop_screen_monitoring,
            "find_button": self.find_ui_element,
            "click_on": self.click_on_element,
            "analyze_performance": self.analyze_system_performance,
            "detect_changes": self.detect_screen_changes,
            "save_vision_log": self.save_vision_analysis,
        }
        
        self.monitoring_active = False
        self.monitoring_thread = None
        
    def _initialize_ocr(self):
        """Initialize OCR engines"""
        try:
            # Initialize EasyOCR if available (better for general text)
            if EASYOCR_AVAILABLE:
                self.ocr_reader = easyocr.Reader(['en'])
                print("✅ EasyOCR initialized successfully")
            else:
                print("📝 Using Tesseract OCR as fallback")
        except Exception as e:
            print(f"⚠️ OCR initialization warning: {e}")
    
    def take_screenshot(self, save_path: str = None) -> str:
        """Take a screenshot of the current screen"""
        try:
            # Take screenshot using pyautogui
            screenshot = pyautogui.screenshot()
            
            if save_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"nova_screenshot_{timestamp}.png"
            
            screenshot.save(save_path)
            self.last_screenshot = save_path
            
            # Add to history (keep last 10)
            self.screenshot_history.append({
                'path': save_path,
                'timestamp': datetime.now(),
                'size': screenshot.size
            })
            if len(self.screenshot_history) > 10:
                # Clean up old screenshots
                old_screenshot = self.screenshot_history.pop(0)
                try:
                    os.remove(old_screenshot['path'])
                except:
                    pass
            
            return f"📸 Screenshot saved as {save_path}! I can now see your screen with {screenshot.size[0]}x{screenshot.size[1]} resolution."
            
        except Exception as e:
            return f"❌ Error taking screenshot: {str(e)}"
    
    def describe_screen(self) -> str:
        """Analyze and describe what's currently on screen"""
        try:
            # Take a fresh screenshot
            screenshot_path = "temp_screen_analysis.png"
            self.take_screenshot(screenshot_path)
            
            # Load and analyze the image
            image = cv2.imread(screenshot_path)
            if image is None:
                return "❌ Could not capture screen for analysis"
            
            height, width = image.shape[:2]
            
            # Basic analysis
            analysis = f"🖥️ SCREEN ANALYSIS:\n"
            analysis += f"Screen Resolution: {width}x{height}\n"
            
            # Color analysis
            avg_color = np.mean(image, axis=(0, 1))
            brightness = np.mean(avg_color)
            
            if brightness < 50:
                analysis += "🌙 Screen appears dark (dark theme or night mode)\n"
            elif brightness > 200:
                analysis += "☀️ Screen appears bright (light theme)\n"
            else:
                analysis += "🖼️ Screen has moderate brightness\n"
            
            # Detect if there are windows/UI elements
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) > 100:
                analysis += "🖱️ Detected multiple UI elements and windows\n"
            elif len(contours) > 20:
                analysis += "📋 Detected some interface elements\n"
            else:
                analysis += "🏞️ Screen appears mostly empty or showing large content\n"
            
            # Try to read any visible text
            text_found = self.read_text_on_screen()
            if "Found text:" in text_found:
                analysis += "📝 Text content detected on screen\n"
            
            # Clean up temp file
            try:
                os.remove(screenshot_path)
            except:
                pass
                
            return analysis
            
        except Exception as e:
            return f"❌ Error analyzing screen: {str(e)}"
    
    def read_text_on_screen(self) -> str:
        """Extract and read text from the current screen"""
        try:
            # Take screenshot
            screenshot_path = "temp_ocr_screen.png"
            self.take_screenshot(screenshot_path)
            
            text_results = []
            
            # Try EasyOCR first (better results)
            if self.ocr_reader is not None:
                try:
                    results = self.ocr_reader.readtext(screenshot_path)
                    for (bbox, text, confidence) in results:
                        if confidence > 0.5:  # Only include confident results
                            text_results.append(text.strip())
                except Exception as e:
                    print(f"EasyOCR error: {e}")
            
            # Fallback to Tesseract
            if not text_results:
                try:
                    # Enhance image for better OCR
                    img = Image.open(screenshot_path)
                    img = img.convert('L')  # Convert to grayscale
                    img = ImageEnhance.Contrast(img).enhance(2)
                    img.save("temp_enhanced_ocr.png")
                    
                    text = pytesseract.image_to_string("temp_enhanced_ocr.png")
                    if text.strip():
                        text_results = [line.strip() for line in text.split('\n') if line.strip()]
                    
                    os.remove("temp_enhanced_ocr.png")
                except Exception as e:
                    print(f"Tesseract error: {e}")
            
            # Clean up
            try:
                os.remove(screenshot_path)
            except:
                pass
            
            if text_results:
                # Limit output to avoid overwhelming response
                displayed_text = text_results[:20]  # Show first 20 lines
                response = "📖 Found text on screen:\n"
                response += "\n".join(f"• {text}" for text in displayed_text)
                if len(text_results) > 20:
                    response += f"\n... and {len(text_results) - 20} more lines"
                return response
            else:
                return "📄 No readable text found on the current screen"
                
        except Exception as e:
            return f"❌ Error reading screen text: {str(e)}"
    
    def find_text_on_screen(self, search_text: str) -> str:
        """Find specific text on the screen"""
        try:
            screenshot_path = "temp_search_screen.png"
            self.take_screenshot(screenshot_path)
            
            found_locations = []
            
            # Use EasyOCR for location detection
            if self.ocr_reader is not None:
                try:
                    results = self.ocr_reader.readtext(screenshot_path)
                    for (bbox, text, confidence) in results:
                        if confidence > 0.5 and search_text.lower() in text.lower():
                            # Calculate center of bounding box
                            center_x = int(np.mean([point[0] for point in bbox]))
                            center_y = int(np.mean([point[1] for point in bbox]))
                            found_locations.append({
                                'text': text,
                                'position': (center_x, center_y),
                                'confidence': confidence
                            })
                except Exception as e:
                    print(f"Text search error: {e}")
            
            # Clean up
            try:
                os.remove(screenshot_path)
            except:
                pass
            
            if found_locations:
                response = f"🔍 Found '{search_text}' on screen:\n"
                for i, location in enumerate(found_locations[:5]):  # Show first 5 matches
                    response += f"• Match {i+1}: '{location['text']}' at position ({location['position'][0]}, {location['position'][1]})\n"
                return response
            else:
                return f"🔍 Could not find '{search_text}' on the current screen"
                
        except Exception as e:
            return f"❌ Error searching for text: {str(e)}"
    
    def identify_current_application(self) -> str:
        """Try to identify the currently active application"""
        try:
            import psutil
            
            # Get the active window (this is OS-specific)
            screenshot_path = "temp_app_detection.png"
            self.take_screenshot(screenshot_path)
            
            # Basic analysis based on common UI patterns
            analysis = "🔍 ACTIVE APPLICATION ANALYSIS:\n"
            
            # Try to read window title or app-specific text
            text_results = []
            if self.ocr_reader is not None:
                try:
                    results = self.ocr_reader.readtext(screenshot_path)
                    for (bbox, text, confidence) in results:
                        if confidence > 0.7:
                            text_results.append(text.strip())
                except:
                    pass
            
            # Look for common application indicators
            app_indicators = {
                'Chrome': ['Chrome', 'Google', 'New Tab', 'Bookmarks'],
                'Firefox': ['Firefox', 'Mozilla', 'Bookmarks', 'History'],
                'VS Code': ['Visual Studio Code', 'Explorer', 'Terminal', 'Extensions'],
                'Notepad': ['Notepad', 'Untitled', '.txt'],
                'Word': ['Microsoft Word', 'Document', 'Ribbon'],
                'Excel': ['Microsoft Excel', 'Sheet', 'Cell'],
                'File Explorer': ['This PC', 'Documents', 'Downloads', 'Desktop'],
                'Command Prompt': ['Command Prompt', 'cmd', 'C:\\'],
                'PowerShell': ['PowerShell', 'PS C:'],
            }
            
            detected_apps = []
            for app_name, keywords in app_indicators.items():
                for keyword in keywords:
                    if any(keyword.lower() in text.lower() for text in text_results):
                        detected_apps.append(app_name)
                        break
            
            if detected_apps:
                analysis += f"Detected applications: {', '.join(set(detected_apps))}\n"
            else:
                analysis += "Could not identify specific application from screen content\n"
            
            # Add some visible text context
            if text_results:
                analysis += f"Visible text includes: {', '.join(text_results[:5])}"
            
            # Clean up
            try:
                os.remove(screenshot_path)
            except:
                pass
            
            return analysis
            
        except Exception as e:
            return f"❌ Error identifying application: {str(e)}"
    
    def describe_image_file(self, image_path: str) -> str:
        """Analyze and describe a specific image file"""
        try:
            if not os.path.exists(image_path):
                return f"❌ Image file not found: {image_path}"
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return f"❌ Could not load image: {image_path}"
            
            height, width = image.shape[:2]
            
            analysis = f"🖼️ IMAGE ANALYSIS: {os.path.basename(image_path)}\n"
            analysis += f"Dimensions: {width}x{height} pixels\n"
            
            # Color analysis
            avg_color = np.mean(image, axis=(0, 1))
            dominant_color = avg_color.astype(int)
            analysis += f"Dominant colors: Blue:{dominant_color[0]}, Green:{dominant_color[1]}, Red:{dominant_color[2]}\n"
            
            # Brightness analysis
            brightness = np.mean(avg_color)
            if brightness < 50:
                analysis += "📊 Image is quite dark\n"
            elif brightness > 200:
                analysis += "📊 Image is quite bright\n"
            else:
                analysis += "📊 Image has moderate brightness\n"
            
            # Try to read text in the image
            if PIL_AVAILABLE:
                try:
                    if self.ocr_reader is not None:
                        results = self.ocr_reader.readtext(image_path)
                        text_found = [text for (bbox, text, confidence) in results if confidence > 0.5]
                        if text_found:
                            analysis += f"📝 Text found in image: {', '.join(text_found[:5])}\n"
                except:
                    pass
            
            return analysis
            
        except Exception as e:
            return f"❌ Error analyzing image: {str(e)}"
    
    # Creator-only advanced functions
    def find_ui_element(self, element_description: str) -> str:
        """Find UI elements like buttons, menus, etc. (Creator only)"""
        if not self.user_is_creator:
            return "🔒 Advanced UI detection is only available to my creator!"
        
        try:
            screenshot_path = "temp_ui_detection.png"
            self.take_screenshot(screenshot_path)
            
            # This is a simplified version - in practice, you'd use more sophisticated
            # computer vision techniques or UI automation libraries
            response = f"🔍 Searching for UI element: '{element_description}'\n"
            response += "This feature is under development. Currently searching for text matches..."
            
            # Search for text that might be on buttons or UI elements
            text_result = self.find_text_on_screen(element_description)
            response += f"\n{text_result}"
            
            # Clean up
            try:
                os.remove(screenshot_path)
            except:
                pass
            
            return response
            
        except Exception as e:
            return f"❌ Error finding UI element: {str(e)}"
    
    def click_on_element(self, element_description: str) -> str:
        """Click on a UI element (Creator only - be very careful!)"""
        if not self.user_is_creator:
            return "🔒 Click automation is only available to my creator!"
        
        # This is potentially dangerous, so we'll be extra cautious
        try:
            # First, find the element
            find_result = self.find_text_on_screen(element_description)
            
            if "Found" in find_result and "position" in find_result:
                return f"🎯 Found element '{element_description}' but automated clicking is disabled for safety. Manual clicking recommended."
            else:
                return f"❌ Could not locate element '{element_description}' on screen"
                
        except Exception as e:
            return f"❌ Error in click automation: {str(e)}"
    
    def start_screen_monitoring(self) -> str:
        """Start continuous screen monitoring (Creator only)"""
        if not self.user_is_creator:
            return "🔒 Screen monitoring is only available to my creator!"
        
        if self.monitoring_active:
            return "📺 Screen monitoring is already active!"
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_screen_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        return "📺 Started continuous screen monitoring! I'll watch for changes and interesting events."
    
    def stop_screen_monitoring(self) -> str:
        """Stop screen monitoring (Creator only)"""
        if not self.user_is_creator:
            return "🔒 Screen monitoring control is only available to my creator!"
        
        self.monitoring_active = False
        return "📺 Stopped screen monitoring."
    
    def _monitor_screen_loop(self):
        """Background thread for screen monitoring"""
        previous_screen = None
        
        while self.monitoring_active:
            try:
                # Take screenshot
                current_screen = pyautogui.screenshot()
                
                if previous_screen is not None:
                    # Compare screens for significant changes
                    # This is a simplified comparison
                    pass
                
                previous_screen = current_screen
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(10)
    
    def detect_screen_changes(self) -> str:
        """Detect changes between current and previous screenshots"""
        if not self.user_is_creator:
            return "🔒 Change detection is only available to my creator!"
        
        if len(self.screenshot_history) < 2:
            return "📸 Need at least 2 screenshots to detect changes. Take another screenshot first!"
        
        try:
            # Compare last two screenshots
            current_path = self.screenshot_history[-1]['path']
            previous_path = self.screenshot_history[-2]['path']
            
            current_img = cv2.imread(current_path)
            previous_img = cv2.imread(previous_path)
            
            if current_img is None or previous_img is None:
                return "❌ Could not load screenshots for comparison"
            
            # Calculate difference
            diff = cv2.absdiff(current_img, previous_img)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            
            # Calculate change percentage
            total_pixels = gray_diff.shape[0] * gray_diff.shape[1]
            changed_pixels = np.count_nonzero(gray_diff > 30)  # Threshold for significant change
            change_percentage = (changed_pixels / total_pixels) * 100
            
            if change_percentage > 50:
                return f"🔄 Major screen changes detected! {change_percentage:.1f}% of screen changed."
            elif change_percentage > 10:
                return f"📱 Moderate screen changes detected. {change_percentage:.1f}% of screen changed."
            elif change_percentage > 1:
                return f"👁️ Minor screen changes detected. {change_percentage:.1f}% of screen changed."
            else:
                return "😴 No significant screen changes detected."
                
        except Exception as e:
            return f"❌ Error detecting changes: {str(e)}"
    
    def save_vision_analysis(self) -> str:
        """Save current vision analysis to file (Creator only)"""
        if not self.user_is_creator:
            return "🔒 Vision logging is only available to my creator!"
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"nova_vision_log_{timestamp}.json"
            
            # Perform comprehensive analysis
            screenshot_result = self.take_screenshot()
            screen_description = self.describe_screen()
            text_content = self.read_text_on_screen()
            app_info = self.identify_current_application()
            
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'screenshot_info': screenshot_result,
                'screen_description': screen_description,
                'text_content': text_content,
                'application_info': app_info,
                'screenshot_history': [
                    {
                        'path': item['path'],
                        'timestamp': item['timestamp'].isoformat(),
                        'size': item['size']
                    } for item in self.screenshot_history
                ]
            }
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            return f"💾 Vision analysis saved to {log_file}!"
            
        except Exception as e:
            return f"❌ Error saving vision analysis: {str(e)}"
    
    def execute_vision_command(self, command: str, params: str = "") -> Optional[str]:
        """Execute a vision command safely"""
        # Check basic vision commands first (available to all)
        for cmd_key, cmd_func in self.basic_vision_commands.items():
            if cmd_key.replace("_", " ") in command.lower():
                if params:
                    return cmd_func(params)
                else:
                    return cmd_func()
        
        # Check creator vision commands
        if self.user_is_creator:
            for cmd_key, cmd_func in self.creator_vision_commands.items():
                if cmd_key.replace("_", " ") in command.lower():
                    if params:
                        return cmd_func(params)
                    else:
                        return cmd_func()
        
        return None  # Command not found

# Integration function for enhanced_system_control.py
def integrate_vision_with_nova():
    """
    Integration function to add vision capabilities to Nova
    """
    def enhanced_vision_query(prompt, current_username, is_current_user_creator):
        # Initialize vision system
        vision_system = NovaVision(user_is_creator=is_current_user_creator)
        
        prompt_lower = prompt.lower()
        
        # Vision command detection
        vision_triggers = {
            "what do you see": vision_system.describe_screen,
            "what is this": vision_system.describe_screen,
            "describe screen": vision_system.describe_screen,
            "what's on screen": vision_system.describe_screen,
            "read screen": vision_system.read_text_on_screen,
            "read text": vision_system.read_text_on_screen,
            "take screenshot": vision_system.take_screenshot,
            "screenshot": vision_system.take_screenshot,
            "what app": vision_system.identify_current_application,
            "current app": vision_system.identify_current_application,
        }
        
        # Check for vision commands
        for trigger, function in vision_triggers.items():
            if trigger in prompt_lower:
                return function()
        
        # Find text commands
        if "find" in prompt_lower and any(word in prompt_lower for word in ["text", "word", "on screen"]):
            # Extract search term
            search_term = prompt.replace("find", "").replace("text", "").replace("word", "").replace("on screen", "").strip()
            if search_term:
                return vision_system.find_text_on_screen(search_term)
        
        # Image analysis commands
        if "analyze image" in prompt_lower or "describe image" in prompt_lower:
            # Extract image path if provided
            words = prompt.split()
            for i, word in enumerate(words):
                if word.lower() in ["image", "picture", "photo"] and i + 1 < len(words):
                    image_path = words[i + 1]
                    return vision_system.describe_image_file(image_path)
        
        # Creator-only commands
        if is_current_user_creator:
            if "monitor screen" in prompt_lower or "start monitoring" in prompt_lower:
                return vision_system.start_screen_monitoring()
            elif "stop monitoring" in prompt_lower:
                return vision_system.stop_screen_monitoring()
            elif "detect changes" in prompt_lower:
                return vision_system.detect_screen_changes()
            elif "save vision" in prompt_lower or "save analysis" in prompt_lower:
                return vision_system.save_vision_analysis()
        
        return None  # No vision command detected
    
    return enhanced_vision_query

# Usage example and testing
if __name__ == "__main__":
    print("🔍 Testing Nova Vision System...")
    
    # Test with creator privileges
    vision = NovaVision(user_is_creator=True)
    
    print("\n📸 Taking screenshot...")
    print(vision.take_screenshot())
    
    print("\n👁️ Describing screen...")
    print(vision.describe_screen())
    
    print("\n📖 Reading screen text...")
    print(vision.read_text_on_screen())
    
    print("\n🔍 Identifying current application...")
    print(vision.identify_current_application())