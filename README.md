# Lucifer AI - Advanced PC Assistant

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Security](https://img.shields.io/badge/Security-Audited-red.svg)

A voice-enabled, text-input AI assistant that automates PC tasks, holds intelligent conversations, remembers context, and actually thinks. Built with security in mind.

## ✨ Features

### 🤖 AI Capabilities
- **Natural Language Processing**: Powered by spaCy for intelligent intent detection
- **Context Awareness**: Remembers conversations and user preferences
- **Voice Interface**: Text-to-speech output (when TTS is available)
- **Memory System**: Persistent storage of facts and preferences

### 🛠️ System Automation
- **App Management**: Launch and close applications
- **Web Integration**: Open websites and perform searches
- **File Operations**: Create, list, and manage files
- **System Monitoring**: CPU, RAM, disk usage, and battery status
- **Screenshot Capture**: Take and save screenshots

### 🔧 Utilities
- **Calculator**: Safe mathematical expression evaluation
- **Timer System**: Set countdown timers with notifications
- **Joke Generator**: Built-in humor for entertainment
- **Help System**: Comprehensive command reference

## 🛡️ Security Features

- **Command Injection Protection**: Uses subprocess with argument lists
- **Path Traversal Prevention**: File paths are normalized and validated
- **Code Execution Safeguards**: Restricted eval environment
- **Input Sanitization**: URL encoding for web requests
- **Memory Safety**: Robust error handling for data persistence

## 📋 Requirements

- Python 3.8+
- Dependencies: `spacy`, `pyttsx3`, `psutil`, `Pillow`
- Optional: eSpeak-ng (for voice output on Linux)

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/mickey45/lucifer.git
   cd lucifer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

3. **Run the assistant:**
   ```bash
   python chatbot.py
   ```

## 💻 Usage

### Basic Commands
- `help` - Show all available commands
- `exit` - Quit the assistant
- `what time is it` - Get current time and date
- `system info` - Display system statistics

### Examples
```
You: open youtube
Lucifer: Opening YouTube in your browser.

You: calculate 15 * 7 + 3
Lucifer: 15 * 7 + 3 = 108

You: remember my meeting is at 3pm
Lucifer: Got it — I'll remember that.

You: set timer 5 minutes
Lucifer: Timer set for 5 minutes. I'll alert you when it's done.
```

## 🧪 Security Testing

Run the security test suite to verify protections:

```bash
python security_test.py
```

This tests for:
- Command injection vulnerabilities
- Path traversal attacks
- Code execution exploits
- XSS prevention

## 📁 Project Structure

```
lucifer/
├── chatbot.py          # Main AI assistant code
├── security_test.py    # Security testing suite
├── requirements.txt    # Python dependencies
├── setup.bat          # Windows setup script
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## 🔒 Security Audit

This project has been audited for common vulnerabilities:
- ✅ Command injection prevention
- ✅ Path traversal protection
- ✅ Safe code evaluation
- ✅ Input validation
- ✅ Memory corruption handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run security tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This AI assistant is designed for personal use. Use responsibly and be aware of system permissions when running automated tasks.

---

**Made with ❤️ for PC automation and AI assistance** 
