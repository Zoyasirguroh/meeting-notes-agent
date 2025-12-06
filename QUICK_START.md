# Quick Reference Card

## Start Application

```powershell
# Windows
.\START.bat

# PowerShell
powershell -ExecutionPolicy Bypass -File .\START.ps1

# Manual
docker-compose up -d
```

## Access

| What | URL |
|------|-----|
| App | http://localhost:3000 |
| API | http://localhost:8000 |
| Docs | http://localhost:8000/docs |

## Status Check

```powershell
docker ps
docker logs meeting-notes-frontend
docker logs meeting-notes-backend
```

## Stop

```powershell
.\STOP.bat
# or
docker-compose down
```

## Restart

```powershell
docker-compose restart
```

## Common Issues

| Problem | Solution |
|---------|----------|
| Blank page | `docker logs meeting-notes-frontend` |
| API error | `docker logs meeting-notes-backend` |
| Port in use | Change port in docker-compose.yml |
| Slow start | Wait 60 seconds, first run is slow |

## Reset Everything

```powershell
docker-compose down -v
docker-compose up -d
```

## View Logs

```powershell
docker-compose logs -f
docker-compose logs -f frontend
docker-compose logs -f backend
```

## Important Files

- `backend/.env` - Add your OPENAI_API_KEY here
- `docker-compose.yml` - Service configuration
- `SETUP.md` - Full setup guide
- `DOCKER_TROUBLESHOOTING.md` - Detailed troubleshooting

---

See SETUP.md for complete documentation.
