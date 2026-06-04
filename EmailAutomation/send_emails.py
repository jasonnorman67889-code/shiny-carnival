import csv
import json
import mimetypes
import os
import re
import smtplib
import ssl
import time
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ==================== MASTER SYSTEM SETTINGS ====================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your-email@outlook.com")  # Replace with your Outlook address
APP_PASSWORD = os.getenv("APP_PASSWORD", "xxxx-xxxx-xxxx-xxxx")   # Replace with your 16-character Microsoft App Password
CSV_FILE_PATH = "users.csv"             # Target data matrix source
LOG_FILE_PATH = "email_status_log.csv"  # Real-time production report log
JSON_LOG_FILE_PATH = "email_status_log.json"
SUMMARY_FILE_PATH = "batch_summary.json"
MAX_ATTACHMENT_SIZE_MB = 5
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 2
# ================================================================

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")


def is_valid_email(email):
    return bool(email and EMAIL_REGEX.match(email.strip()))


def format_currency(amount_str):
    try:
        val = float(str(amount_str).replace("$", "").replace(",", "").strip())
        return f"${val:,.2f}"
    except (ValueError, TypeError):
        return str(amount_str).strip() or "N/A"


def format_timestamp(date_str):
    if not date_str:
        return "N/A"

    possible_formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M", "%m/%d/%Y"]
    clean_str = str(date_str).strip()

    for fmt in possible_formats:
        try:
            dt = datetime.strptime(clean_str, fmt)
            return dt.strftime("%B %d, %Y")
        except ValueError:
            continue
    return clean_str


def is_attachment_valid(filepath):
    if not filepath:
        return False, "No attachment specified"
    if not os.path.exists(filepath):
        return False, "File not found"

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    if size_mb > MAX_ATTACHMENT_SIZE_MB:
        return False, f"File too large ({size_mb:.2f} MB)"
    return True, "OK"


def log_status(email, name, status, details=""):
    file_exists = os.path.exists(LOG_FILE_PATH)
    with open(LOG_FILE_PATH, mode="a", newline="", encoding="utf-8") as log_file:
        writer = csv.writer(log_file)
        if not file_exists:
            writer.writerow(["Log_Timestamp", "Recipient_Email", "Recipient_Name", "Delivery_Status", "Error_Details"])

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        writer.writerow([timestamp, email, name, status, details])


def log_status_json(email, name, status, details=""):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "recipient_email": email,
        "recipient_name": name,
        "delivery_status": status,
        "error_details": details,
    }
    with open(JSON_LOG_FILE_PATH, "a", encoding="utf-8") as json_file:
        json_file.write(json.dumps(entry) + "\n")


def log_status_dual(email, name, status, details=""):
    log_status(email, name, status, details)
    log_status_json(email, name, status, details)


def write_summary(total, success, failure):
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_emails": total,
        "successful_deliveries": success,
        "failed_deliveries": failure,
        "log_files": {
            "csv": LOG_FILE_PATH,
            "json": JSON_LOG_FILE_PATH,
        },
    }
    with open(SUMMARY_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=4)
    print(f"[Summary] Written to {SUMMARY_FILE_PATH}")


def connect_with_retry(max_attempts=5, base_delay=2):
    attempt = 0
    context = ssl.create_default_context()

    while attempt < max_attempts:
        try:
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(SENDER_EMAIL, APP_PASSWORD)
            return server
        except Exception as exc:
            attempt += 1
            wait_time = base_delay * (2 ** (attempt - 1))
            print(f"[Retry {attempt}] Connection failed: {exc}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    raise ConnectionError("Max retry attempts reached. Could not connect to SMTP server.")


def send_with_retry(server, sender, recipient, msg, max_attempts=RETRY_ATTEMPTS, base_delay=RETRY_BASE_DELAY):
    attempt = 0

    while attempt < max_attempts:
        try:
            server.sendmail(sender, recipient, msg.as_string())
            return True
        except Exception as exc:
            attempt += 1
            wait_time = base_delay * (2 ** (attempt - 1))
            print(f"[Retry {attempt}] Failed to send {recipient}: {exc}. Retrying in {wait_time}s...")
            time.sleep(wait_time)

    return False


def build_email_message(recipient_email, recipient_name, pdf_filename, invoice_date, amount_due, portal_url):
    msg = MIMEMultipart()
    msg["From"] = f"Billing Department <{SENDER_EMAIL}>"
    msg["To"] = recipient_email
    msg["Subject"] = f"Statement Update for {recipient_name} - {invoice_date}"

    html_content = f"""
    <html>
      <body style="font-family: Calibri, Arial, sans-serif; color: #222222; max-width: 600px; margin: auto;">
        <h2 style="color: #0078d4;">Account Statement Notification</h2>
        <p>Dear {recipient_name},</p>
        <p>Your statement generated on <strong>{invoice_date}</strong> is ready for verification.</p>
        <div style="background-color: #f3f2f1; padding: 15px; border-left: 4px solid #0078d4; margin: 15px 0;">
          <strong>Statement Details:</strong><br>
          Total Balance Due: <span style="font-size: 16px; font-weight: bold; color: #107c41;">{amount_due}</span>
        </div>
        <p>We have securely attached your file <strong>{pdf_filename}</strong> directly to this communication.</p>
        <p>To view your payment history or securely update authentication details, click the link below:</p>
        <p style="margin: 25px 0;"><a href="{portal_url}" style="padding: 12px 24px; background-color: #0078d4; color: white; text-decoration: none; border-radius: 4px; font-weight: bold;">View Electronic Portal</a></p>
        <hr style="border: none; border-top: 1px solid #e1dfdd; margin-top: 30px;">
        <p style="font-size: 11px; color: #605e5c;">This is a system automated transactional message. Reply transmissions are not monitored.</p>
      </body>
    </html>
    """

    msg.attach(MIMEText(html_content, "html"))
    return msg


def send_transactional_batch():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"[Critical Error] Target file tracking system missing at: '{CSV_FILE_PATH}'")
        return

    success_count = 0
    failure_count = 0

    try:
        server = connect_with_retry()
        print("[Connected] SMTP connection established and ready for execution.\n")

        with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            rows = list(reader)
            total_emails = len(rows)

            for index, row in enumerate(rows, start=1):
                recipient_email = str(row.get("email", "")).strip()
                recipient_name = str(row.get("name", "")).strip() or "Customer"
                token = str(row.get("token", "")).strip()
                pdf_filename = str(row.get("pdf_filename", "")).strip()
                invoice_date = format_timestamp(row.get("raw_date", ""))
                amount_due = format_currency(row.get("raw_amount", ""))
                portal_url = f"https://yourapp.com/{token}"

                if not is_valid_email(recipient_email):
                    details = "Invalid email format"
                    print(f"[{index}/{total_emails}] Skipped invalid email: {recipient_email}")
                    log_status_dual(recipient_email, recipient_name, "FAILED", details)
                    failure_count += 1
                    continue

                is_valid, file_message = is_attachment_valid(pdf_filename)
                if not is_valid:
                    print(f"[{index}/{total_emails}] Skipped missing/invalid attachment for {recipient_email}: {file_message}")
                    log_status_dual(recipient_email, recipient_name, "FAILED", file_message)
                    failure_count += 1
                    continue

                msg = build_email_message(recipient_email, recipient_name, pdf_filename, invoice_date, amount_due, portal_url)

                content_type, encoding = mimetypes.guess_type(pdf_filename)
                if content_type is None or encoding is not None:
                    content_type = "application/octet-stream"
                main_type, sub_type = content_type.split("/", 1)

                with open(pdf_filename, "rb") as pdf_file:
                    attachment = MIMEBase(main_type, sub_type)
                    attachment.set_payload(pdf_file.read())
                encoders.encode_base64(attachment)
                attachment.add_header("Content-Disposition", f"attachment; filename=\"{os.path.basename(pdf_filename)}\"")
                msg.attach(attachment)

                if send_with_retry(server, SENDER_EMAIL, recipient_email, msg):
                    print(f"[{index}/{total_emails}] Processed Successfully: {recipient_email}")
                    log_status_dual(recipient_email, recipient_name, "SUCCESS", "Dispatched without exception.")
                    success_count += 1
                else:
                    print(f"[{index}/{total_emails}] Failed delivery after retries: {recipient_email}")
                    log_status_dual(recipient_email, recipient_name, "FAILED", "Retries exhausted")
                    failure_count += 1

                time.sleep(3)

        server.quit()

        print("\n" + "=" * 45)
        print("          AUTOMATION SYSTEM SUMMARY          ")
        print("=" * 45)
        print(f" Total Rows Analyzed    : {total_emails}")
        print(f" Successful Deliveries  : {success_count}")
        print(f" Failed / Dropped Rows  : {failure_count}")
        print(f" Live Tracking Log File : {LOG_FILE_PATH}")
        print("=" * 45)

        write_summary(total_emails, success_count, failure_count)

    except Exception as system_fault:
        print(f"\n[Fatal Event] Run stopped due to core infrastructure failure: {system_fault}")


if __name__ == "__main__":
    send_transactional_batch()
