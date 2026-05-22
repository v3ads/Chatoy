# Chatoy

A GitHub-backed static dashboard for HubActually HubBot that displays the latest run ledger from a source-controlled latest-run JSON file. Built with Manus.

## 🚀 Quick Start (Local Dev)

The app is designed to fail-closed for security. To run it locally without complex auth:

### 1. Backend (FastAPI)
```bash
cd app
# Create and activate venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure for local dev
export CHATOY_AUTH_DISABLED=true
export CHATOY_ANTHROPIC_API_KEY=your_key_here

# Start the server
uvicorn app.main:app --reload
```

### 2. Frontend (Next.js)
```bash
cd web
pnpm install
pnpm dev
```
Open [http://localhost:3000](http://localhost:3000). If you see a connection error, click **Settings** and ensure the API URL is `http://127.0.0.1:8000`.

## 🛠 Troubleshooting "Not Working"

If you encounter issues, check these common pitfalls:

| Issue | Solution |
| :--- | :--- |
| **503 Service Unavailable** | The backend auth is unconfigured. Set `CHATOY_AUTH_DISABLED=true` or provide Supabase credentials. |
| **401 Unauthorized** | The backend is expecting a token. Either disable auth (above) or paste a valid JWT in the frontend Settings. |
| **Connection Refused** | The frontend is trying to talk to the wrong URL. Check the **Settings** panel in the UI. |
| **Static Responses** | You are using the "Fake LLM". Provide a `CHATOY_ANTHROPIC_API_KEY` to enable real AI. |

## 📦 Deployment

- **Backend**: Deploy to Railway using the included `railway.toml` and `Dockerfile`.
- **Frontend**: Deploy to Vercel. Ensure `NEXT_PUBLIC_API_URL` is set to your backend URL.
- **Database**: Optional. If `CHATOY_DATABASE_URL` is missing, the app uses in-memory stores (data lost on restart).
