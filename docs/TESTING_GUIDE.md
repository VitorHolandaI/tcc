# Testing Guide - Complete System

## Overview

This guide walks you through testing all features of the TCC monitoring system after implementation.

## Quick Start

### Option 1: Docker (Recommended)

```bash
cd /home/vitor/git/tcc
./run-all-services.sh --docker
```

### Option 2: Local Development

```bash
cd /home/vitor/git/tcc
./run-all-services.sh --local
```

### Check Status

```bash
./run-all-services.sh --status
```

### View Logs

```bash
./run-all-services.sh --logs
```

### Stop All Services

```bash
./run-all-services.sh --stop
```

## Testing Checklist

### 1. Service Health Checks

Verify all services are running:

```bash
# Main API
curl http://localhost:8000/health
# Expected: {"status": "healthy"}

# Recording Service
curl http://localhost:8001/health

# Analysis Service
curl http://localhost:8002/health

# Webcam Service
curl http://localhost:8003/health

# Audio Service
curl http://localhost:8004/health

# Keystroke Service
curl http://localhost:8005/health

# Frontend
curl http://localhost:3000
# Expected: HTML page
```

### 2. User Authentication Flow

#### A. Create Professor Account
1. Navigate to: http://localhost:3000/signup
2. Fill form:
   - Name: "Professor Teste"
   - Email: "professor@test.com"
   - Password: "Test123!"
   - Role: Professor
3. Click "Cadastrar"
4. Expected: Redirect to login or dashboard

#### B. Create Student Account
1. Navigate to: http://localhost:3000/signup
2. Fill form:
   - Name: "Aluno Teste"
   - Email: "aluno@test.com"
   - Password: "Test123!"
   - Role: Aluno
3. Click "Cadastrar"
4. Expected: Redirect to login or dashboard

#### C. Login Test
1. Navigate to: http://localhost:3000/login
2. Login with professor account
3. Expected: Dashboard with "Criar Prova" button
4. Logout and login with student account
5. Expected: Dashboard with available exams

### 3. Exam Creation Flow (Professor)

1. Login as professor
2. Click "Criar Nova Prova"
3. Fill exam details:
   - Title: "Prova de Teste - Monitoramento Completo"
   - Description: "Teste de gravação de tela, webcam, áudio e keystroke"
   - Start date/time: (current date + 5 minutes)
   - End date/time: (current date + 30 minutes)
   - Duration: 20 minutes
   - Allowed emails: "aluno@test.com"
4. Add questions:
   - **Question 1** (Multiple Choice):
     - Text: "Qual comando Git cria um novo branch?"
     - Options: "git branch", "git checkout", "git new", "git create"
     - Correct: "git branch"
   - **Question 2** (Coding):
     - Text: "Escreva uma função que retorna a soma de dois números"
     - Language: Python
     - Test cases:
       - Input: "2, 3" → Output: "5"
       - Input: "10, 20" → Output: "30"
5. Click "Criar Prova"
6. Expected: Prova created, visible in dashboard

### 4. Exam Taking Flow (Student)

#### A. Start Exam
1. Login as student
2. Navigate to available exams
3. Click on "Prova de Teste - Monitoramento Completo"
4. Expected: Exam instructions and "Iniciar Prova" button
5. Click "Iniciar Prova"
6. Expected:
   - Browser prompts for screen sharing permission → Allow
   - Browser prompts for webcam permission → Allow
   - Browser prompts for microphone permission → Allow
   - Exam interface loads with first question

#### B. Answer Questions

**Question 1 (Multiple Choice):**
1. Select "git branch"
2. Click "Salvar" or auto-save should trigger
3. Expected: Answer saved, can move to next question

**Question 2 (Coding):**
1. Type code in Monaco Editor:
   ```python
   def soma(a, b):
       return a + b
   ```
2. Click "Executar Código"
3. Expected: Test results show Pass/Fail
4. Save answer

#### C. Monitor Keystroke Capture

While typing in the code editor:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for logs every 2 minutes:
   ```
    Keystroke data saved: X events
   ```
4. Expected: Keystroke events are being captured and auto-saved

#### D. Test Edge Cases

**Clipboard Operations:**
1. Copy text (Ctrl+C)
2. Paste text (Ctrl+V)
3. Cut text (Ctrl+X)
4. Expected: All operations captured with `command_type`

**Backspace and Arrow Keys:**
1. Type text, then backspace
2. Use arrow keys to move cursor
3. Expected: Captured with appropriate `command_type`

**Connection Loss Simulation:**
1. Open DevTools → Network tab
2. Enable "Offline" mode for 30 seconds
3. Continue typing
4. Disable "Offline" mode
5. Wait for auto-save (2 min)
6. Expected: All keystrokes saved (concatenated with previous data)

#### E. Finish Exam
1. Answer all questions
2. Click "Finalizar Prova"
3. Expected:
   - Confirmation dialog
   - After confirming: recordings stop, final keystroke data saved
   - Redirect to completion page
   - Console shows: "Final keystroke data saved"

### 5. Recording Verification (Professor)

1. Login as professor
2. Navigate to "Minhas Provas"
3. Click on "Prova de Teste - Monitoramento Completo"
4. Click on student "Aluno Teste"
5. Expected: Student submission page with:
   - Answers to questions
   - Score (if graded)
   - "Análises Comportamentais" section with 4 buttons

### 6. Behavioral Analysis Testing

#### A. Gaze Analysis

1. On student submission page, click "Analisar Gaze"
2. Expected:
   - Button shows loading spinner
   - Status changes to "Processando..."
   - After ~10-30 seconds (depending on video length):
     - Status changes to "Concluída"
     - Results card appears with metrics:
       - Average gaze position (x, y)
       - Deviations (x, y)
       - Suspicious frame percentage
3. Leave the page and return
4. Expected: Results are still visible (persistent)

#### B. Audio Analysis

1. Click "Analisar Áudio"
2. Expected:
   - Button shows loading spinner
   - Status changes to "Processando..."
   - After ~10-30 seconds:
     - Status changes to "Concluída"
     - Results card appears with metrics:
       - Total duration
       - Number of speech segments
       - Total speech duration
       - Silence percentage
       - Suspicious audio percentage

#### C. Keystroke Dynamics Analysis

1. Click "Analisar Keystroke"
2. Expected:
   - Button shows loading spinner
   - Status changes to "Processando..."
   - After ~5-15 seconds:
     - Status changes to "Concluída"
     - Results card appears with metrics:
       - Average hold time (ms)
       - Average flight time (ms)
       - Command counts (paste, copy, backspace, etc.)
       - Suspicious command percentage

#### D. View Complete Video

1. Click "Ver Vídeo Completo"
2. Expected:
   - Modal opens with video player
   - Video shows concatenated screen recording
   - Play/pause controls work
   - Can close modal

### 7. API Testing (Advanced)

#### A. Test Keystroke Endpoint Directly

```bash
# Get auth token (replace with actual token from browser DevTools → Application → Local Storage)
TOKEN="your-firebase-jwt-token"

# Test saving keystroke data
curl -X PUT http://localhost:8000/submissoes/keystroke/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "key": "a",
      "timestamp": "2024-01-01 12:00:00.000",
      "application": "Browser",
      "flight_time": null,
      "hold_time": 0.123,
      "command_type": null
    }
  ]'
```

#### B. Test Analysis Services

```bash
# Start gaze analysis
curl -X POST http://localhost:8002/analyze/1/1 \
  -H "Authorization: Bearer $TOKEN"

# Get gaze analysis result
curl http://localhost:8002/analysis/1/1 \
  -H "Authorization: Bearer $TOKEN"

# Start audio analysis
curl -X POST http://localhost:8004/analyze/1/1 \
  -H "Authorization: Bearer $TOKEN"

# Get audio analysis result
curl http://localhost:8004/analysis/1/1 \
  -H "Authorization: Bearer $TOKEN"

# Start keystroke analysis
curl -X POST http://localhost:8005/analyze/1/1 \
  -H "Authorization: Bearer $TOKEN"

# Get keystroke analysis result
curl http://localhost:8005/analysis/1/1 \
  -H "Authorization: Bearer $TOKEN"
```

### 8. Edge Cases and Error Handling

#### A. Student Not Whitelisted
1. Create exam with whitelist: "other@test.com"
2. Login as "aluno@test.com"
3. Try to access exam
4. Expected: 403 Forbidden error

#### B. Exam Not Started Yet
1. Create exam with start time in future
2. Student tries to access
3. Expected: Error message "Prova ainda não iniciou"

#### C. Exam Already Finished
1. Create exam with end time in past
2. Student tries to access
3. Expected: Error message "Prova já encerrou"

#### D. Missing Permissions (Screen/Webcam/Audio)
1. Start exam
2. Deny one of the permissions
3. Expected: Error message explaining which permission is needed

#### E. No Keystroke Data
1. Professor tries to analyze keystroke for submission with no keystroke data
2. Expected: Error message "Sem dados de keystroke disponíveis"

### 9. Database Verification

```bash
# Connect to PostgreSQL (Docker)
docker-compose exec postgres psql -U tcc_user -d tcc_db

# Or local PostgreSQL
psql -U tcc_user -d tcc_db

# Check keystroke data
SELECT id, aluno_id, prova_id,
       jsonb_array_length(keystroke_dynamics) as event_count
FROM submissao
WHERE keystroke_dynamics IS NOT NULL;

# Check analysis records
SELECT * FROM keystroke_analysis ORDER BY created_at DESC LIMIT 5;
SELECT * FROM audio_analysis ORDER BY created_at DESC LIMIT 5;
SELECT * FROM gaze_analysis ORDER BY created_at DESC LIMIT 5;
```

### 10. Performance Testing

#### A. Large Keystroke Dataset
1. Simulate long exam (30+ minutes)
2. Type continuously (generate 1000+ events)
3. Verify:
   - Auto-save every 2 minutes works
   - Final save completes successfully
   - Analysis completes in reasonable time (<30s)

#### B. Multiple Concurrent Students
1. Create exam
2. Have 3-5 students start exam simultaneously
3. Verify:
   - All streams initialize correctly
   - No port conflicts
   - All recordings save properly
   - Database handles concurrent writes

#### C. Network Interruption
1. Start exam
2. Disconnect network for 1 minute
3. Continue typing
4. Reconnect network
5. Verify:
   - Keystroke data is queued locally
   - Auto-save resumes
   - Data is concatenated correctly

## Common Issues and Solutions

### Issue: Services won't start
```bash
# Check if ports are in use
sudo netstat -tulpn | grep -E ':(3000|8000|8001|8002|8003|8004|8005)'

# Kill processes on ports
./run-all-services.sh --stop
# Or manually:
sudo lsof -ti:8000 | xargs kill -9
```

### Issue: Database connection errors
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Check database exists
psql -U postgres -c "\l"
```

### Issue: Frontend can't reach backend
- Check environment variables in `front/.env`
- Verify CORS settings in backend
- Check browser console for errors

### Issue: Keystroke events not captured
- Open DevTools Console to check for errors
- Verify Monaco Editor is initialized
- Check if auto-save interval is working (console logs)

### Issue: Analysis stuck in "Processando"
- Check service logs: `docker-compose logs analysis-service`
- Verify video/audio files exist in recordings folder
- Check if dependencies (OpenCV, Whisper) are installed

## Success Criteria

All tests pass if:

- All 7 services start without errors
- Health checks return 200 OK
- Professor can create exams
- Student can take exams
- Screen recording works (3 streams: screen, webcam, audio)
- Keystroke capture works (events saved every 2 min)
- Keystroke data format matches Roberto's analyzer
- Concatenation works when connection is lost
- All 3 analyses complete successfully:
  - Gaze analysis shows metrics
  - Audio analysis shows metrics
  - Keystroke analysis shows metrics
- Professor can view complete video
- Authorization works (whitelist, ownership)
- Database stores all data correctly

## Next Steps

After all tests pass:

1. Review `docs/VPS_DEPLOYMENT.md` for production deployment
2. Configure SSL certificates for HTTPS
3. Set up automated backups
4. Configure monitoring/alerting
5. Perform security audit
6. Load testing with multiple concurrent users

## Getting Help

If you encounter issues:
1. Check service logs: `./run-all-services.sh --logs`
2. Review error messages in browser console
3. Check database for data: `psql -U tcc_user -d tcc_db`
4. Consult implementation docs in `/docs` folder
5. Consult `docs/SERVICES_ARCHITECTURE.md` for service details
