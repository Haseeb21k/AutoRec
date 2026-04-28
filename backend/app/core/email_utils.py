import os
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Fallback to localhost if not provided
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip('/')

def get_gmail_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    
    # 1. Try to load from environment variable (For Railway Production)
    token_json_str = os.getenv("GMAIL_TOKEN_JSON")
    if token_json_str:
        try:
            token_info = json.loads(token_json_str)
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
        except Exception as e:
            print(f"Error parsing GMAIL_TOKEN_JSON: {e}")

    # 2. Fallback to local file (For Local Development)
    if not creds:
        token_path = os.path.join(os.path.dirname(__file__), '..', '..', 'token.json')
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    # If there are no (valid) credentials available, try to refresh them
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("No valid Gmail API credentials found. Please run generate_gmail_token.py first locally, or set GMAIL_TOKEN_JSON in production.")
            
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        return service
    except Exception as error:
        print(f'An error occurred connecting to Gmail API: {error}')
        return None

def send_invite_email(to_email: str, token: str):
    """
    Sends an HTML invitation email with the setup link via Gmail API.
    """
    try:
        service = get_gmail_service()
        if not service:
            raise Exception("Failed to initialize Gmail service.")

        # 1. Setup Message
        msg = MIMEMultipart()
        msg['To'] = to_email
        msg['Subject'] = "Invitation to AutoRec System"
        # msg['From'] is optional and will default to the authenticated user

        # 2. Create Link
        # Note: This points to your Frontend URL (set via env var)
        link = f"{FRONTEND_URL}/setup-password?token={token}"
        
        # 3. Email Body (HTML)
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #4F46E5;">Welcome to AutoRec</h2>
                <p>You have been invited to join the Financial Reconciliation Platform.</p>
                <br>
                <a href="{link}" style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px;">Set Password</a>
                <br><br>
                <p>Or copy: {link}</p>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, 'html'))

        # Encode the message in base64url format
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
        body = {'raw': raw_message}

        # 4. Send via Gmail API over HTTP
        print(f"Sending email to {to_email} via Gmail API...")
        message = service.users().messages().send(userId='me', body=body).execute()
        
        print(f"Success: Email successfully sent to {to_email}. Message Id: {message['id']}")

    except Exception as e:
        print(f"Error: Failed to send email via Gmail API: {str(e)}")