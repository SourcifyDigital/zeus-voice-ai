# Zeus Voice AI — Deployment Guide

## Overview

Zeus Voice AI is a web app where users sign in with Google, then talk to their email, calendar, and the web. The frontend is a static HTML page (deploy on Vercel, free). The backend is a Python FastAPI server (deploy on Render, free).

## What You Need

| Service | Sign Up | Cost |
|---------|:-------:|:----:|
| Verce/Netlify | vercel.com | Free |
| Render / Railway | render.com | Free |
| Groq API Key | console.groq.com | Free tier |
| Google Cloud Project | console.cloud.google.com | Free |

## Step 1: Create a Google OAuth Web Client

1. Go to https://console.cloud.google.com/apis/credentials
2. Create a project (or use existing)
3. Click **"Create Credentials" → "OAuth 2.0 Client ID"**
4. Application type: **"Web application"**
5. Name: "Zeus Voice AI"
6. **Authorized JavaScript origins:** Add your frontend URL
   - For development: `http://localhost:5500`
   - For production: `https://your-app.vercel.app`
7. **Authorized redirect URIs:** Add your callback URL
   - For development: `http://localhost:8000/auth/google/callback`
   - For production: `https://your-backend.onrender.com/auth/google/callback`
8. Click **Create**
9. Copy the **Client ID** and **Client Secret**

## Step 2: Set Up the Backend (Render)

1. Go to https://render.com and sign up
2. Click **"New +" → "Web Service"**
3. Connect your GitHub/GitLab or upload the code
4. Or use Render's manual deploy:
   - Set **Runtime** to `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port 8000`

5. Add these **Environment Variables**:
   | Key | Value |
   |:----|:------|
   | `GROQ_API_KEY` | Your Groq API key |
   | `GOOGLE_CLIENT_ID` | Your Google OAuth Client ID |
   | `GOOGLE_CLIENT_SECRET` | Your Google OAuth Client Secret |
   | `BASE_URL` | `https://your-backend.onrender.com` |
   | `FRONTEND_URL` | `https://your-app.vercel.app` |

## Step 3: Set Up the Frontend (Vercel)

1. Go to https://vercel.com and sign up
2. Click **"Add New Project"**
3. Upload the `frontend/` folder
4. Make sure it points to `index.html`
5. **Optional:** In `app.js`, change `API_BASE`:
   - Development: `http://localhost:8000`
   - Production: `https://your-backend.onrender.com`

## Step 4: Test It

1. Open the frontend URL
2. Click **"Sign in with Google"**
3. Authorize the app
4. You'll be redirected back to the chat screen
5. Tap the mic and say: *"Read my emails"* or *"What's on my calendar?"*

## Customization

- **Change colors:** Edit `frontend/style.css` (search for `#00d4ff` = cyan accent color)
- **Change app name:** Search for "Zeus" in `frontend/index.html` and `backend/main.py`
- **Change TTS voice:** In `backend/main.py`, line 204, change `en-US-AndrewNeural` to any:
  - `en-US-JennyNeural` (female, professional)
  - `en-US-GuyNeural` (male, calm)
  - `en-GB-SoniaNeural` (British female)
  - Find all voices: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts

## Troubleshooting

| Problem | Fix |
|:--------|:----|
| "Sign in with Google" loops back | Check redirect URIs in Google Cloud Console |
| "Not authenticated" error | The backend session expired. Sign in again. |
| Microphone not working | Allow microphone permissions in browser |
| Audio not playing | Browser blocks autoplay — tap the screen first |
| Groq errors | Check GROQ_API_KEY is set and has credits |
