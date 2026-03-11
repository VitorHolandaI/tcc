# Firebase Authentication Setup Guide

## Overview
This backend now integrates Firebase Authentication to validate JWT tokens from the frontend.

## Setup Instructions

### 1. Get Your Firebase Project ID

From your frontend `.env` file, you should have `VITE_FIREBASE_PROJECT_ID`. Use this same value.

### 2. Configure Backend Environment

Create or update `/home/vitor/git/tcc/back/.env`:

```bash
# Option 1: Use Project ID (simplest for development)
FIREBASE_PROJECT_ID=your-project-id-here
```

**OR** for production with service account:

```bash
# Option 2: Use Service Account Key File (recommended for production)
FIREBASE_SERVICE_ACCOUNT_PATH=/path/to/serviceAccountKey.json
```

### 3. Get Service Account Key (Optional - for production)

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to **Project Settings** > **Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file securely
6. Update `.env` with the path to this file

### 4. Test the Authentication

Start the backend server:
```bash
cd /home/vitor/git/tcc/back
source env/bin/activate
uvicorn app.main:app --reload
```

The server should start and display:
```
 Firebase initialized with project ID: your-project-id
```

## Protected Endpoints

### Professor Endpoints (require professor authentication)
- `POST /provas/` - Create new prova
- `GET /provas/me/agendadas` - Get my scheduled provas
- `GET /provas/me/passadas` - Get my past provas
- `GET /provas/me/todas` - Get all my provas

### Aluno Endpoints (require student authentication)
- `GET /provas/aluno/agendadas` - Get available scheduled provas
- `GET /provas/aluno/passadas` - Get past provas

### How it works

1. Frontend sends Firebase ID token in Authorization header:
   ```
   Authorization: Bearer <firebase-id-token>
   ```

2. Backend validates token using Firebase Admin SDK

3. Backend extracts user info (email, uid, name) from token

4. Backend checks if user is professor (`@ccc` in email) or aluno

5. Endpoint executes with authenticated user context

## Troubleshooting

### "Invalid token" error
- Ensure frontend is getting fresh tokens with `await user.getIdToken()`
- Check that `FIREBASE_PROJECT_ID` matches between frontend and backend

### "Unauthorized" error
- Token might be expired (Firebase tokens expire after 1 hour)
- Frontend should handle token refresh automatically

### "Forbidden" error
- User type doesn't match endpoint requirement
- Professor trying to access aluno endpoints or vice-versa

## Security Notes

 **IMPORTANT**:
- Never commit `.env` file to git
- Never commit service account JSON files to git
- Use environment variables in production
- Keep service account keys secure
