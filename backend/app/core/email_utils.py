import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")   
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_invite_email(to_email: str, token: str):
    """
    Sends an HTML invitation email with the setup link.
    """
    try:
        print(f"Connecting to SMTP server as {SMTP_USER}...")
        
        # 1. Setup Message
        msg = MIMEMultipart()
        msg['From'] = f"AutoRec Admin <{SMTP_USER}>"
        msg['To'] = to_email
        msg['Subject'] = "Invitation to AutoRec System"

        # 2. Create Link
        # Note: This points to your Frontend URL
        link = f"http://localhost:5173/setup-password?token={token}"
        
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

        # 4. Send via SMTP
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email successfully sent to {to_email}")

    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")