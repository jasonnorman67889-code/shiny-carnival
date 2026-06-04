import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ==================== CONFIGURATION SETTINGS ====================
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SENDER_EMAIL = "your-email@outlook.com"  # Replace with your Outlook address
APP_PASSWORD = "xxxx-xxxx-xxxx-xxxx"    # Replace with your 16-character Microsoft App Password
TEST_RECIPIENT = "your_test_destination@gmail.com"  # Replace with your test recipient address
TEST_FILE = "receipt_101.pdf"           # Must exist in this folder
# ================================================================


def run_diagnostic():
    print("=== LIVE DIAGNOSTIC SYSTEM INITIALIZED ===")

    if not os.path.exists(TEST_FILE):
        with open(TEST_FILE, "w", encoding="utf-8") as f:
            f.write("Mock transaction file generated for system verification.")
        print(f"[*] Created temporary test file: {TEST_FILE}")

    try:
        print(f"1. Establishing secure handshake connection with {SMTP_SERVER} (Port {SMTP_PORT})...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
        server.ehlo()

        print("2. Upgrading stream interface to transport security encryption (STARTTLS)...")
        server.starttls()
        server.ehlo()

        print("3. Passing encrypted credentials to Microsoft Access Controls...")
        server.login(SENDER_EMAIL, APP_PASSWORD)
        print("   [SUCCESS] Authentication passed! Your App Password is valid.")

        print("4. Structuring email envelope and multi-part data stream...")
        msg = MIMEMultipart()
        msg["From"] = f"System Test <{SENDER_EMAIL}>"
        msg["To"] = TEST_RECIPIENT
        msg["Subject"] = "⚙️ Diagnostic Test: Connection Interface Verified"

        body = (
            "<h3>Diagnostic Connection Test Successful</h3>"
            "<p>Your Python environment is authorized to send emails via Microsoft SMTP servers.</p>"
        )
        msg.attach(MIMEText(body, "html"))

        with open(TEST_FILE, "rb") as f:
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", f"attachment; filename=\"{TEST_FILE}\"")
            msg.attach(attachment)

        print("5. Launching execution payload...")
        server.sendmail(SENDER_EMAIL, TEST_RECIPIENT, msg.as_string())
        server.quit()

        print("\n=======================================================")
        print(" SUCCESS: Test complete! Please verify your target inbox.")
        print("=======================================================")

    except Exception as e:
        print("\n❌ CRITICAL PROCESS FAILURE!")
        print(f" Error Engine Type : {type(e).__name__}")
        print(f" Terminal Report    : {str(e)}")
        print("\n[Fix Tip] If error 535 occurs, double-check that Two-Step Verification is enabled and you generated a clean App Password.")


if __name__ == "__main__":
    run_diagnostic()
