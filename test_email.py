import os
import ssl
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Optional: load environment variables from a .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ==================== CONFIGURATION SETTINGS ====================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your-email@outlook.com")
APP_PASSWORD = os.getenv("APP_PASSWORD", "xxxx-xxxx-xxxx-xxxx")
TEST_RECIPIENT = os.getenv("TEST_RECIPIENT", "your_test_destination@gmail.com")
TEST_FILE = os.getenv("TEST_FILE", "receipt_101.pdf")
# ================================================================


def connect_secure():
    """Create an SMTP connection with TLS certificate verification."""
    context = ssl.create_default_context()
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    return server


def run_diagnostic():
    print("=== LIVE DIAGNOSTIC SYSTEM INITIALIZED ===")

    # Generate mock attachment if it doesn't exist yet (simple text PDF placeholder)
    if not os.path.exists(TEST_FILE):
        try:
            with open(TEST_FILE, "wb") as f:
                f.write(b"%PDF-1.1\n%\xe2\xe3\xcf\xd3\n")
            print(f"[*] Created temporary test file: {TEST_FILE}")
        except Exception as e:
            print(f"Could not create test file {TEST_FILE}: {e}")

    try:
        print(f"1. Connecting to {SMTP_SERVER} (Port {SMTP_PORT})...")
        server = connect_secure()

        print("4. Structuring email envelope and multi-part data stream...")
        msg = MIMEMultipart()
        msg['From'] = f"System Test <{SENDER_EMAIL}>"
        msg['To'] = TEST_RECIPIENT
        msg['Subject'] = "\u2699\ufe0f Diagnostic Test: Connection Interface Verified"

        body = "<h3>Diagnostic Connection Test Successful</h3><p>Your Python environment is authorized to send emails via Microsoft SMTP servers.</p>"
        msg.attach(MIMEText(body, 'html'))

        # Append attachment to stream
        with open(TEST_FILE, 'rb') as f:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(TEST_FILE)}"')
            msg.attach(attachment)

        print("5. Sending test email...")
        server.sendmail(SENDER_EMAIL, TEST_RECIPIENT, msg.as_string())
        server.quit()

        print("\n=======================================================")
        print(" SUCCESS: Test complete! Please verify your target inbox.")
        print("=======================================================")

    except Exception as e:
        print("\n\u274c CRITICAL PROCESS FAILURE!")
        print(f" Error Engine Type : {type(e).__name__}")
        print(f" Terminal Report    : {str(e)}")
        print("\n[Fix Tip] If error 535 occurs, double-check that Two-Step Verification is ON and you generated an App Password, then set APP_PASSWORD in your environment.")


if __name__ == "__main__":
    run_diagnostic()
