# Docker Troubleshooting Guide

## Issue: Frontend UI not showing at http://localhost:3000

### Symptoms
- Port 3000 shows a blank page or connection refused
- React app doesn't load

### Root Causes Fixed
1. **Empty App.jsx** - React component was missing (NOW FIXED)
2. **API URL** - Frontend couldn't connect to backend (NOW FIXED)
   - Changed from `http://localhost:8000` to `http://backend:8000` inside Docker
3. **Docker networking** - Services need to communicate via service names, not localhost

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- No services running on ports: 3000, 8000, 5432, 6379

### Step 1: Check Docker is Running
```powershell
docker --version
docker-compose --version
```

### Step 2: Clean Previous Containers (if needed)
```powershell
cd c:\Users\FCI\Documents\meeting-notes-agent
docker-compose down -v
docker system prune -f
```

### Step 3: Build & Start Services
```powershell
docker-compose up -d
```

### Step 4: Wait for Services to Initialize
- Backend: ~10-15 seconds to start
- Frontend: ~30-45 seconds (npm install & build)
- Database: ~5-10 seconds

### Step 5: Verify Services
```powershell
# Check all containers are running
docker ps

# Should see:
# - meeting-notes-backend
# - meeting-notes-frontend
# - meeting-notes-db
# - meeting-notes-redis
```

### Step 6: Access the Application
```
Frontend: http://localhost:3000
Backend API: http://localhost:8000
API Docs: http://localhost:8000/docs
```

## Common Issues & Solutions

### Issue 1: Port Already in Use
```powershell
# Find process using port 3000
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue

# Kill the process (if needed)
Stop-Process -Id <PID> -Force
```

### Issue 2: Frontend Container Keeps Restarting
**Solution**: Check logs
```powershell
docker logs meeting-notes-frontend
```

**Common causes**:
- npm install failed - run `docker-compose down -v && docker-compose up -d`
- Insufficient memory - increase Docker Desktop memory allocation

### Issue 3: Backend Connection Error
**Error**: "Failed to analyze transcript. Please check the API connection."

**Solution**: 
```powershell
# Check backend logs
docker logs meeting-notes-backend

# Verify API is responding
curl http://localhost:8000/health
```

### Issue 4: Database Connection Error
**Check if database is ready**:
```powershell
docker logs meeting-notes-db

# Connect to database
docker exec -it meeting-notes-db psql -U postgres -d meeting_notes -c "SELECT 1;"
```

### Issue 5: Blank White Page in Frontend
1. Check browser console for errors (F12)
2. Check frontend logs:
```powershell
docker logs meeting-notes-frontend
```
3. Clear browser cache: Ctrl+Shift+Delete
4. Restart frontend container:
```powershell
docker-compose restart frontend
```

## Monitoring & Debugging

### View Real-time Logs
```powershell
# All containers
docker-compose logs -f

# Specific container
docker-compose logs -f frontend
docker-compose logs -f backend
docker-compose logs -f db
```

### Enter Container Shell
```powershell
# Frontend
docker exec -it meeting-notes-frontend sh

# Backend
docker exec -it meeting-notes-backend bash

# Database
docker exec -it meeting-notes-db psql -U postgres -d meeting_notes
```

### Test Backend API
```powershell
# Health check
curl http://localhost:8000/health

# List endpoints
curl http://localhost:8000/docs
```

### Test Redis Connection
```powershell
docker exec -it meeting-notes-redis redis-cli ping
```

## Performance Tips

1. **Allocate More Memory to Docker**
   - Docker Desktop Settings → Resources → Memory: 4GB+ recommended

2. **First Time Setup is Slow**
   - npm install takes time (30-45 seconds)
   - Database initialization takes time
   - This is normal!

3. **Speed Up Subsequent Starts**
   - Containers are cached, subsequent starts are faster
   - Skip volume mounts if not needed

## Environment Variables

### Frontend (.env)
```
REACT_APP_API_URL=http://backend:8000  (inside Docker)
REACT_APP_API_URL=http://localhost:8000 (local development)
```

### Backend (.env)
```
OPENAI_API_KEY=sk-your-key-here (REQUIRED)
DATABASE_URL=postgresql://postgres:postgres123@db:5432/meeting_notes
REDIS_URL=redis://redis:6379
```

## Complete Restart Procedure

If everything is broken, use this nuclear option:

```powershell
cd c:\Users\FCI\Documents\meeting-notes-agent

# Stop all containers
docker-compose down

# Remove all volumes
docker-compose down -v

# Remove all images
docker-compose down --rmi all

# Clean system
docker system prune -f --volumes

# Rebuild from scratch
docker-compose up -d --build

# Wait 60 seconds for services to initialize
Start-Sleep -Seconds 60

# Verify everything
docker ps
```

## Verify Setup is Complete

```powershell
# Run this after containers are up for 60 seconds

# 1. Frontend is running
(curl http://localhost:3000 -UseBasicParsing).StatusCode -eq 200

# 2. Backend is running
(curl http://localhost:8000/health -UseBasicParsing).StatusCode -eq 200

# 3. Database is ready
docker exec meeting-notes-db pg_isready -U postgres -d meeting_notes

# 4. Redis is ready
docker exec meeting-notes-redis redis-cli ping
```

## Support

If issues persist:
1. Share output of `docker ps`
2. Share output of `docker logs meeting-notes-frontend`
3. Share output of `docker logs meeting-notes-backend`
4. Check system resources: `docker stats`

---

**Last Updated**: November 30, 2025
**Status**: All files created and configured
