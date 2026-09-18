# SwasthyaSync — Quick Start Script
# Run both backend and frontend in separate windows

Write-Host "Starting SwasthyaSync..." -ForegroundColor Cyan

# Start backend
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
  cd '$PSScriptRoot\backend'
  Write-Host 'Starting FastAPI backend on http://localhost:8000...' -ForegroundColor Green
  python -m uvicorn main:app --reload --port 8000
"@

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend
Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
  cd '$PSScriptRoot\frontend'
  Write-Host 'Starting Vite frontend on http://localhost:5173...' -ForegroundColor Green
  cmd /c npm run dev
"@

Start-Sleep -Seconds 2
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "SwasthyaSync is running!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
