# Meeting Notes Agent - Setup & Troubleshooting

## What Was Fixed

Your application wasn't showing at `http://localhost:3000` because:

1. **Empty React Component** - `App.jsx` was blank → **NOW POPULATED** with a full 350+ line React application
2. **Missing Styling** - `index.css` had no styles → **NOW COMPLETE** with full CSS styling
3. **Docker Networking** - Frontend was trying to reach backend at `localhost` inside containers → **NOW USES** `backend:8000` (service name)

## Project Structure

```
meeting-notes-agent/
├── docker-compose.yml              ✓ Main orchestration (FIXED)
├── init-db.sql                     ✓ Database schema
├── DOCKER_TROUBLESHOOTING.md       ✓ Detailed troubleshooting guide
├── START.bat                       ✓ Windows startup script
├── START.ps1                       ✓ PowerShell startup script
├── STOP.bat                        ✓ Windows stop script
│
├── backend/
│   ├── .dockerignore               ✓ Docker ignore file
│   ├── .env                        ✓ Environment variables (has API key placeholder)
│   ├── .env.example                ✓ Template for .env
│   ├── Dockerfile                  ✓ Backend container config
│   ├── main.py                     ✓ FastAPI application
│   ├── transcription.py            ✓ Audio processing (for future use)
│   ├── websocket.py                ✓ Real-time features
│   └── requirements.txt            ✓ Python dependencies
│
└── frontend/
    ├── .dockerignore               ✓ Docker ignore file
    ├── Dockerfile                  ✓ Frontend container config
    ├── package.json                ✓ Node dependencies
    ├── public/
    │   └── index.html              ✓ HTML template
    └── src/
        ├── App.jsx                 ✓ React component (350+ lines, FIXED)
        ├── index.js                ✓ React entry point
        └── index.css               ✓ Global styles (complete CSS, FIXED)
```

## Quick Start

### Option 1: Using Windows Batch Script (Easiest)

```powershell
cd c:\Users\FCI\Documents\meeting-notes-agent
.\START.bat
```

The script will:
- ✓ Check Docker is installed and running
- ✓ Start all containers
- ✓ Wait for services to initialize
- ✓ Open http://localhost:3000 in your browser

### Option 2: Using PowerShell Script

```powershell
cd c:\Users\FCI\Documents\meeting-notes-agent
powershell -ExecutionPolicy Bypass -File .\START.ps1
```

### Option 3: Manual Commands

```powershell
cd c:\Users\FCI\Documents\meeting-notes-agent

# Clean previous run (if needed)
docker-compose down -v

# Start services
docker-compose up -d

# Wait 60 seconds for initialization
Start-Sleep -Seconds 60

# Open in browser
start http://localhost:3000
```

## After Starting

### Access Points

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend** | http://localhost:3000 | React UI |
| **Backend** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/docs | Swagger documentation |
| **Database** | localhost:5432 | PostgreSQL (see .env for credentials) |
| **Redis** | localhost:6379 | Cache/queues |

### First Run Timing

- **First start**: 60-90 seconds (npm install, builds, database init)
- **Subsequent starts**: 10-20 seconds (containers already built)

### What's Running

```powershell
# Check all services are healthy
docker ps

# You should see:
# - meeting-notes-frontend (port 3000)
# - meeting-notes-backend (port 8000)
# - meeting-notes-db (port 5432)
# - meeting-notes-redis (port 6379)
```

## Configuration

### API Key (IMPORTANT!)

The backend requires an OpenAI API key for AI analysis:

1. Get key from: https://platform.openai.com/api-keys
2. Edit `backend/.env`:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```

### Database

Default credentials (in docker-compose.yml):
- **User**: postgres
- **Password**: postgres123
- **Database**: meeting_notes
- **Host**: db (inside Docker), localhost (from host)

### Frontend API Connection

Inside Docker: `http://backend:8000` (configured in docker-compose.yml)
Local development: `http://localhost:8000` (if running outside Docker)

## Testing the Application

### 1. Verify Services Started

```powershell
# Check Docker containers
docker ps

# Check backend is responding
curl http://localhost:8000/health

# Check frontend is serving
curl http://localhost:3000 -UseBasicParsing | Select-Object StatusCode
```

### 2. View Logs

```powershell
# All logs with timestamps
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f db
```

### 3. Test API

```powershell
# View API documentation
start http://localhost:8000/docs

# Test analysis endpoint (example)
$body = @{
    transcript = "Team discussed project timeline. John assigned to frontend, Sarah to backend."
    meeting_platform = "zoom"
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8000/analyze" `
  -ContentType "application/json" `
  -Body $body
```

## Troubleshooting

### Issue: Port Already in Use

```powershell
# Find process on port 3000
Get-NetTCPConnection -LocalPort 3000 | Select-Object ProcessId
taskkill /PID <PID> /F
```

### Issue: Frontend Shows Blank Page

1. **Check browser console**: F12 → Console tab
2. **Check logs**:
   ```powershell
   docker logs meeting-notes-frontend
   ```
3. **Clear cache**: Ctrl+Shift+Delete → Clear all
4. **Restart**: `docker-compose restart frontend`

### Issue: "Failed to analyze transcript" Error

This means the backend isn't responding. Check:

```powershell
# Is backend running?
docker ps | findstr backend

# Check backend logs
docker logs meeting-notes-backend

# Is API responding?
curl http://localhost:8000/health
```

### Issue: Database Connection Error

```powershell
# Check database container
docker logs meeting-notes-db

# Verify database is ready
docker exec meeting-notes-db pg_isready -U postgres -d meeting_notes

# Connect to database
docker exec -it meeting-notes-db psql -U postgres -d meeting_notes
```

### Issue: Redis Connection Error

```powershell
# Check redis container
docker logs meeting-notes-redis

# Test redis connection
docker exec meeting-notes-redis redis-cli ping
```

## Stopping & Restarting

### Stop Services

```powershell
# Using script
.\STOP.bat

# Or manually
docker-compose down
```

### Stop & Remove All Data

```powershell
docker-compose down -v
```

### Complete Reset (Nuclear Option)

```powershell
# Stop and remove everything
docker-compose down -v --rmi all

# Clean Docker system
docker system prune -f --volumes

# Start fresh
docker-compose up -d
```

## Development Mode

### Running Locally (Without Docker)

**Backend Requirements**:
- Python 3.11+
- PostgreSQL 15
- Redis 7

```powershell
# Install Python dependencies
pip install -r backend/requirements.txt

# Set environment variables
$env:DATABASE_URL = "postgresql://localhost/meeting_notes"
$env:REDIS_URL = "redis://localhost:6379"
$env:OPENAI_API_KEY = "your-key-here"

# Run backend
uvicorn backend.main:app --reload

# In another terminal, run frontend
cd frontend
npm install
npm start
```

**Frontend Requirements**:
- Node.js 18+
- npm or yarn

```powershell
cd frontend
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

## File Descriptions

### Backend Files

- **main.py** (334 lines)
  - FastAPI application
  - `/analyze` endpoint for transcript analysis
  - `/export` endpoint for exporting results
  - `/notify` endpoint for notifications
  - CORS enabled for frontend communication

- **requirements.txt**
  - FastAPI, uvicorn for web server
  - OpenAI for AI analysis
  - psycopg2 for PostgreSQL
  - redis for caching
  - Integration libraries: jira, slack-sdk, notion-client

- **websocket.py**
  - Real-time features (for future use)
  - WebSocket connection handling

- **transcription.py**
  - Audio processing (for future use)
  - Placeholder for transcription logic

### Frontend Files

- **App.jsx** (350+ lines)
  - Tab-based interface (Input/Results)
  - Audio recording capability
  - Real-time analysis with loading state
  - Export to PDF/CSV
  - Email notifications
  - Display of: Tasks, Decisions, Risks, Follow-ups, Summary

- **index.css** (500+ lines)
  - Complete styling with CSS variables
  - Responsive design (mobile, tablet, desktop)
  - Dark theme compatibility
  - Animations and transitions

- **index.html**
  - Standard React template
  - Viewport configuration
  - Meta tags for SEO

- **package.json**
  - React 18.3.1
  - react-scripts 5.0.1
  - axios for API calls
  - lucide-react for icons

### Configuration Files

- **docker-compose.yml**
  - 5 services: frontend, backend, postgres, redis, (optionally more)
  - Volume mounts for development
  - Environment variables
  - Service networking and dependencies

- **Dockerfile** (frontend & backend)
  - Multi-stage builds for optimization
  - Production-ready configuration
  - Proper layer caching

- **init-db.sql**
  - Database schema with tables for:
    - meetings, tasks, decisions, risks, follow-ups
    - participants, transcription_segments
    - exports, notifications
  - Indexes for performance
  - Triggers for timestamps

## Next Steps

1. **Set API Key**: Edit `backend/.env` with your OpenAI API key
2. **Start Application**: Run `.\START.bat`
3. **Test**: Open http://localhost:3000
4. **Analyze Meetings**: Paste a meeting transcript and click "Analyze Meeting"
5. **Review Results**: Check tasks, decisions, risks, follow-ups
6. **Export**: Download results as PDF or CSV

## Support & Debugging

For detailed troubleshooting, see: `DOCKER_TROUBLESHOOTING.md`

Key commands:
```powershell
docker-compose logs -f              # View live logs
docker ps                           # List running containers
docker exec -it <container> sh      # Enter container shell
docker stats                        # Monitor resource usage
```

---

**Status**: ✓ All files created and configured
**Last Updated**: November 30, 2025
