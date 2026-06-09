# Zeus Voice AI

A web-based voice AI assistant. Sign in with Google, then talk to your email, calendar, and the web.

## One Command to Run

```bash
# Backend
cd backend
cp .env.example .env  # Edit .env with your API keys
pip install -r requirements.txt
python main.py

# Frontend (separate terminal)
cd frontend
# Serve with any static server, e.g.:
python -m http.server 5500
# Or deploy the frontend/ folder to Vercel
```

## What Works

- 🎤 Voice input (mic button → Groq Whisper transcription)
- 🧠 AI responses (Groq Llama 3.3 70B)
- 🔊 Voice output (Microsoft Edge TTS)
- 🔑 Sign in with Google (Gmail + Calendar access)
- 📧 Read recent emails
- 📅 Check today's calendar
- 🔍 Web search
- 💬 General conversation
- 📱 Mobile responsive

## Project Structure

```
zeus-voice-web/
├── frontend/
│   ├── index.html      # Single page app
│   ├── style.css       # Dark theme
│   └── app.js          # Mic, auth, display logic
├── backend/
│   ├── main.py         # FastAPI server (1 file)
│   ├── requirements.txt
│   └── .env.example    # Template for API keys
└── docs/
    ├── DEPLOYMENT_GUIDE.md   # Step-by-step deploy to Vercel + Render
    └── BUYER_GUIDE.md        # How to rebrand and sell
```

## License

This is a saleable product. See selling guide in `docs/BUYER_GUIDE.md`.
