# Test Maker Platform - Services Architecture Documentation

**Version**: 1.0
**Last Updated**: February 2026
**Project**: Online Exam Proctoring Platform (TCC)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Pattern](#architecture-pattern)
3. [Backend Services](#backend-services)
4. [Frontend Application](#frontend-application)
5. [Analysis Services](#analysis-services)
6. [Inter-Service Communication](#inter-service-communication)
7. [Data Flow & Storage](#data-flow--storage)
8. [Authentication & Authorization](#authentication--authorization)
9. [Future Innovations](#future-innovations)

---

## System Overview

The Test Maker Platform is a comprehensive online exam proctoring system designed to monitor student behavior during coding exams through multiple behavioral analysis techniques. The system employs a distributed microservices architecture with specialized services for different monitoring aspects.

### Key Capabilities

- **Exam Management**: Create, schedule, and manage coding exams
- **Multi-Language Support**: Python, JavaScript, Java, C++, Go
- **Real-Time Monitoring**: Screen recording, webcam capture, audio recording
- **Behavioral Analysis**: Gaze tracking, keystroke dynamics, speaker diarization, code similarity
- **Automated Grading**: Test case execution and evaluation
- **Professor Dashboard**: Comprehensive submission review with analysis tools

### Technology Stack

| Layer | Technology |
|-------|-----------|
| **Backend Framework** | FastAPI (Python 3.9+) |
| **Frontend Framework** | React 19 + TypeScript |
| **Build Tool** | Vite 7.2 |
| **Database** | PostgreSQL 15 (production), SQLite (dev) |
| **ORM** | SQLAlchemy |
| **Authentication** | Firebase Authentication + JWT |
| **Real-Time Communication** | WebSocket |
| **Video Processing** | ffmpeg, OpenCV, MediaPipe |
| **Audio Analysis** | PyAnnote.audio (HuggingFace) |
| **Code Editor** | Monaco Editor |

---

## Architecture Pattern

### Microservices Architecture

The system follows a **distributed microservices pattern** with a central monolithic API that orchestrates specialized services.

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND (React + TypeScript) │
│ Port 3000/80 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ MAIN API (Port 8000) │
│ FastAPI Monolithic App │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Controllers: │ │
│ │ - Professor, Student, Exam, Question, Submission │ │
│ │ - Recording, Analysis, Monitoring, Evaluation │ │
│ └──────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │ Database: PostgreSQL (Exams, Submissions, Users) │ │
│ └──────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │ │ │ │ │
         ▼ ▼ ▼ ▼ ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
    │Recording│ │Webcam │ │Audio │ │Analysis│ │Keystroke
    │Service │ │Service │ │Service │ │Service │ │Service
    │(8001) │ │(8003) │ │(8004) │ │(8002) │ │(8005)
    └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
         │ │ │ │ │
         └───────────┴───────────┴───────────┴───────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │ Similarity │
                      │ Service │
                      │ (8006) │
                      └──────────────┘
```

### Design Principles

1. **Service Isolation**: Each microservice has independent deployment, database, and scaling
2. **Shared Storage**: Media files (recordings, videos, audio) stored on shared volumes
3. **Async Processing**: Long-running analyses use background tasks
4. **Stateless Services**: All services are stateless (state in database/storage)
5. **Health Monitoring**: Each service exposes health check endpoints
6. **Graceful Degradation**: Core exam functionality works even if analysis services fail

---

## Backend Services

### Main API Service (Port 8000)

**Location**: `/back/app/`
**Purpose**: Central orchestrator for exam platform functionality

#### Architecture

**Controllers** (`/app/controllers/`):
- `professor_controller.py` - Professor CRUD operations, exam ownership
- `aluno_controller.py` - Student management and enrollment
- `prova_controller.py` - Exam lifecycle (create, start, finish, delete)
- `questao_controller.py` - Question management for exams
- `submissao_controller.py` - Student code submissions with keystroke data
- `recording_controller.py` - Recording orchestration (delegates to Recording Service)
- `analysis_controller.py` - Analysis orchestration (gaze, audio, keystroke, similarity)
- `monitoring_controller.py` - Real-time exam monitoring
- `avaliacao_controller.py` - Grading and evaluation

**Models** (`/app/models/`):
- `professor_model.py` - Professor entity with Firebase UID
- `aluno_model.py` - Student entity with Firebase UID
- `prova_model.py` - Exam entity (title, language, start/end dates)
- `questao_model.py` - Question entity (description, examples, weight, test cases)
- `submissao_model.py` - Submission entity with `keystroke_dynamics` JSON field
- `video_analysis_model.py` - Gaze analysis results

**Repositories** (`/app/repositories/`):
- Database access layer with CRUD operations for each entity
- Query builders for complex operations (submissions by exam, questions by exam, etc.)

**Core** (`/app/core/`):
- `database.py` - PostgreSQL connection pool configuration
- `auth_dependency.py` - JWT token validation middleware
- `firebase_config.py` - Firebase Admin SDK initialization
- `enums.py` - Status enums (ExamStatus, SubmissionStatus, AnalysisStatus)
- `ownership.py` - Authorization helpers (verify exam ownership)

#### Database Schema

**Key Tables**:
- `professores` - Professor accounts (id, nome, email, firebase_uid)
- `alunos` - Student accounts (id, nome, email, matricula, firebase_uid)
- `provas` - Exams (id, titulo, linguagem, data_inicio, data_fim, professor_id)
- `questoes` - Questions (id, titulo, descricao, peso, test_cases, prova_id)
- `submissoes` - Submissions (id, codigo_submetido, keystroke_dynamics JSON, aluno_id, questao_id)
- `avaliacoes` - Grades (id, nota, feedback, submissao_id)
- `video_analyses` - Gaze analysis results

#### Key Endpoints

```
POST /professors - Create professor account
GET /professors/me - Get current professor
POST /alunos - Create student account
GET /alunos - List all students
POST /provas - Create exam
GET /provas/{id} - Get exam details
POST /provas/{id}/start - Start exam (enable submissions)
POST /provas/{id}/finish - Finish exam (disable submissions)
GET /provas/{id}/questoes - List exam questions
POST /submissoes - Submit code for question
GET /submissoes/prova/{prova_id} - Get all submissions for exam
POST /recordings/finalize/{prova_id}/{aluno_id} - Finalize recording
GET /recordings/video/{prova_id}/{aluno_id} - Download recording
POST /analysis/gaze/{prova_id}/{aluno_id} - Start gaze analysis
GET /analysis/gaze/{prova_id}/{aluno_id} - Get gaze results
```

#### Configuration

**Environment Variables**:
```env
DATABASE_URL=postgresql://testmaker:testmaker123@localhost:5432/testmaker
RECORDING_SERVICE_URL=http://localhost:8001
ANALYSIS_SERVICE_URL=http://localhost:8002
RECORDINGS_DIR=./recordings
FIREBASE_PROJECT_ID=your-project-id
```

---

### Recording Service (Port 8001)

**Location**: `/back/recording-service/`
**Purpose**: High-volume WebSocket-based screen recording with resume capability

#### Architecture

**Key Components**:
- `main.py` - FastAPI app with WebSocket endpoint
- `storage_manager.py` - Segment management and file I/O
- `config.py` - Environment-based configuration

**Classes**:
- `SegmentManager` - Handles segment creation, metadata tracking
- `ActiveRecordingsManager` - Thread-safe concurrent recording management with async locks

#### How It Works

1. **WebSocket Connection** (`/ws/{prova_id}`):
   - Client sends Firebase JWT token for authentication
   - Service validates student is enrolled in exam
   - Creates recording session with unique segment directory

2. **Segment-Based Storage**:
   - Receives video chunks via WebSocket
   - Writes to segments: `segment_000.webm`, `segment_001.webm`, etc.
   - Each segment capped at 50MB (configurable via `MAX_SEGMENT_SIZE_MB`)
   - Maintains `metadata.json` with timing info and file sizes

3. **Resume Capability**:
   - If connection drops, student can reconnect
   - Service finds existing segments and continues from last index
   - Prevents data loss during network interruptions

4. **Finalization** (`POST /finalize/{prova_id}/{aluno_id}`):
   - Concatenates all segments using ffmpeg
   - Creates final video: `prova_{id}_aluno_{id}.webm`
   - Returns file size and duration
   - Auto-triggered when professor views recording if not already finalized

#### Storage Structure

```
/recordings/
├── segments/
│ ├── prova_1_aluno_123/
│ │ ├── metadata.json
│ │ ├── segment_000.webm
│ │ ├── segment_001.webm
│ │ └── ...
│ └── prova_1_aluno_456/
│ └── ...
├── prova_1_aluno_123.webm (finalized)
└── prova_1_aluno_456.webm
```

#### Scalability

- Supports **150+ concurrent recordings** with async I/O
- Lock-based concurrency control prevents race conditions
- Background task queue for finalization operations
- Health check endpoint reports capacity: `GET /health`

#### Configuration

```env
RECORDING_SERVICE_HOST=0.0.0.0
RECORDING_SERVICE_PORT=8001
RECORDINGS_DIR=/app/recordings
SEGMENTS_DIR=/app/recordings/segments
MAX_CONCURRENT_RECORDINGS=150
MAX_SEGMENT_SIZE_MB=50
FIREBASE_PROJECT_ID=your-project-id
```

---

### Analysis Service (Port 8002)

**Location**: `/back/analysis-service/`
**Purpose**: Eye/gaze tracking analysis on webcam recordings

#### Architecture

**Key Components**:
- `main.py` - FastAPI app with analysis endpoints
- `gaze_analyzer.py` - MediaPipe-based face and gaze detection
- `models.py` - VideoAnalysis database model

**Technology**:
- **MediaPipe FaceMesh** - Facial landmark detection (468 points)
- **Head Pose Estimation** - 3D rotation angles from 2D landmarks
- **Gaze Direction** - Calculated from head orientation

#### How It Works

1. **Trigger Analysis** (`POST /analyze/{prova_id}/{aluno_id}`):
   - Validates exam is finished (`data_fim < now`)
   - Only professor who owns exam can trigger
   - Creates VideoAnalysis record with status `processing`
   - Launches background task

2. **Video Processing**:
   - Reads webcam recording from `/webcam_recordings/webcam_prova_{id}_aluno_{id}.webm`
   - Processes every N frames (default 5, configurable via `PROCESS_EVERY_N_FRAMES`)
   - For each frame:
     - Detects face with MediaPipe FaceMesh
     - Calculates head pose (rotation angles)
     - Determines gaze direction: Forward, Left, Right, Up, Down, No Face

3. **Metrics Calculation**:
   - `percentage_forward` - % of frames looking forward
   - `percentage_left/right/up/down` - % of frames in each direction
   - `percentage_no_face` - % of frames with no face detected
   - `position_changes_per_minute` - Gaze direction change frequency
   - `total_position_changes` - Total direction switches
   - `suspicious_periods` - Array of timestamps with unusual behavior

4. **Result Storage**:
   - Updates VideoAnalysis record with metrics
   - Status: `pending` → `processing` → `completed` or `failed`
   - Progress percentage for resume capability

#### Gaze Classification

```python
Direction Thresholds:
- Forward: pitch [-15°, 15°], yaw [-15°, 15°]
- Left: yaw < -15°
- Right: yaw > 15°
- Up: pitch < -15°
- Down: pitch > 15°
```

#### Configuration

```env
ANALYSIS_SERVICE_HOST=0.0.0.0
ANALYSIS_SERVICE_PORT=8002
WEBCAM_RECORDINGS_DIR=/app/webcam_recordings
MAX_CONCURRENT_ANALYSIS=10
PROCESS_EVERY_N_FRAMES=5
USE_GPU=false
FIREBASE_PROJECT_ID=your-project-id
```

#### Performance

- Processes 1-hour video in ~5-10 minutes (CPU mode, every 5 frames)
- GPU acceleration available with `USE_GPU=true`
- Concurrency limited to 10 parallel analyses (prevents CPU overload)

---

### Webcam Service (Port 8003)

**Location**: `/back/webcam-service/`
**Purpose**: Capture student's face for gaze analysis input

#### Architecture

Simple WebSocket service for webcam streaming.

**Endpoints**:
- `POST /ws/{prova_id}` - WebSocket endpoint for streaming
- `GET /video/{prova_id}/{aluno_id}` - Serve webcam video (professor-only)
- `GET /` - Health check

#### How It Works

1. Client connects via WebSocket with Firebase JWT
2. Streams webcam video chunks in real-time
3. Saves as single file: `webcam_prova_{id}_aluno_{id}.webm`
4. Professors can download video for review

#### Storage

```
/webcam_recordings/
├── webcam_prova_1_aluno_123.webm
├── webcam_prova_1_aluno_456.webm
└── ...
```

#### Configuration

```env
WEBCAM_DIR=/app/webcam_recordings
FIREBASE_PROJECT_ID=your-project-id
```

---

### Audio Service (Port 8004)

**Location**: `/back/audio-service/`
**Purpose**: Audio capture and speaker diarization analysis

#### Architecture

**Key Components**:
- `main.py` - FastAPI app with WebSocket and analysis endpoints
- `audio_analyzer.py` - PyAnnote.audio wrapper for speaker diarization
- `models.py` - AudioRecording and AudioAnalysis models

**Technology**:
- **PyAnnote.audio** - State-of-the-art speaker diarization from HuggingFace
- **Pipeline**: `pyannote/speaker-diarization-3.1`
- **Torch/TorchAudio** - Deep learning framework for audio processing

#### How It Works

**Audio Capture** (`POST /ws/{prova_id}`):
1. WebSocket connection with JWT authentication
2. Receives audio chunks in real-time
3. Saves as WAV file: `prova_{id}_aluno_{id}.wav`
4. Creates AudioRecording database entry with metadata

**Speaker Diarization** (`POST /analyze/{prova_id}/{aluno_id}`):
1. Loads audio file from storage
2. Applies PyAnnote speaker diarization pipeline
3. Detects:
   - Number of unique speakers
   - Speaker timeline (who spoke when)
   - Overlapping speech periods
   - Silence percentage
4. Stores results in AudioAnalysis table

#### Output Example

```json
{
  "status": "completed",
  "total_speakers": 2,
  "has_multiple_speakers": true,
  "speaker_timeline": [
    {"speaker": "SPEAKER_00", "start": 0.5, "end": 12.3},
    {"speaker": "SPEAKER_01", "start": 12.5, "end": 25.1},
    {"speaker": "SPEAKER_00", "start": 25.2, "end": 40.0}
  ],
  "silence_percentage": 15.2,
  "overlapping_periods": [
    {"start": 12.2, "end": 12.5, "speakers": ["SPEAKER_00", "SPEAKER_01"]}
  ]
}
```

#### Use Cases

- Detect if student talked to someone during exam (multiple speakers)
- Identify extended conversations (long overlapping periods)
- Flag exams with suspiciously low silence percentage

#### Configuration

```env
AUDIO_SERVICE_HOST=0.0.0.0
AUDIO_SERVICE_PORT=8004
AUDIO_DIR=/app/audio_recordings
HUGGINGFACE_TOKEN=hf_your_token_here
USE_GPU=false
MAX_CONCURRENT_AUDIO_ANALYSIS=5
MIN_SPEAKER_CONFIDENCE=0.5
FIREBASE_PROJECT_ID=your-project-id
```

---

### Keystroke Service (Port 8005)

**Location**: `/back/keystroke-service/`
**Purpose**: Keystroke dynamics and typing pattern analysis

#### Architecture

**Key Components**:
- `main.py` - FastAPI app with analysis endpoints
- `keystroke_analyzer.py` - Statistical analysis of typing patterns
- `models.py` - KeystrokeAnalysis model

#### How It Works

1. **Data Source**:
   - Reads keystroke events from `submissao.keystroke_dynamics` JSON field in main database
   - Each event: `{type: "keydown/keyup", key: "a", timestamp: 1234567890, command: null}`
   - Captured in real-time by frontend during exam

2. **Analysis Metrics**:

   **Typing Rhythm**:
   - `hold_time` - Duration key is pressed (keydown → keyup)
   - `flight_time` - Time between releasing one key and pressing next
   - Calculates average and standard deviation for both

   **Suspicious Commands**:
   - Detects: Ctrl+C, Ctrl+V, Ctrl+X (copy/paste/cut)
   - Counts: Backspace, Delete, Escape, Tab usage
   - Calculates `suspicious_percentage` based on command frequency

   **Manhattan Distance**:
   - Measures typing pattern deviation from baseline
   - Higher values indicate unusual typing behavior

3. **Suspicion Scoring**:
   - Combines command frequency, timing anomalies, and pattern deviation
   - Generates `suspicious_percentage` (0-100%)
   - Flags exams with >20% as high risk

#### Output Example

```json
{
  "status": "completed",
  "typing_metrics": {
    "hold_time_avg": 0.095,
    "hold_time_std": 0.042,
    "flight_time_avg": 0.180,
    "flight_time_std": 0.098
  },
  "suspicious_commands": {
    "suspicious_percentage": 12.5,
    "command_counts": {
      "copy": 3,
      "paste": 5,
      "backspace": 45,
      "delete": 2
    }
  },
  "manhattan_metrics": {
    "total_distance": 15.67,
    "average_deviation": 0.42
  }
}
```

#### Configuration

```env
KEYSTROKE_SERVICE_HOST=0.0.0.0
KEYSTROKE_SERVICE_PORT=8005
MAX_CONCURRENT_KEYSTROKE_ANALYSIS=5
MIN_EVENTS_THRESHOLD=10
FIREBASE_PROJECT_ID=your-project-id
```

---

### Similarity Service (Port 8006)

**Location**: `/back/similarity-service/`
**Purpose**: Code plagiarism detection across student submissions

#### Architecture

**Key Components**:
- `main.py` - FastAPI app with analysis endpoints
- `similarity_analyzer.py` - Code comparison algorithm (MOSS-like)
- `models.py` - SimilarityAnalysis model

#### How It Works

1. **Trigger Analysis** (`POST /analyze/{prova_id}`):
   - Only exam owner (professor) can trigger
   - Fetches all submissions for the exam from main database
   - Groups submissions by question ID

2. **Pairwise Comparison**:
   - For each question, compares all submission pairs
   - Applies code similarity algorithm:
     - Tokenization (removes whitespace, comments)
     - N-gram extraction
     - Jaccard similarity coefficient
     - Structural similarity (AST comparison)

3. **Threshold Detection**:
   - Configurable threshold (default 70%)
   - Pairs above threshold flagged as suspicious
   - Generates detailed diff for review

4. **Result Aggregation**:
   - Groups suspicious pairs by question
   - Calculates overall plagiarism risk per exam
   - Stores full results in SimilarityAnalysis table

#### Output Example

```json
{
  "status": "completed",
  "prova_id": 1,
  "threshold": 70.0,
  "suspicious_pairs": [
    {
      "questao_id": 1,
      "questao_titulo": "Implementar ordenação",
      "aluno1_id": 123,
      "aluno1_nome": "João Silva",
      "aluno2_id": 456,
      "aluno2_nome": "Maria Santos",
      "similarity_score": 87.5,
      "diff_url": "/similarity/diff/1/123/456"
    }
  ],
  "total_pairs_analyzed": 45,
  "suspicious_count": 3
}
```

#### Configuration

```env
SIMILARITY_SERVICE_HOST=0.0.0.0
SIMILARITY_SERVICE_PORT=8006
MAX_CONCURRENT_SIMILARITY_ANALYSIS=5
SIMILARITY_THRESHOLD=70.0
FIREBASE_PROJECT_ID=your-project-id
```

---

## Frontend Application

**Location**: `/front/`
**Tech Stack**: React 19 + TypeScript + Vite

### Architecture

#### Directory Structure

```
/front/src/
├── pages/ # Page components
│ ├── Login.tsx
│ ├── DashboardProfessor.tsx
│ ├── DashboardAluno.tsx
│ ├── CriarProva.tsx
│ ├── FazerProva.tsx
│ ├── SubmissoesProva.tsx
│ └── VisualizarSubmissao.tsx
├── components/ # Reusable components
│ ├── ProtectedRoute.tsx
│ ├── TextBox.tsx # Code editor with keystroke capture
│ └── ScreenGuard.tsx # Prevents tab switching
├── services/ # API communication
│ ├── apiConfig.ts
│ ├── ApiMethods.ts
│ ├── ProvaService.ts
│ ├── SubmissaoService.ts
│ ├── AnalysisService.ts
│ └── RecordingService.ts
├── contexts/ # Global state
│ └── AuthContext.tsx
├── hooks/ # Custom React hooks
│ └── useKeystrokeCapture.ts
├── runners/ # Code execution
│ ├── PythonRunner.ts
│ ├── JavaScriptRunner.ts
│ └── BackendRunner.ts
├── css/ # Stylesheets
└── config/ # Firebase config
```

### Key Features

#### Authentication Flow

1. **Login** (`/`):
   - Firebase Google OAuth sign-in
   - Extracts Firebase UID and ID token
   - Determines user type by email domain:
     - `@ccc.ufcg.edu.br` or `@computacao.ufcg.edu.br` → Professor
     - All other domains → Student
   - Creates account in backend if first login
   - Redirects to appropriate dashboard

2. **Protected Routes**:
   - `ProtectedRoute` component wraps all authenticated pages
   - Checks Firebase auth state
   - Validates token freshness (refreshes if expired)
   - Redirects to login if unauthenticated

#### Professor Workflow

1. **Create Exam** (`/professor/criar-prova`):
   - Define exam title, language, start/end dates
   - Add questions with descriptions, examples, test cases, weights
   - Set visibility and grading options

2. **View Submissions** (`/professor/prova/{id}/submissoes`):
   - Grid of student cards with avatars
   - Question completion progress bars
   - Weighted grade calculation
   - Click to view detailed submission

3. **Analyze Submission** (`/professor/prova/{id}/submissao/{aluno_id}`):
   - Split view: question description (left), submitted code (right)
   - Question navigation carousel
   - **Behavioral Analysis Toolbar**:
     - Gaze Analysis (generate/view dropdown)
     - Audio Analysis (generate/view dropdown)
     - Keystroke Analysis (generate/view dropdown)
     - View Screen Recording button
     - View Webcam Recording button
     - Code Similarity button
   - Grade editing interface
   - Execution result display

#### Student Workflow

1. **Take Exam** (`/aluno/fazer-prova/{id}`):
   - Full-screen mode with screen guard (prevents tab switching)
   - Monaco code editor with syntax highlighting
   - Real-time keystroke capture (timing and commands)
   - Screen recording permission request
   - Webcam recording permission request
   - Audio recording permission request
   - Question navigation
   - Submit code button
   - Finalize exam button

2. **View Results** (`/aluno/resultado/{id}`):
   - Submitted code for each question
   - Execution results (test case pass/fail)
   - Grade (if available)
   - Feedback from professor

### API Communication

**Service Layer Pattern**:

```typescript
// ProvaService.ts
class ProvaService {
  static async get(prova_id: number, token: string): Promise<Prova> {
    const response = await ApiMethods.get(`/provas/${prova_id}`, token);
    return response.data;
  }

  static async criar(payload: ProvaPayload, token: string): Promise<Prova> {
    const response = await ApiMethods.post('/provas', payload, token);
    return response.data;
  }
}
```

**Multi-Service Architecture**:
- Main API (8000): Exams, submissions, users
- Recording Service (8001): Screen recording WebSocket
- Analysis Service (8002): Gaze analysis
- Webcam Service (8003): Webcam recording
- Audio Service (8004): Audio recording and analysis
- Keystroke Service (8005): Keystroke analysis
- Similarity Service (8006): Code similarity

### Real-Time Recording

**Screen Recording**:
```typescript
// Uses MediaRecorder API
const stream = await navigator.mediaDevices.getDisplayMedia({
  video: { mediaSource: 'screen' }
});
const mediaRecorder = new MediaRecorder(stream);
const ws = new WebSocket(`ws://localhost:8001/ws/${prova_id}`);

mediaRecorder.ondataavailable = (event) => {
  ws.send(event.data); // Send chunks to Recording Service
};
```

**Keystroke Capture**:
```typescript
// useKeystrokeCapture.ts hook
const captureEvent = (event: KeyboardEvent, type: 'keydown' | 'keyup') => {
  const keystrokeEvent = {
    type,
    key: event.key,
    timestamp: Date.now(),
    command: detectCommand(event) // Ctrl+C, Ctrl+V, etc.
  };
  keystrokeData.push(keystrokeEvent);
};
```

### UI Components

**TextBox Component** (Code Editor):
- Monaco Editor integration
- Syntax highlighting for multiple languages
- Autocomplete with custom completions
- Keystroke capture hook attached
- Prevents paste (Ctrl+V disabled)
- Line numbers and minimap

**ScreenGuard Component**:
- Enters full-screen mode on exam start
- Detects tab switching (visibility change)
- Warns student if they leave the exam tab
- Logs suspicious activity

---

## Analysis Services

### Gaze Tracking (`/analise/gaze/`)

**Standalone Research Tool** - Not part of production deployment

#### Components

1. **Head Pose Estimation** (`head_estimate.py`):
   - Uses MediaPipe FaceMesh (468 facial landmarks)
   - Calculates 3D head rotation from 2D landmarks
   - Real-time inference on webcam feed
   - Output: Looking Left/Right/Up/Down/Forward

2. **Eye Gaze Tracking** (`hello.py`):
   - Extracts iris position relative to eye bounds
   - **Calibration Phase**: User looks at 5 points (corners + center)
   - **Linear Regression**: Maps iris position → screen coordinates
   - **Smoothing**: Exponential weighted average (α=0.15)
   - Real-time gaze point visualization

#### Technology

- **OpenCV** - Webcam capture and image processing
- **MediaPipe** - Face mesh detection
- **NumPy** - Linear algebra for regression
- **SciKit-Learn** - Linear regression model (optional)

#### Usage

```bash
# Head pose estimation
python analise/gaze/head_estimate.py

# Eye gaze tracking with calibration
python analise/gaze/hello.py
# Press 'C' to calibrate (look at 5 points)
# Press 'R' to recalibrate
```

#### Limitations

- Hardcoded screen resolution (1920x1080)
- Linear regression with only 5 calibration points (low accuracy)
- No depth perception (can't distinguish distance from screen)
- Blink detection is crude (eye height threshold)

---

### TccRoberto Keylogger (`/tccRoberto/`)

**Research Tool** - Privacy-invasive, not for production use

#### Components

1. **Full Keylogger** (`keylogger.py`):
   - System-wide keyboard monitoring with `pynput`
   - Logs ALL keystrokes including alphanumeric characters
   - Captures active window/application
   - Records keystroke timing (hold time, flight time)
   - Saves to `keylog.json` in plaintext

2. **Limited Keylogger** (`limited_keylogger.py`):
   - Same as full keylogger but omits alphanumeric characters
   - Still logs special keys, commands, timing, and active application
   - Slightly less invasive but still privacy-concerning

3. **Analyzer** (`analyzer.py`):
   - Reads `keylog.json` and performs statistical analysis
   - Calculates typing metrics (hold time, flight time statistics)
   - Detects outliers (Z-score > 3)
   - Computes Manhattan distance for pattern deviation
   - Generates PDF report with graphs

#### Privacy Concerns

 **WARNING**: This tool logs all keystrokes system-wide, including:
- Passwords typed in browsers or other apps
- Personal emails and messages
- Search queries
- Sensitive form data

**Not Recommended for Production** - Use backend keystroke service instead, which only captures during exams and within the exam interface.

#### Usage (Research Only)

```bash
# Start full keylogger
python tccRoberto/keylogger.py

# Start limited keylogger
python tccRoberto/limited_keylogger.py

# Analyze captured data
python tccRoberto/analyzer.py

# Generate report
python tccRoberto/report_generator.py
```

---

## Inter-Service Communication

### Communication Patterns

#### HTTP/REST

**Main API → Microservices**:
```python
# recording_controller.py
import httpx

async def finalize_recording(prova_id: int, aluno_id: int):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{RECORDING_SERVICE_URL}/finalize/{prova_id}/{aluno_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
    return response.json()
```

**Frontend → All Services**:
```typescript
// AnalysisService.ts
static async startGazeAnalysis(prova_id: number, aluno_id: number, token: string) {
  const response = await axios.post(
    `${ANALYSIS_SERVICE_URL}/analyze/${prova_id}/${aluno_id}`,
    {},
    { headers: { Authorization: `Bearer ${token}` } }
  );
  return response.data;
}
```

#### WebSocket

**Screen/Webcam/Audio Recording**:
```typescript
// Frontend opens WebSocket to Recording Service
const ws = new WebSocket(`ws://localhost:8001/ws/${prova_id}`);

// Send auth token first
ws.send(JSON.stringify({ token: firebaseToken }));

// Stream video chunks
mediaRecorder.ondataavailable = (event) => {
  ws.send(event.data); // Binary data
};
```

#### Database Sharing

**Cross-Service Queries**:
```python
# keystroke-service/main.py imports models from main app
from app.models.submissao_model import Submissao

# Query main database
submissao = db.query(Submissao).filter(
    Submissao.aluno_id == aluno_id,
    Submissao.prova_id == prova_id
).first()
```

**Concerns**: Tight coupling between services. Better approach: API calls instead of direct DB access.

### Authentication Flow

1. **Frontend**: User logs in with Firebase Google OAuth
2. **Frontend**: Gets Firebase ID token
3. **Frontend**: Sends token in `Authorization: Bearer {token}` header to all services
4. **Backend Services**: Each service validates token independently with Firebase Admin SDK
5. **User Type Determination**: Email domain checked:
   - `@ccc.ufcg.edu.br` or `@computacao.ufcg.edu.br` → Professor
   - All others → Student
6. **Authorization**: Services check if user owns resource (exam, submission)

---

## Data Flow & Storage

### Storage Architecture

```
/back/
├── data/ # SQLite databases (dev mode)
│ └── escola.db
├── recordings/ # Screen recordings
│ ├── segments/ # Temporary segments
│ │ └── prova_{id}_aluno_{id}/
│ │ ├── metadata.json
│ │ └── segment_*.webm
│ └── prova_{id}_aluno_{id}.webm
├── webcam_recordings/ # Webcam videos
│ └── webcam_prova_{id}_aluno_{id}.webm
├── audio_recordings/ # Audio files
│ └── prova_{id}_aluno_{id}.wav
└── logs/ # Application logs
    ├── main-api.log
    ├── recording-service.log
    └── ...
```

### Database Architecture

**PostgreSQL (Production)**:
- Single shared database: `testmaker`
- All services connect to same database
- Tables: professores, alunos, provas, questoes, submissoes, avaliacoes, video_analyses, audio_recordings, audio_analyses, keystroke_analyses, similarity_analyses

**SQLite (Development)**:
- Each service can have independent database
- Main API: `escola.db`
- Microservices: `{service}_service.db`

### Exam Lifecycle Data Flow

```
1. Professor Creates Exam
   ├─> POST /provas (Main API)
   ├─> Inserts into provas table
   └─> Creates questions in questoes table

2. Student Takes Exam
   ├─> GET /provas/{id} (Main API) - Fetch exam details
   ├─> GET /provas/{id}/questoes - Fetch questions
   ├─> Opens WebSocket to Recording Service (screen)
   ├─> Opens WebSocket to Webcam Service (face)
   ├─> Opens WebSocket to Audio Service (audio)
   ├─> Types code in Monaco editor (keystroke capture active)
   ├─> POST /submissoes (Main API) - Submit code with keystroke_dynamics JSON
   └─> Closes WebSockets when exam finishes

3. Professor Reviews Submission
   ├─> GET /submissoes/prova/{id} - List all submissions
   ├─> GET /submissoes/{aluno_id} - View specific submission
   ├─> POST /analysis/gaze/{prova_id}/{aluno_id} - Trigger gaze analysis
   │ └─> Analysis Service reads webcam recording, processes, stores results
   ├─> POST /audio/analyze/{prova_id}/{aluno_id} - Trigger audio analysis
   │ └─> Audio Service reads audio file, diarization, stores results
   ├─> POST /keystroke/analyze/{prova_id}/{aluno_id} - Trigger keystroke analysis
   │ └─> Keystroke Service reads keystroke_dynamics from submissao, analyzes, stores results
   ├─> GET /recordings/video/{prova_id}/{aluno_id} - Download screen recording
   │ └─> Recording Service finalizes segments (if not done), serves video
   └─> POST /similarity/analyze/{prova_id} - Run plagiarism detection
       └─> Similarity Service compares all submissions for exam
```

### Shared Volumes (Docker)

```yaml
volumes:
  recordings:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./back/recordings

  webcam-recordings:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./back/webcam_recordings

  audio-recordings:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ./back/audio_recordings
```

**All services mount these volumes** → Analysis services can read recordings created by recording services.

---

## Authentication & Authorization

### Firebase Authentication

**Setup**:
```python
# firebase_config.py
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("path/to/firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
```

**Token Validation**:
```python
# auth_dependency.py
from firebase_admin import auth
from fastapi import HTTPException, Header

async def verify_firebase_token(authorization: str = Header(...)):
    try:
        token = authorization.split("Bearer ")[1]
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### User Type Determination

```python
def get_user_type(email: str) -> str:
    professor_domains = ["@ccc.ufcg.edu.br", "@computacao.ufcg.edu.br"]
    if any(email.endswith(domain) for domain in professor_domains):
        return "professor"
    return "aluno"
```

### Authorization Checks

**Exam Ownership**:
```python
def verify_exam_ownership(prova_id: int, professor_id: int, db: Session):
    prova = db.query(Prova).filter(Prova.id == prova_id).first()
    if not prova or prova.professor_id != professor_id:
        raise HTTPException(status_code=403, detail="Access denied")
```

**Enrollment Check**:
```python
def verify_student_enrolled(prova_id: int, aluno_id: int, db: Session):
    # Check if student is enrolled in exam (via prova_alunos table)
    enrollment = db.query(ProvaAluno).filter(
        ProvaAluno.prova_id == prova_id,
        ProvaAluno.aluno_id == aluno_id
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="Not enrolled")
```

---

## Future Innovations

### Scalability Enhancements

#### 1. Full PostgreSQL Migration
**Current**: Services use mix of SQLite (dev) and PostgreSQL (main API)
**Future**: All services use PostgreSQL with separate schemas

```yaml
# docker-compose.yml
postgres:
  image: postgres:15-alpine
  environment:
    - POSTGRES_DB=testmaker
  volumes:
    - postgres-data:/var/lib/postgresql/data

# Each service connects to same database but different schema
main-api:
  environment:
    - DATABASE_URL=postgresql://testmaker:pass@postgres:5432/testmaker?schema=main

recording-service:
  environment:
    - DATABASE_URL=postgresql://testmaker:pass@postgres:5432/testmaker?schema=recording
```

**Benefits**: Better concurrency, ACID guarantees, connection pooling, replication

#### 2. Message Queue for Async Tasks
**Current**: Background tasks use FastAPI `BackgroundTasks` (in-memory, lost on restart)
**Future**: RabbitMQ or Redis for durable task queues

```python
# Celery task example
@celery_app.task
def analyze_gaze(prova_id: int, aluno_id: int):
    # Long-running analysis
    result = GazeAnalyzer.process_video(...)
    db.add(VideoAnalysis(result))
    db.commit()

# Controller triggers task
@app.post("/analyze/{prova_id}/{aluno_id}")
async def trigger_analysis(prova_id: int, aluno_id: int):
    task = analyze_gaze.delay(prova_id, aluno_id)
    return {"task_id": task.id}
```

**Benefits**: Task persistence, retry logic, distributed workers, progress tracking

#### 3. Load Balancing with Nginx
**Current**: Single instance of each service
**Future**: Multiple instances behind Nginx reverse proxy

```nginx
upstream recording-service {
    server recording-1:8001;
    server recording-2:8001;
    server recording-3:8001;
}

server {
    listen 80;
    location /recordings/ {
        proxy_pass http://recording-service;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Benefits**: Horizontal scaling, high availability, session affinity

#### 4. Kubernetes Deployment
**Current**: Docker Compose (single-host deployment)
**Future**: Kubernetes with auto-scaling

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: recording-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: recording-service
  template:
    spec:
      containers:
      - name: recording
        image: testmaker/recording-service:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: recording-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: recording-service
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Benefits**: Auto-scaling based on load, self-healing, rolling updates, resource limits

#### 5. Distributed Storage (S3/MinIO)
**Current**: Local filesystem with bind mounts
**Future**: Object storage for recordings

```python
import boto3

s3 = boto3.client('s3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)

# Upload recording
with open('prova_1_aluno_123.webm', 'rb') as f:
    s3.upload_fileobj(f, 'recordings', 'prova_1_aluno_123.webm')

# Generate presigned URL for download
url = s3.generate_presigned_url('get_object',
    Params={'Bucket': 'recordings', 'Key': 'prova_1_aluno_123.webm'},
    ExpiresIn=3600
)
```

**Benefits**: Unlimited storage, CDN integration, backup/versioning, georeplication

### Security Improvements

#### 1. Encryption at Rest
**Current**: Recordings stored as plaintext WebM/WAV files
**Future**: AES-256 encryption for all media files

```python
from cryptography.fernet import Fernet

# Encrypt on write
key = Fernet.generate_key()
cipher = Fernet(key)
encrypted_data = cipher.encrypt(video_data)
with open('recording.webm.enc', 'wb') as f:
    f.write(encrypted_data)

# Decrypt on read
with open('recording.webm.enc', 'rb') as f:
    encrypted = f.read()
decrypted = cipher.decrypt(encrypted)
```

**Benefits**: Protects data if storage is compromised, compliance with privacy regulations

#### 2. Service-to-Service Authentication
**Current**: Services trust each other (no mutual authentication)
**Future**: Mutual TLS (mTLS) between services

```python
# Service generates certificate
openssl req -x509 -newkey rsa:4096 -keyout service.key -out service.crt

# FastAPI with client cert verification
import uvicorn
uvicorn.run(app,
    ssl_keyfile="service.key",
    ssl_certfile="service.crt",
    ssl_ca_certs="ca.crt",
    ssl_cert_reqs=ssl.CERT_REQUIRED
)
```

**Benefits**: Prevents service impersonation, zero-trust architecture

#### 3. Rate Limiting
**Current**: No rate limiting (vulnerable to DoS)
**Future**: Per-user and per-endpoint rate limits

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/recordings/finalize/{prova_id}/{aluno_id}")
@limiter.limit("5/minute")
async def finalize_recording(...):
    ...
```

**Benefits**: Prevents abuse, ensures fair resource usage

#### 4. Audit Logging
**Current**: Basic application logs
**Future**: Comprehensive audit trail for all data access

```python
def log_audit(user_id: int, action: str, resource: str, result: str):
    audit_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        result=result,
        timestamp=datetime.now(),
        ip_address=request.client.host
    )
    db.add(audit_entry)
    db.commit()

# Usage
@app.get("/recordings/video/{prova_id}/{aluno_id}")
async def get_recording(...):
    log_audit(professor_id, "VIEW_RECORDING", f"prova_{prova_id}_aluno_{aluno_id}", "SUCCESS")
    return FileResponse(...)
```

**Benefits**: Forensic analysis, compliance, detect unauthorized access

#### 5. Token Rotation
**Current**: Firebase tokens long-lived
**Future**: Short-lived tokens with refresh mechanism

```typescript
// Frontend refreshes token every hour
setInterval(async () => {
  const user = firebase.auth().currentUser;
  if (user) {
    const newToken = await user.getIdToken(true); // Force refresh
    localStorage.setItem('token', newToken);
  }
}, 3600000); // 1 hour
```

**Benefits**: Reduced risk if token is stolen, forced re-authentication

### Analysis Enhancements

#### 1. Real-Time Anomaly Detection
**Current**: Post-exam analysis only
**Future**: Live monitoring during exam with real-time alerts

```python
# WebSocket for live analysis stream
@app.websocket("/monitor/{prova_id}/{aluno_id}")
async def monitor_exam(websocket: WebSocket, prova_id: int, aluno_id: int):
    await websocket.accept()

    while True:
        # Get recent activity
        gaze_data = get_recent_gaze(aluno_id)
        keystroke_data = get_recent_keystrokes(aluno_id)
        audio_data = get_recent_audio(aluno_id)

        # Detect anomalies
        anomalies = detect_anomalies(gaze_data, keystroke_data, audio_data)

        if anomalies:
            await websocket.send_json({
                "type": "anomaly",
                "data": anomalies,
                "timestamp": datetime.now().isoformat()
            })

        await asyncio.sleep(5)
```

**Benefits**: Immediate intervention, better deterrent effect

#### 2. Multi-Modal Fusion
**Current**: Separate analysis for gaze, audio, keystroke
**Future**: Combined analysis with unified suspicion score

```python
def calculate_unified_suspicion_score(prova_id: int, aluno_id: int):
    gaze = get_gaze_analysis(prova_id, aluno_id)
    audio = get_audio_analysis(prova_id, aluno_id)
    keystroke = get_keystroke_analysis(prova_id, aluno_id)

    # Weighted combination
    score = (
        0.3 * gaze.suspicious_percentage +
        0.3 * audio.multiple_speaker_score +
        0.4 * keystroke.suspicious_percentage
    )

    # Contextual adjustments
    if gaze.no_face_percentage > 30 and audio.total_speakers > 1:
        score *= 1.5 # High correlation → increase confidence

    return min(score, 100)
```

**Benefits**: More accurate detection, fewer false positives, holistic view

#### 3. Baseline Learning
**Current**: Fixed thresholds for suspicious behavior
**Future**: ML-based baseline per student

```python
from sklearn.ensemble import IsolationForest

# Train on student's past exams
def train_baseline(aluno_id: int):
    past_exams = get_student_history(aluno_id)
    features = extract_features(past_exams) # hold_time, flight_time, etc.

    model = IsolationForest(contamination=0.1)
    model.fit(features)

    save_model(aluno_id, model)

# Detect anomalies
def detect_anomaly(aluno_id: int, current_exam):
    model = load_model(aluno_id)
    features = extract_features([current_exam])

    is_anomaly = model.predict(features)[0] == -1
    return is_anomaly
```

**Benefits**: Personalized detection, reduced false positives for atypical typing patterns

#### 4. Proctoring Dashboard
**Current**: Analysis results in submission view
**Future**: Dedicated real-time monitoring dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│ Exam: Midterm Exam - Algorithms │
│ Active Students: 45/50 │
├─────────────────────────────────────────────────────────────────┤
│ │
│ Name Status Anomalies Last Activity │
│ ─────────────────────────────────────────────────────────── │
│ João Silva Taking 3 2s ago │
│ Maria Santos Taking 0 5s ago │
│ Pedro Costa Taking 1 10s ago │
│ ... │
│ │
│ [Filter: All | Suspicious Only | Inactive] │
│ │
├─────────────────────────────────────────────────────────────────┤
│ Alerts: │
│ João Silva - Multiple speakers detected (3 min ago) │
│ Pedro Costa - Gaze away from screen >30s (5 min ago) │
└─────────────────────────────────────────────────────────────────┘
```

**Benefits**: Scalable monitoring for large exams, prioritize suspicious students

#### 5. Student Transparency Report
**Current**: No visibility into what data is collected
**Future**: Post-exam report showing all collected data

```
Your Exam Data Report - Midterm Exam

Data Collected:
 Screen Recording (1h 45m) - Stored for 30 days
 Webcam Recording (1h 45m) - Stored for 30 days
 Audio Recording (1h 45m) - Stored for 30 days
 Keystroke Timing (2,847 events) - Stored for 90 days
 Code Submissions (5 questions) - Stored indefinitely

Analysis Performed:
- Gaze Tracking: 87% looking forward
- Audio Analysis: 1 speaker detected
- Keystroke Dynamics: Normal typing pattern
- Code Similarity: No matches above 70%

Your Rights:
- Request data deletion after grading (within 30 days)
- Appeal suspicious behavior flags
- View detailed analysis results

Questions? Contact: proctor@university.edu
```

**Benefits**: Transparency, student trust, GDPR compliance

### Privacy & Ethics

#### 1. Differential Privacy
**Current**: Raw data stored and analyzed
**Future**: Privacy-preserving analysis with noise injection

```python
def add_laplace_noise(value: float, sensitivity: float, epsilon: float):
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return value + noise

# Example: Anonymized gaze percentage
def get_anonymized_gaze_percentage(prova_id: int):
    students = get_all_students(prova_id)
    percentages = [s.gaze_forward for s in students]

    # Add noise to each value
    anonymized = [
        add_laplace_noise(p, sensitivity=1.0, epsilon=0.5)
        for p in percentages
    ]

    return np.mean(anonymized) # Still useful for aggregate analysis
```

**Benefits**: Protects individual privacy while enabling research

#### 2. Configurable Monitoring Levels
**Current**: All monitoring always enabled
**Future**: Professor chooses monitoring intensity

```python
class MonitoringLevel(Enum):
    MINIMAL = "minimal" # Only code submissions
    STANDARD = "standard" # + keystroke dynamics
    ENHANCED = "enhanced" # + screen recording
    FULL = "full" # + webcam + audio + gaze

@app.post("/provas")
async def create_exam(exam_data: ProvaPayload):
    exam = Prova(
        ...
        monitoring_level=exam_data.monitoring_level,
        require_screen_recording=(exam_data.monitoring_level in [MonitoringLevel.ENHANCED, MonitoringLevel.FULL]),
        require_webcam=(exam_data.monitoring_level == MonitoringLevel.FULL),
        require_audio=(exam_data.monitoring_level == MonitoringLevel.FULL)
    )
    db.add(exam)
    db.commit()
```

**Benefits**: Proportional monitoring, respects student privacy

#### 3. Data Retention Policies
**Current**: Data stored indefinitely
**Future**: Automatic deletion after retention period

```python
# Cron job runs daily
@app.on_event("startup")
def schedule_cleanup():
    scheduler.add_job(cleanup_old_recordings, 'cron', hour=2)

def cleanup_old_recordings():
    cutoff_date = datetime.now() - timedelta(days=30)

    old_exams = db.query(Prova).filter(Prova.data_fim < cutoff_date).all()

    for exam in old_exams:
        # Delete recordings
        recording_path = f"recordings/prova_{exam.id}_*"
        for file in glob.glob(recording_path):
            secure_delete(file)

        # Delete analysis results
        db.query(VideoAnalysis).filter(VideoAnalysis.prova_id == exam.id).delete()
        db.commit()
```

**Benefits**: Minimizes data exposure, GDPR compliance

#### 4. Consent Management
**Current**: Implicit consent
**Future**: Explicit consent with opt-out options

```typescript
// Frontend consent modal before exam
<ConsentModal>
  <h2>Data Collection Consent</h2>
  <p>This exam will collect the following data:</p>

  <Checkbox checked disabled>
     Code submissions (required)
  </Checkbox>

  <Checkbox checked={consent.keystroke} onChange={...}>
    Keystroke timing patterns
  </Checkbox>

  <Checkbox checked={consent.screen} onChange={...}>
    Screen recording
  </Checkbox>

  <Checkbox checked={consent.webcam} onChange={...}>
    Webcam recording (for gaze tracking)
  </Checkbox>

  <Checkbox checked={consent.audio} onChange={...}>
    Audio recording (for speaker detection)
  </Checkbox>

  <p>Declining optional items may affect your exam experience.</p>

  <Button onClick={submitConsent}>I Understand and Consent</Button>
</ConsentModal>
```

**Benefits**: Legal compliance, student autonomy

### Developer Experience

#### 1. OpenAPI/Swagger Documentation
**Current**: No API documentation
**Future**: Auto-generated interactive docs

```python
# FastAPI automatically generates OpenAPI schema
app = FastAPI(
    title="Test Maker API",
    description="Online exam proctoring platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Accessible at http://localhost:8000/api/docs
```

**Benefits**: Easy integration, reduced onboarding time

#### 2. Centralized Configuration
**Current**: Environment variables scattered across services
**Future**: Configuration service (Consul, etcd)

```python
import consul

config = consul.Consul()

# Get config value
db_url = config.kv.get('database/url')[1]['Value'].decode('utf-8')

# Watch for changes
def on_config_change(key, value):
    reload_database_connection(value)

config.kv.watch('database/url', on_config_change)
```

**Benefits**: Dynamic reconfiguration, version control for config

#### 3. Development Seed Data
**Current**: Manual database setup
**Future**: Automated seed script with realistic data

```python
# seed_development.py
def seed_database():
    # Create professors
    prof1 = Professor(nome="Dr. João Silva", email="joao@ccc.ufcg.edu.br")
    prof2 = Professor(nome="Dr. Maria Santos", email="maria@ccc.ufcg.edu.br")

    # Create students
    alunos = [
        Aluno(nome=f"Student {i}", email=f"student{i}@example.com", matricula=f"2024{i:04d}")
        for i in range(1, 51)
    ]

    # Create exam with questions
    exam = Prova(
        titulo="Sample Midterm Exam",
        linguagem="python",
        data_inicio=datetime.now(),
        data_fim=datetime.now() + timedelta(hours=2),
        professor=prof1
    )

    questions = [
        Questao(titulo="Fibonacci", descricao="Implement fibonacci...", peso=10, prova=exam),
        Questao(titulo="Binary Search", descricao="Implement binary search...", peso=10, prova=exam)
    ]

    db.add_all([prof1, prof2] + alunos + [exam] + questions)
    db.commit()

# Run with: python seed_development.py
```

**Benefits**: Faster development setup, reproducible environments

#### 4. Integration Test Suite
**Current**: No automated tests
**Future**: Comprehensive test coverage with pytest

```python
# tests/test_recording_service.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

def test_recording_websocket_connection(client):
    with client.websocket_connect("/ws/1") as websocket:
        # Send auth token
        websocket.send_json({"token": "valid_firebase_token"})

        # Send video chunk
        websocket.send_bytes(b"fake_video_data")

        # Check acknowledgment
        response = websocket.receive_json()
        assert response["status"] == "received"

def test_finalize_recording(client):
    response = client.post("/finalize/1/123")
    assert response.status_code == 200
    assert "file_size" in response.json()
```

**Benefits**: Catch regressions, enable refactoring

#### 5. CI/CD Pipeline
**Current**: Manual deployment
**Future**: Automated testing and deployment

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=app tests/
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to production
        run: |
          docker-compose -f docker-compose.prod.yml build
          docker-compose -f docker-compose.prod.yml up -d
```

**Benefits**: Automated testing, faster deployments, quality gates

---

## Summary

The Test Maker Platform is a sophisticated microservices-based exam proctoring system with comprehensive behavioral monitoring capabilities. Its distributed architecture enables scalability and resilience, while the modular design allows for independent service development and deployment.

**Key Strengths**:
- Comprehensive monitoring (screen, webcam, audio, keystroke, code similarity)
- Scalable WebSocket-based recording with resume capability
- Background analysis with progress tracking
- Multi-language code execution support
- Modern React frontend with real-time capture

**Areas for Improvement**:
- Security (encryption, mTLS, rate limiting)
- Scalability (PostgreSQL migration, message queues, Kubernetes)
- Privacy (consent management, data retention, transparency)
- Developer experience (API docs, tests, CI/CD)

This documentation serves as a comprehensive guide for developers, architects, and stakeholders to understand the system's design, implementation, and future roadmap.

---

**Last Updated**: February 16, 2026
**Maintained By**: TCC Development Team
**Contact**: For questions or contributions, please open an issue on the project repository.
