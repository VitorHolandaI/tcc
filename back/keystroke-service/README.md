# Keystroke Analysis Service

Microservice for keystroke dynamics analysis in the Test Maker Platform.

## Features

- **Typing Metrics Analysis**: Calculates hold time, flight time, and other typing patterns
- **Suspicious Command Detection**: Identifies copy/paste, cut, and other suspicious behaviors
- **Background Processing**: Analyzes keystroke data asynchronously
- **Firebase JWT Authentication**: Secure access for professors only
- **PostgreSQL Storage**: Stores analysis results with status tracking

## Endpoints

### Health Check
```
GET /
```

Returns service status and version.

### Start Keystroke Analysis
```
POST /analyze/{prova_id}/{aluno_id}
Authorization: Bearer <firebase_jwt_token>
```

Starts keystroke analysis for a specific submission. Only accessible by professors.

**Response:**
```json
{
  "message": "Keystroke analysis started in background",
  "status": "processing",
  "total_events": 1234
}
```

### Get Analysis Results
```
GET /analysis/{prova_id}/{aluno_id}
Authorization: Bearer <firebase_jwt_token>
```

Retrieves keystroke analysis results. Only accessible by professors.

**Response (completed):**
```json
{
  "status": "completed",
  "prova_id": 1,
  "aluno_id": 123,
  "typing_metrics": {
    "total_events": 1234,
    "hold_time_avg": 0.123,
    "hold_time_std": 0.045,
    "flight_time_avg": 0.234,
    "flight_time_std": 0.067
  },
  "suspicious_commands": {
    "command_counts": {
      "paste": 5,
      "copy": 3,
      "backspace": 45
    },
    "suspicious_percentage": 12.5,
    "total_commands": 53,
    "avg_manhattan_distance": 3.45,
    "command_sequences": 8
  },
  "completed_at": "2026-02-12T10:30:00"
}
```

## Architecture

### Components

1. **main.py**: FastAPI application with JWT authentication
2. **analyzer.py**: Keystroke dynamics analysis algorithms (from tccRoberto)
3. **report_generator.py**: PDF report generation (from tccRoberto)
4. **database.py**: SQLAlchemy models for analysis results
5. **config.py**: Environment configuration

### Database Schema

**keystroke_analysis** table:
- `id`: Primary key
- `prova_id`: Foreign key to prova
- `aluno_id`: Foreign key to aluno
- `status`: Analysis status (pending, processing, completed, failed)
- `error_message`: Error message if failed
- Typing metrics: hold_time_avg, hold_time_std, flight_time_avg, flight_time_std
- Suspicious commands: command_counts (JSON), suspicious_percentage, total_commands
- Timestamps: created_at, completed_at

## Installation

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (see .env.example):
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the service:
```bash
python main.py
```

### Docker

1. Build the image:
```bash
docker build -t keystroke-service .
```

2. Run the container:
```bash
docker run -d \
  -p 8005:8005 \
  -e DATABASE_URL=postgresql://testmaker:pass@db:5432/testmaker \
  -e FIREBASE_PROJECT_ID=your-project-id \
  -v /path/to/serviceAccountKey.json:/app/serviceAccountKey.json \
  keystroke-service
```

## Environment Variables

See `.env.example` for all available configuration options.

## Dependencies

- **FastAPI**: Web framework
- **SQLAlchemy**: Database ORM
- **Firebase Admin**: JWT authentication
- **NumPy**: Numerical computations
- **SciPy**: Statistical analysis
- **Matplotlib**: Plotting (for report generation)
- **ReportLab**: PDF generation

## Integration

This service integrates with:
- **Main Backend**: Reads keystroke data from submissoes table
- **Firebase**: JWT authentication
- **PostgreSQL**: Stores analysis results

## Security

- JWT token validation via Firebase
- Professor-only access
- No sensitive data in logs
- Temporary files cleaned after analysis

## Analysis Metrics

### Typing Metrics
- **Hold Time**: Duration of key press
- **Flight Time**: Time between key presses
- **Standard Deviation**: Consistency of typing pattern

### Suspicious Commands
- **Copy/Paste Detection**: Identifies clipboard usage
- **Command Sequences**: Groups of suspicious commands
- **Manhattan Distance**: Measures command clustering
- **Suspicious Percentage**: Overall suspicious behavior ratio

## Port

Default port: **8005**

## License

MIT
