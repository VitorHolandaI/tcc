import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv

load_dotenv()

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")

        if service_account_path and os.path.exists(service_account_path):
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print(" Firebase initialized with service account")
        else:
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            if project_id:
                firebase_admin.initialize_app(options={
                    'projectId': project_id,
                })
                print(f" Firebase initialized with project ID: {project_id}")
            else:
                firebase_admin.initialize_app()
                print(" Firebase initialized with default credentials")

def verify_firebase_token(id_token: str) -> dict:
    """
    Verify Firebase ID token and return decoded token

    Args:
        id_token: Firebase ID token from client

    Returns:
        dict: Decoded token containing user information

    Raises:
        Exception: If token is invalid
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise Exception(f"Invalid token: {str(e)}")

initialize_firebase()
