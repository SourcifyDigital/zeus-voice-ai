import os
import json
import uuid
import time
import asyncio
import logging
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Google
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build

# Groq
import groq

# Audio
import edge_tts

# ── Load env ──────────────────────────────────────────────────────────
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    print("[WARN] GROQ_API_KEY not set. Voice processing will fail.")
    GROQ_API_KEY = "sk-fallback"

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# ── App setup ─────────────────────────────────────────────────────────
app = FastAPI(title="Zeus Voice AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
AUDIO_DIR = Path("audio_cache")
AUDIO_DIR.mkdir(exist_ok=True)

groq_client = groq.Groq(api_key=GROQ_API_KEY)

# Simple in-memory session store: token -> {email, creds_json}
SESSIONS: dict[str, dict] = {}

# ── Google OAuth Scopes ───────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]

# ── Routes ────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"status": "ok", "name": "Zeus Voice AI API"}

@app.get("/health")
def health():
    return {"status": "healthy"}

# ── Auth ──────────────────────────────────────────────────────────────

@app.get("/auth/google")
def google_login():
    """Redirect user to Google consent screen."""
    redirect_uri = f"{BASE_URL.rstrip('/')}/auth/google/callback"
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    return RedirectResponse(auth_url)


@app.get("/auth/google/callback")
async def google_callback(request: Request):
    """Handle OAuth callback — exchange code for token, store session."""
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(400, "Missing authorization code")

    redirect_uri = f"{BASE_URL.rstrip('/')}/auth/google/callback"
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )

    flow.fetch_token(code=code, authorization_response=str(request.url))
    creds = flow.credentials

    # Get user email
    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()
    email = user_info.get("email", "unknown@unknown.com")

    # Create session token
    token = str(uuid.uuid4())
    SESSIONS[token] = {
        "email": email,
        "creds_json": creds.to_json(),
    }

    # Redirect back to frontend with token
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5500")
    return RedirectResponse(f"{frontend_url}?token={token}&email={email}")


@app.get("/auth/status")
def auth_status(request: Request):
    """Check if user is authenticated."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session = SESSIONS.get(token)
    if not session:
        return {"authenticated": False}
    return {"authenticated": True, "email": session["email"]}


def _get_session(request: Request) -> dict:
    """Get authenticated session or raise 401."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    session = SESSIONS.get(token)
    if not session:
        raise HTTPException(401, "Not authenticated. Sign in with Google first.")
    return session


def _get_creds(session: dict) -> Credentials:
    """Rebuild Google credentials from stored JSON. Refresh if expired."""
    creds = Credentials.from_json(session["creds_json"])
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        # Update stored credentials
        session["creds_json"] = creds.to_json()
    return creds

# ── Voice Processing ──────────────────────────────────────────────────

@app.post("/api/ask")
async def ask(request: Request, audio: UploadFile = File(...)):
    """Receive audio, transcribe, process, TTS, return result."""
    session = _get_session(request)
    creds = _get_creds(session)

    # Save uploaded audio to temp file
    temp_id = uuid.uuid4().hex
    temp_path = AUDIO_DIR / f"input_{temp_id}.webm"
    content = await audio.read()
    with open(temp_path, "wb") as f:
        f.write(content)

    try:
        # 1. Transcribe with Groq Whisper
        with open(temp_path, "rb") as f:
            transcription = groq_client.audio.transcriptions.create(
                file=("audio.webm", f),
                model="whisper-large-v3",
                response_format="text",
            )
        transcript = transcription.strip()
        print(f"[TRANSCRIPT] {transcript}")

        # 2. Process with Groq Llama + Google APIs
        response_text = await process_command(transcript, creds)

        # 3. Generate TTS
        audio_filename = f"response_{temp_id}.mp3"
        audio_path = AUDIO_DIR / audio_filename
        communicate = edge_tts.Communicate(response_text, voice="en-US-AndrewNeural")
        await communicate.save(str(audio_path))

        return {
            "transcript": transcript,
            "text": response_text,
            "audio_url": f"/audio/{audio_filename}",
        }

    finally:
        # Clean up input audio
        if temp_path.exists():
            temp_path.unlink()


@app.get("/audio/{filename}")
def serve_audio(filename: str):
    """Serve generated TTS audio files."""
    filepath = AUDIO_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "Audio not found")
    return FileResponse(str(filepath), media_type="audio/mpeg")


# ── Command Processing ────────────────────────────────────────────────

async def process_command(text: str, creds: Credentials) -> str:
    """Route user command to the right Google API or general chat."""

    # Detect intent via keywords (fast, no extra LLM call)
    text_lower = text.lower()

    # ── Email intents ──
    if any(kw in text_lower for kw in ["read my email", "latest email", "new email", "check email", "any emails", "unread"]):
        try:
            return get_recent_emails(creds)
        except Exception as e:
            return f"Error reading emails: {str(e)[:100]}"

    if any(kw in text_lower for kw in ["send email", "send an email", "email to"]):
        return "Email sending is available. For now you can dictate what to write. Say 'Send an email to [name] about [subject] saying [message]'"

    # ── Calendar intents ──
    if any(kw in text_lower for kw in ["calendar", "my day", "schedule", "meeting", "appointment", "events", "what's on"]):
        try:
            return get_calendar_events(creds)
        except Exception as e:
            return f"Error reading calendar: {str(e)[:100]}"

    # ── Search intents ──
    if any(kw in text_lower for kw in ["search", "look up", "find", "google", "what is", "who is", "tell me about"]):
        return await web_search(text)

    # ── General conversation ──
    return await chat_response(text)


def get_recent_emails(creds: Credentials) -> str:
    """Fetch recent unread/important emails from Gmail."""
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=5, q="in:inbox").execute()
    messages = results.get("messages", [])
    if not messages:
        return "You have no emails in your inbox."

    response_lines = ["Here are your recent emails:"]
    for msg_data in messages:
        msg = service.users().messages().get(userId="me", id=msg_data["id"], format="metadata").execute()
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        from_name = headers.get("From", "Unknown").split("<")[0].strip().strip('"')
        subject = headers.get("Subject", "(No subject)")
        snippet = msg.get("snippet", "")[:80]
        response_lines.append(f"• From {from_name}: {subject}")
        if snippet:
            response_lines.append(f"  \"{snippet}\"")

    return "\n".join(response_lines)


def get_calendar_events(creds: Credentials) -> str:
    """Fetch today's calendar events."""
    from datetime import datetime, timezone, timedelta
    service = build("calendar", "v3", credentials=creds)

    now = datetime.now(timezone.utc)
    end_of_day = now.replace(hour=23, minute=59, second=59)

    events_result = service.events().list(
        calendarId="primary",
        timeMin=now.isoformat(),
        timeMax=end_of_day.isoformat(),
        maxResults=10,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    events = events_result.get("items", [])
    if not events:
        return "You have no upcoming events for the rest of today."

    response_lines = ["Here are your upcoming events:"]
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        summary = event.get("summary", "Untitled event")
        # Format time nicely
        try:
            dt = datetime.fromisoformat(start)
            time_str = dt.strftime("%I:%M %p").lstrip("0")
        except:
            time_str = start
        response_lines.append(f"• {time_str} — {summary}")

    return "\n".join(response_lines)


async def web_search(query: str) -> str:
    """Search the web and return a summary."""
    import httpx

    # Use DuckDuckGo instant answer API (no API key needed)
    search_url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(search_url, params=params, timeout=10)
            data = resp.json()

        # Extract abstract text
        abstract = data.get("AbstractText", "")
        if abstract:
            return f"Here's what I found: {abstract}"
        else:
            return f"I searched for that but didn't find a clear answer. You can try asking more specifically."
    except Exception as e:
        return f"Sorry, I had trouble searching. {str(e)[:80]}"


async def chat_response(text: str) -> str:
    """General conversation via Groq Llama."""
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Zeus, a voice AI assistant. You help users with their email, calendar, "
                        "and web search. Keep responses concise and conversational since they will be read "
                        "aloud. Use natural language, not bullet points."
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=300,
        )
        return completion.choices[0].message.content

    except Exception as e:
        return f"Sorry, I hit an error: {str(e)[:80]}"


# ── Startup ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("╔═══════════════════════════════════════╗")
    print("║     Zeus Voice AI — Backend Server     ║")
    print("╚═══════════════════════════════════════╝")
    print(f"Base URL: {BASE_URL}")
    print(f"Frontend: {os.getenv('FRONTEND_URL', 'http://localhost:5500')}")
    print("Waiting for connections...\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
