"""
LUCIFER AI — Advanced PC Assistant
===================================
A voice-enabled, text-input AI assistant that automates PC tasks,
holds intelligent conversations, remembers context, and actually thinks.

Requirements:
    pip install spacy pyttsx3 psutil requests
    python -m spacy download en_core_web_sm

Usage:
    python lucifer.py
"""

import datetime
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from pathlib import Path

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    print("[!] spaCy not loaded. Install with: pip install spacy && python -m spacy download en_core_web_sm")
    nlp = None

try:
    import pyttsx3
    engine = pyttsx3.init()
    # Tune voice
    voices = engine.getProperty("voices")
    if len(voices) > 1:
        engine.setProperty("voice", voices[0].id)  # Change index for different voice
    engine.setProperty("rate", 175)
    engine.setProperty("volume", 1.0)
except Exception:
    engine = None
    print("[!] pyttsx3 not available. Voice output disabled.")

try:
    import psutil
except ImportError:
    psutil = None


# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
ASSISTANT_NAME = "Lucifer"
MEMORY_FILE = Path.home() / ".lucifer_memory.json"
AUTH_FILE = Path.home() / ".lucifer_auth.json"
MAX_CONVERSATION_HISTORY = 50
MAX_MEMORY_ITEMS = 200
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION = 300  # 5 minutes in seconds


# ─────────────────────────────────────────────
# SECURITY & AUTHENTICATION
# ─────────────────────────────────────────────
class SecurityAuth:
    """PIN-based authentication system with security features."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.auth_data = {"pin_hash": None, "username": None, "failed_attempts": 0, "locked_until": None}
        self._load()

    def _load(self):
        """Load authentication data from file."""
        if self.filepath.exists():
            try:
                data = json.loads(self.filepath.read_text())
                self.auth_data = data
            except (json.JSONDecodeError, KeyError):
                self._save()

    def _save(self):
        """Save authentication data securely."""
        try:
            self.filepath.write_text(json.dumps(self.auth_data, indent=2))
            # Restrict file permissions to owner only
            os.chmod(self.filepath, 0o600)
        except Exception as e:
            print(f"  [!] Could not save auth data: {e}")

    def _hash_pin(self, pin: str) -> str:
        """Hash a PIN using SHA-256."""
        return hashlib.sha256(pin.encode()).hexdigest()

    def is_locked(self) -> bool:
        """Check if the system is locked due to failed attempts."""
        if self.auth_data["locked_until"]:
            if time.time() < self.auth_data["locked_until"]:
                remaining = int(self.auth_data["locked_until"] - time.time())
                print(f"  [!] System locked. Try again in {remaining} seconds.")
                return True
            else:
                # Unlock the system
                self.auth_data["locked_until"] = None
                self.auth_data["failed_attempts"] = 0
                self._save()
                return False
        return False

    def is_registered(self) -> bool:
        """Check if PIN is registered."""
        return self.auth_data["pin_hash"] is not None

    def register_pin(self, pin: str, username: str = "User") -> bool:
        """Register a new PIN (first-time setup)."""
        if not pin.isdigit() or len(pin) < 4:
            print("  [!] PIN must be at least 4 digits.")
            return False

        self.auth_data["pin_hash"] = self._hash_pin(pin)
        self.auth_data["username"] = username
        self.auth_data["failed_attempts"] = 0
        self.auth_data["locked_until"] = None
        self._save()
        return True

    def verify_pin(self, pin: str) -> bool:
        """Verify the PIN."""
        if self.is_locked():
            return False

        if not self.is_registered():
            print("  [!] No PIN registered. Please set up first.")
            return False

        if self._hash_pin(pin) == self.auth_data["pin_hash"]:
            # Reset failed attempts on successful login
            self.auth_data["failed_attempts"] = 0
            self.auth_data["locked_until"] = None
            self._save()
            return True
        else:
            # Increment failed attempts
            self.auth_data["failed_attempts"] += 1
            remaining = MAX_FAILED_ATTEMPTS - self.auth_data["failed_attempts"]

            if self.auth_data["failed_attempts"] >= MAX_FAILED_ATTEMPTS:
                self.auth_data["locked_until"] = time.time() + LOCKOUT_DURATION
                self._save()
                print(f"  [!] Too many failed attempts. System locked for 5 minutes.")
                return False
            else:
                print(f"  [!] Incorrect PIN. {remaining} attempts remaining.")
                self._save()
                return False

    def authenticate(self) -> bool:
        """Authenticate the user by PIN."""
        if not self.is_registered():
            print(f"\n  [{ASSISTANT_NAME}]: First time setup! Please create a PIN.")
            print("  [*] PIN must be at least 4 digits for security.")
            while True:
                pin = input("  Enter your PIN: ").strip()
                confirm_pin = input("  Confirm PIN: ").strip()

                if pin != confirm_pin:
                    print("  [!] PINs don't match. Try again.")
                    continue

                username = input("  Enter your name (or press Enter for 'User'): ").strip() or "User"

                if self.register_pin(pin, username):
                    print(f"  [{ASSISTANT_NAME}]: PIN registered successfully. Welcome, {username}.")
                    return True
                else:
                    print("  [!] Invalid PIN. Try again.")
        else:
            # Existing user login
            username = self.auth_data.get("username", "User")
            attempts = 0
            while attempts < 3:
                pin = input(f"  [{ASSISTANT_NAME}]: Please enter your PIN: ").strip()
                if self.verify_pin(pin):
                    print(f"  [{ASSISTANT_NAME}]: Welcome back, {username}!")
                    return True
                attempts += 1

            if self.is_locked():
                return False
            return False


# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
ASSISTANT_NAME = "Lucifer"
MEMORY_FILE = Path.home() / ".lucifer_memory.json"
AUTH_FILE = Path.home() / ".lucifer_auth.json"
MAX_CONVERSATION_HISTORY = 50
MAX_MEMORY_ITEMS = 200
MAX_FAILED_ATTEMPTS = 3
LOCKOUT_DURATION = 300  # 5 minutes in seconds


# ─────────────────────────────────────────────
# VOICE OUTPUT
# ─────────────────────────────────────────────
_speak_lock = threading.Lock()

def speak(text: str):
    """Print and speak the response."""
    print(f"\n  [{ASSISTANT_NAME}]: {text}")
    if engine:
        with _speak_lock:
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception:
                pass  # Fail silently if audio device busy


def listen() -> str:
    """Get typed input from user."""
    try:
        command = input(f"\n  You: ").strip()
        return command
    except (KeyboardInterrupt, EOFError):
        return "exit"


# ─────────────────────────────────────────────
# PERSISTENT MEMORY
# ─────────────────────────────────────────────
class Memory:
    """Persistent memory that survives across sessions."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.facts: list[dict] = []        # Things user asked to remember
        self.preferences: dict = {}         # Learned preferences
        self.history: deque = deque(maxlen=MAX_CONVERSATION_HISTORY)
        self._load()

    def _load(self):
        if self.filepath.exists():
            try:
                data = json.loads(self.filepath.read_text())
                self.facts = data.get("facts", [])
                self.preferences = data.get("preferences", {})
            except (json.JSONDecodeError, KeyError, OSError):
                # Reset to empty if corrupted
                self.facts = []
                self.preferences = {}

    def save(self):
        data = {
            "facts": self.facts[-MAX_MEMORY_ITEMS:],
            "preferences": self.preferences,
        }
        try:
            self.filepath.write_text(json.dumps(data, indent=2))
        except Exception as e:
            print(f"  [!] Could not save memory: {e}")

    def remember(self, text: str, category: str = "general"):
        entry = {
            "text": text,
            "category": category,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.facts.append(entry)
        self.save()

    def recall(self, query: str = "", n: int = 5) -> list[dict]:
        if not query:
            return self.facts[-n:]
        query_lower = query.lower()
        matches = [f for f in self.facts if query_lower in f["text"].lower()]
        return matches[-n:] if matches else self.facts[-n:]

    def forget(self, keyword: str) -> int:
        before = len(self.facts)
        self.facts = [f for f in self.facts if keyword.lower() not in f["text"].lower()]
        removed = before - len(self.facts)
        self.save()
        return removed

    def set_preference(self, key: str, value: str):
        self.preferences[key] = value
        self.save()

    def add_to_history(self, role: str, text: str):
        self.history.append({
            "role": role,
            "text": text,
            "time": datetime.datetime.now().isoformat()
        })


# ─────────────────────────────────────────────
# NLP ENGINE
# ─────────────────────────────────────────────
class NLPEngine:
    """Enhanced intent detection and entity extraction."""

    # Intent patterns: (intent_name, keywords, priority)
    INTENT_PATTERNS = [
        ("exit",        ["exit", "quit", "bye", "goodbye", "stop", "shut down", "close yourself"], 100),
        ("time",        ["time", "clock", "what time"], 90),
        ("date",        ["date", "today", "day is it", "what day"], 90),
        ("weather",     ["weather", "temperature", "forecast", "rain", "sunny"], 85),
        ("system_info", ["cpu", "ram", "memory usage", "disk", "battery", "system info", "system status"], 85),
        ("open_app",    ["open", "launch", "start", "run"], 70),
        ("close_app",   ["close", "kill", "terminate", "end process", "stop process"], 70),
        ("search",      ["search", "google", "look up", "find online", "search for"], 75),
        ("youtube",     ["play", "youtube", "video"], 72),
        ("remember",    ["remember", "save this", "note this", "store this", "keep in mind", "don't forget"], 80),
        ("recall",      ["recall", "what did i", "do you remember", "what do you know", "my notes", "my memories"], 80),
        ("forget",      ["forget", "delete memory", "remove memory", "clear memory"], 80),
        ("screenshot",  ["screenshot", "screen capture", "capture screen"], 85),
        ("list_files",  ["list files", "show files", "what's in folder", "directory", "ls"], 75),
        ("create_file", ["create file", "make file", "new file", "write file", "touch"], 75),
        ("calculate",   ["calculate", "math", "compute", "what is", "how much is", "solve"], 60),
        ("timer",       ["timer", "remind me in", "set timer", "alarm", "countdown"], 80),
        ("joke",        ["joke", "funny", "make me laugh", "humor"], 70),
        ("help",        ["help", "what can you do", "commands", "abilities", "features"], 90),
        ("preference",  ["my name is", "call me", "i prefer", "i like", "my favorite"], 65),
    ]

    def __init__(self):
        pass

    def detect_intent(self, text: str) -> tuple[str, float]:
        """Detect intent with confidence score."""
        text_lower = text.lower()
        best_intent = "chat"
        best_score = 0

        for intent, keywords, priority in self.INTENT_PATTERNS:
            for kw in keywords:
                if kw in text_lower:
                    score = priority + (len(kw) / len(text_lower)) * 10
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        return best_intent, best_score

    def extract_entities(self, text: str) -> dict:
        """Extract named entities, nouns, verbs, and adjectives."""
        result = {"entities": [], "nouns": [], "verbs": [], "adjectives": [], "numbers": []}
        if nlp:
            doc = nlp(text)
            result["entities"] = [(ent.text, ent.label_) for ent in doc.ents]
            result["nouns"] = [t.text for t in doc if t.pos_ == "NOUN"]
            result["verbs"] = [t.lemma_ for t in doc if t.pos_ == "VERB"]
            result["adjectives"] = [t.text for t in doc if t.pos_ == "ADJ"]
            result["numbers"] = [t.text for t in doc if t.like_num]
        return result

    def extract_after_keyword(self, text: str, keywords: list[str]) -> str:
        """Extract text after a keyword. e.g., 'open notepad' -> 'notepad'"""
        text_lower = text.lower()
        for kw in keywords:
            idx = text_lower.find(kw)
            if idx != -1:
                return text[idx + len(kw):].strip()
        return ""


# ─────────────────────────────────────────────
# SMART CHAT ENGINE
# ─────────────────────────────────────────────
class ChatEngine:
    """Context-aware conversational responses."""

    GREETINGS = ["hello", "hi", "hey", "greetings", "yo", "sup", "what's up", "howdy", "good morning", "good evening"]
    GREETING_RESPONSES = [
        "Hey there! What can I do for you?",
        "Hello! Ready to help.",
        "Hey! What's on your mind?",
        "Hi! I'm all ears.",
    ]

    FEELINGS_POSITIVE = ["good", "great", "amazing", "fantastic", "awesome", "happy", "wonderful", "excellent"]
    FEELINGS_NEGATIVE = ["bad", "sad", "terrible", "awful", "tired", "stressed", "angry", "upset", "bored"]

    THANKS = ["thank", "thanks", "thx", "appreciate"]
    THANKS_RESPONSES = [
        "You're welcome! Anything else?",
        "Happy to help!",
        "No problem at all.",
        "Anytime!",
    ]

    def __init__(self, memory: Memory):
        self.memory = memory
        self._response_counter = 0

    def respond(self, text: str, entities: dict) -> str:
        text_lower = text.lower().strip()

        # Check greetings
        if any(g in text_lower for g in self.GREETINGS) and len(text_lower.split()) <= 4:
            name = self.memory.preferences.get("name", "")
            greeting = self._cycle(self.GREETING_RESPONSES)
            return f"{greeting} {name}".strip() if name else greeting

        # Check thanks
        if any(t in text_lower for t in self.THANKS):
            return self._cycle(self.THANKS_RESPONSES)

        # Check "how are you"
        if "how are you" in text_lower or "how do you feel" in text_lower:
            return "I'm running smoothly! All systems operational. How about you?"

        # Check feelings
        if any(f in text_lower for f in self.FEELINGS_POSITIVE):
            return "That's great to hear! What can I help you with?"
        if any(f in text_lower for f in self.FEELINGS_NEGATIVE):
            return "I'm sorry to hear that. Let me know if there's anything I can do to help."

        # Who are you?
        if "who are you" in text_lower or "what are you" in text_lower:
            return (f"I'm {ASSISTANT_NAME}, your AI assistant. I can automate tasks on your PC, "
                    "remember things, search the web, manage files, monitor your system, and chat with you.")

        # Contextual response using NLP
        if entities.get("entities"):
            ent_text = ", ".join(f"{e[0]} ({e[1]})" for e in entities["entities"])
            return f"Interesting — you mentioned {ent_text}. Can you tell me more about what you need?"

        if entities.get("verbs"):
            verb = entities["verbs"][0]
            return f"It sounds like you want to {verb} something. Could you be more specific?"

        if entities.get("nouns"):
            noun = entities["nouns"][0]
            return f"You mentioned '{noun}'. What would you like me to do with that?"

        # Fallback
        fallbacks = [
            "I'm not sure I understand. Try saying 'help' to see what I can do.",
            "Could you rephrase that? Or type 'help' for a list of commands.",
            "Hmm, I didn't quite get that. What would you like me to do?",
            "I want to help — can you give me a bit more detail?",
        ]
        return self._cycle(fallbacks)

    def _cycle(self, options: list[str]) -> str:
        self._response_counter += 1
        return options[self._response_counter % len(options)]


# ─────────────────────────────────────────────
# SYSTEM TOOLS
# ─────────────────────────────────────────────
class SystemTools:
    """PC automation and system utilities."""

    APP_MAP = {
        "notepad":    {"win": "notepad", "linux": "gedit", "darwin": "open -a TextEdit"},
        "calculator": {"win": "calc", "linux": "gnome-calculator", "darwin": "open -a Calculator"},
        "browser":    {"win": "start chrome", "linux": "xdg-open https://google.com", "darwin": "open -a 'Google Chrome'"},
        "terminal":   {"win": "start cmd", "linux": "gnome-terminal", "darwin": "open -a Terminal"},
        "explorer":   {"win": "explorer", "linux": "nautilus", "darwin": "open ."},
        "file manager": {"win": "explorer", "linux": "nautilus", "darwin": "open ."},
        "settings":   {"win": "start ms-settings:", "linux": "gnome-control-center", "darwin": "open -a 'System Preferences'"},
        "paint":      {"win": "mspaint", "linux": "gimp", "darwin": "open -a Preview"},
        "word":       {"win": "start winword", "linux": "libreoffice --writer", "darwin": "open -a 'Microsoft Word'"},
        "excel":      {"win": "start excel", "linux": "libreoffice --calc", "darwin": "open -a 'Microsoft Excel'"},
        "vscode":     {"win": "code", "linux": "code", "darwin": "code"},
        "spotify":    {"win": "start spotify:", "linux": "spotify", "darwin": "open -a Spotify"},
        "discord":    {"win": "start discord:", "linux": "discord", "darwin": "open -a Discord"},
    }

    WEBSITES = {
        "youtube":    "https://youtube.com",
        "google":     "https://google.com",
        "github":     "https://github.com",
        "reddit":     "https://reddit.com",
        "twitter":    "https://twitter.com",
        "x":          "https://twitter.com",
        "chatgpt":    "https://chat.openai.com",
        "gmail":      "https://mail.google.com",
        "drive":      "https://drive.google.com",
        "maps":       "https://maps.google.com",
        "stackoverflow": "https://stackoverflow.com",
        "netflix":    "https://netflix.com",
        "amazon":     "https://amazon.com",
        "wikipedia":  "https://wikipedia.org",
        "linkedin":   "https://linkedin.com",
        "instagram":  "https://instagram.com",
        "facebook":   "https://facebook.com",
        "whatsapp":   "https://web.whatsapp.com",
    }

    def __init__(self):
        self.os_type = platform.system().lower()

    def get_system_info(self) -> str:
        info = [f"OS: {platform.system()} {platform.release()}"]
        info.append(f"Machine: {platform.machine()}")
        info.append(f"Processor: {platform.processor() or 'Unknown'}")

        if psutil:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            info.append(f"CPU Usage: {cpu}%")
            info.append(f"RAM: {ram.percent}% used ({ram.used // (1024**3)}GB / {ram.total // (1024**3)}GB)")
            info.append(f"Disk: {disk.percent}% used ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)")

            battery = psutil.sensors_battery()
            if battery:
                plug = "plugged in" if battery.power_plugged else "on battery"
                info.append(f"Battery: {battery.percent}% ({plug})")
        else:
            info.append("Install 'psutil' for detailed system stats.")

        return " | ".join(info)

    def open_app(self, app_name: str) -> str:
        app_lower = app_name.lower().strip()

        # Check websites first
        for site, url in self.WEBSITES.items():
            if site in app_lower:
                webbrowser.open(url)
                return f"Opening {site.title()} in your browser."

        # Check known apps
        for app, commands in self.APP_MAP.items():
            if app in app_lower:
                cmd = commands.get(self.os_type, commands.get("win"))
                try:
                    if self.os_type == "win":
                        os.system(f'start "" {cmd}' if not cmd.startswith("start") else cmd)
                    else:
                        subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return f"Launching {app.title()}."
                except Exception as e:
                    return f"Couldn't open {app}: {e}"

        # Try opening as a URL
        if "." in app_lower:
            url = app_lower if app_lower.startswith("http") else f"https://{app_lower}"
            webbrowser.open(url)
            return f"Opening {url} in your browser."

        # Last resort: try running it directly
        try:
            if self.os_type == "win":
                subprocess.Popen([app_lower], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=False)
            else:
                subprocess.Popen([app_lower], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return f"Trying to open {app_name}..."
        except Exception:
            return f"I don't know how to open '{app_name}'. Try the full app name or a website URL."

    def close_app(self, app_name: str) -> str:
        app_lower = app_name.lower().strip()
        try:
            if self.os_type == "win":
                result = subprocess.run(["taskkill", "/im", f"{app_lower}.exe", "/f"], 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(["pkill", "-f", app_lower], 
                                      capture_output=True, text=True)
            return f"Attempting to close {app_name}."
        except Exception as e:
            return f"Couldn't close {app_name}: {e}"

    def web_search(self, query: str) -> str:
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
        return f"Searching Google for: {query}"

    def youtube_search(self, query: str) -> str:
        import urllib.parse
        encoded_query = urllib.parse.quote(query)
        webbrowser.open(f"https://www.youtube.com/results?search_query={encoded_query}")
        return f"Searching YouTube for: {query}"

    def list_files(self, path: str = ".") -> str:
        try:
            target = Path(path).expanduser().resolve()
            if not target.exists():
                return f"Path '{path}' does not exist."
            items = sorted(target.iterdir())
            dirs = [f"  [DIR]  {i.name}" for i in items if i.is_dir()]
            files = [f"  [FILE] {i.name} ({i.stat().st_size // 1024} KB)" for i in items if i.is_file()]
            result = f"Contents of {target}:\n" + "\n".join(dirs + files)
            return result if (dirs or files) else f"{target} is empty."
        except PermissionError:
            return "Permission denied for that directory."
        except Exception as e:
            return f"Error listing files: {e}"

    def create_file(self, filename: str, content: str = "") -> str:
        try:
            path = Path(filename).expanduser().resolve()
            path.write_text(content)
            return f"Created file: {path}"
        except Exception as e:
            return f"Error creating file: {e}"

    def take_screenshot(self) -> str:
        try:
            from PIL import ImageGrab
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = Path.home() / "Desktop" / f"screenshot_{timestamp}.png"
            img = ImageGrab.grab()
            img.save(filename)
            return f"Screenshot saved to {filename}"
        except ImportError:
            return "Screenshot requires the Pillow library. Install with: pip install Pillow"
        except Exception as e:
            return f"Could not take screenshot: {e}"


# ─────────────────────────────────────────────
# CALCULATOR
# ─────────────────────────────────────────────
def safe_calculate(expression: str) -> str:
    """Evaluate a math expression safely."""
    # Clean the expression
    expr = expression.lower().strip()
    expr = expr.replace("what is", "").replace("calculate", "").replace("compute", "")
    expr = expr.replace("how much is", "").replace("solve", "").replace("math", "")
    expr = expr.replace("x", "*").replace("×", "*").replace("÷", "/")
    expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*")
    expr = expr.replace("divided by", "/").replace("power", "**").replace("to the", "**")
    expr = expr.replace("squared", "**2").replace("cubed", "**3")
    expr = expr.strip()

    if not expr:
        return "Give me a math expression to calculate, like '25 * 4 + 10'."

    # Only allow safe characters
    allowed = set("0123456789.+-*/() %")
    if not all(c in allowed for c in expr.replace("**", "")):
        return f"I can only do numeric math. Try something like '15 * 7 + 3'."

    try:
        result = eval(expr, {"__builtins__": {}}, {})
        if isinstance(result, float):
            result = round(result, 6)
        return f"{expr} = {result}"
    except ZeroDivisionError:
        return "Can't divide by zero!"
    except Exception:
        return f"Couldn't evaluate '{expr}'. Try a simpler expression."


# ─────────────────────────────────────────────
# TIMER
# ─────────────────────────────────────────────
def set_timer(seconds: int, message: str = "Time's up!"):
    """Run a background timer."""
    def _timer():
        time.sleep(seconds)
        speak(f"Timer alert: {message}")
    t = threading.Thread(target=_timer, daemon=True)
    t.start()


# ─────────────────────────────────────────────
# JOKES
# ─────────────────────────────────────────────
JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs.",
    "I told my computer I needed a break. Now it won't stop sending me vacation ads.",
    "Why was the computer cold? It left its Windows open.",
    "What's a computer's favorite snack? Microchips.",
    "Why did the developer go broke? Because he used up all his cache.",
    "There are only 10 types of people in the world: those who understand binary and those who don't.",
    "A SQL query walks into a bar, sees two tables, and asks: Can I JOIN you?",
    "Why do Java developers wear glasses? Because they can't C#.",
]
_joke_idx = 0


# ─────────────────────────────────────────────
# MAIN BRAIN
# ─────────────────────────────────────────────
class LuciferAI:
    """The core AI brain that orchestrates everything."""

    def __init__(self):
        self.auth = SecurityAuth(AUTH_FILE)
        self.memory = Memory(MEMORY_FILE)
        self.nlp_engine = NLPEngine()
        self.chat = ChatEngine(self.memory)
        self.tools = SystemTools()

    def process(self, user_input: str) -> str:
        if not user_input.strip():
            return ""

        self.memory.add_to_history("user", user_input)
        intent, confidence = self.nlp_engine.detect_intent(user_input)
        entities = self.nlp_engine.extract_entities(user_input)

        response = self._handle_intent(intent, user_input, entities)

        self.memory.add_to_history("assistant", response)
        return response

    def _handle_intent(self, intent: str, text: str, entities: dict) -> str:
        text_lower = text.lower()

        # ── EXIT ──
        if intent == "exit":
            self.memory.save()
            speak("Goodbye! See you next time.")
            sys.exit(0)

        # ── TIME ──
        if intent == "time":
            now = datetime.datetime.now()
            return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."

        # ── DATE ──
        if intent == "date":
            now = datetime.datetime.now()
            return f"Today is {now.strftime('%A, %B %d, %Y')}."

        # ── SYSTEM INFO ──
        if intent == "system_info":
            return self.tools.get_system_info()

        # ── OPEN APP/WEBSITE ──
        if intent == "open_app":
            target = self.nlp_engine.extract_after_keyword(text, ["open", "launch", "start", "run"])
            if not target:
                return "What would you like me to open?"
            return self.tools.open_app(target)

        # ── CLOSE APP ──
        if intent == "close_app":
            target = self.nlp_engine.extract_after_keyword(text, ["close", "kill", "terminate", "end", "stop"])
            if not target:
                return "What app should I close?"
            return self.tools.close_app(target)

        # ── SEARCH ──
        if intent == "search":
            query = self.nlp_engine.extract_after_keyword(text, ["search for", "search", "google", "look up", "find online"])
            if not query:
                speak("What should I search for?")
                query = listen()
            if query:
                return self.tools.web_search(query)
            return "I didn't catch the search query."

        # ── YOUTUBE ──
        if intent == "youtube":
            query = self.nlp_engine.extract_after_keyword(text, ["play", "youtube"])
            if "open youtube" in text_lower or text_lower.strip() == "youtube":
                webbrowser.open("https://youtube.com")
                return "Opening YouTube."
            if not query:
                speak("What do you want to watch?")
                query = listen()
            if query:
                return self.tools.youtube_search(query)
            return "I didn't catch what you wanted to watch."

        # ── REMEMBER ──
        if intent == "remember":
            fact = self.nlp_engine.extract_after_keyword(text, ["remember that", "remember", "note that", "note this", "save this"])
            if not fact:
                fact = text
            self.memory.remember(fact)
            return f"Got it — I'll remember that."

        # ── RECALL ──
        if intent == "recall":
            query = self.nlp_engine.extract_after_keyword(text, ["recall", "remember about", "know about"])
            facts = self.memory.recall(query, n=5)
            if facts:
                items = "\n".join(f"  • {f['text']}" for f in facts)
                return f"Here's what I remember:\n{items}"
            return "I don't have anything stored in memory yet. Tell me to remember something!"

        # ── FORGET ──
        if intent == "forget":
            keyword = self.nlp_engine.extract_after_keyword(text, ["forget", "delete", "remove", "clear"])
            if keyword:
                count = self.memory.forget(keyword)
                return f"Done — removed {count} memory entries matching '{keyword}'."
            return "What should I forget? Give me a keyword."

        # ── SCREENSHOT ──
        if intent == "screenshot":
            return self.tools.take_screenshot()

        # ── LIST FILES ──
        if intent == "list_files":
            path = self.nlp_engine.extract_after_keyword(text, ["files in", "in folder", "directory", "list files", "show files"])
            return self.tools.list_files(path if path else ".")

        # ── CREATE FILE ──
        if intent == "create_file":
            name = self.nlp_engine.extract_after_keyword(text, ["create file", "make file", "new file", "write file", "touch"])
            if not name:
                speak("What should I name the file?")
                name = listen()
            if name:
                return self.tools.create_file(name.strip())
            return "I need a filename."

        # ── CALCULATE ──
        if intent == "calculate":
            return safe_calculate(text)

        # ── TIMER ──
        if intent == "timer":
            # Try to extract number of seconds/minutes
            nums = re.findall(r"(\d+)", text)
            if nums:
                seconds = int(nums[0])
                if "minute" in text_lower:
                    seconds *= 60
                elif "hour" in text_lower:
                    seconds *= 3600
                set_timer(seconds)
                unit = "seconds"
                display = seconds
                if seconds >= 3600:
                    unit = "hours"
                    display = seconds // 3600
                elif seconds >= 60:
                    unit = "minutes"
                    display = seconds // 60
                return f"Timer set for {display} {unit}. I'll alert you when it's done."
            return "How many seconds or minutes? e.g., 'set timer 5 minutes'."

        # ── JOKE ──
        if intent == "joke":
            global _joke_idx
            joke = JOKES[_joke_idx % len(JOKES)]
            _joke_idx += 1
            return joke

        # ── HELP ──
        if intent == "help":
            return (
                f"Here's what I can do:\n"
                f"  • Open apps & websites  — 'open youtube', 'open notepad', 'open spotify'\n"
                f"  • Close apps             — 'close notepad'\n"
                f"  • Search the web         — 'search Python tutorials'\n"
                f"  • YouTube search         — 'play lofi music'\n"
                f"  • Tell time & date       — 'what time is it', 'what's today's date'\n"
                f"  • System status          — 'cpu usage', 'system info', 'battery'\n"
                f"  • Math                   — 'calculate 15 * 7 + 3'\n"
                f"  • Remember things        — 'remember my meeting is at 3pm'\n"
                f"  • Recall memories        — 'recall', 'what do you remember'\n"
                f"  • Forget things          — 'forget meeting'\n"
                f"  • Set timers             — 'set timer 5 minutes'\n"
                f"  • Take screenshots       — 'take a screenshot'\n"
                f"  • List & create files    — 'list files in Desktop', 'create file notes.txt'\n"
                f"  • Tell jokes             — 'tell me a joke'\n"
                f"  • Chat                   — just talk to me!\n"
                f"\n  Type 'exit' to quit."
            )

        # ── PREFERENCES ──
        if intent == "preference":
            if "my name is" in text_lower or "call me" in text_lower:
                name = self.nlp_engine.extract_after_keyword(text, ["my name is", "call me"])
                if name:
                    self.memory.set_preference("name", name.strip().title())
                    return f"Nice to meet you, {name.strip().title()}! I'll remember your name."

        # ── CHAT (fallback) ──
        return self.chat.respond(text, entities)

    def run(self):
        """Main loop."""
        # Authenticate user before starting
        if not self.auth.authenticate():
            speak("Authentication failed. Exiting.")
            sys.exit(1)

        name = self.memory.preferences.get("name", "")
        greeting = f"Welcome back, {name}!" if name else "Lucifer initialized. How can I help you?"
        speak(greeting)
        speak("Say 'Lucifer' to wake me up, or just start typing.")

        while True:
            command = listen()
            if not command:
                continue
            
            # Check for wake word
            if command.lower().strip() == "lucifer":
                speak("I'm awake. What can I help you with?")
                continue
            
            response = self.process(command)
            if response:
                speak(response)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        ai = LuciferAI()
        ai.run()
    except KeyboardInterrupt:
        print(f"\n  [{ASSISTANT_NAME}]: Shutting down. Goodbye!")
