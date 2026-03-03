# AI Avatar Setup Guide

## ✅ Successfully Pushed to Git!

Your real-time AI avatar system has been pushed to GitHub with all the improvements:
- ✅ Groq API integration (cloud-based LLM)
- ✅ Working lip-sync with Wav2Lip
- ✅ Real-time display window
- ✅ Interactive text mode
- ✅ API keys secured with environment variables

---

## 🔐 Security: API Keys

Your Groq API key is now stored in `.env` file (which is **NOT** pushed to GitHub).

### For other users cloning this repo:

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Groq API key:
   ```
   GROQ_API_KEY=your_actual_api_key_here
   ```

3. Get a free API key from: https://console.groq.com/keys

---

## 🚀 Quick Start

Run the interactive avatar:
```bash
.\venv\Scripts\python.exe run_avatar_interactive.py
```

Features:
- Type messages and see the avatar respond
- Real-time lip synchronization
- Press 'q' to quit the display window
- Type 'quit' or 'exit' to end the session

---

## 📁 Files Added

- `.env` - Your local API keys (not tracked by git)
- `.env.example` - Template for other users
- `run_avatar_interactive.py` - Interactive mode
- `src/llm/groq_stream.py` - Groq API integration
- Updated `src/config.py` - Reads API key from environment

---

## 🔧 Requirements

Install python-dotenv if needed:
```bash
pip install python-dotenv
```

All dependencies are in `requirements.txt`.

---

## ✨ What's Working

- ✅ Real-time display window (no hanging)
- ✅ Lip sync with voice
- ✅ Groq API (fast cloud LLM)
- ✅ Edge-TTS speech generation
- ✅ Interactive conversations
- ✅ FPS display
- ✅ Keyboard controls (q to quit)

Enjoy your AI avatar! 🤖✨
