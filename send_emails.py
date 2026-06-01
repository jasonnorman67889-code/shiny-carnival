import os
import csv
import ssl
import json
import time
import re
import mimetypes
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from zoneinfo import ZoneInfo

try:
    import requests
except ImportError:
    requests = None

# Optional libs
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    def c_green(s): return Fore.GREEN + s + Style.RESET_ALL
    def c_red(s): return Fore.RED + s + Style.RESET_ALL
    def c_yellow(s): return Fore.YELLOW + s + Style.RESET_ALL
except Exception:
    def c_green(s): return s
    def c_red(s): return s
    def c_yellow(s): return s

# CONFIG (set via .env recommended)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your-email@outlook.com")
APP_PASSWORD = os.getenv("APP_PASSWORD", "xxxx-xxxx-xxxx-xxxx")
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH", "users.csv")
CSV_LOG_FILE = os.getenv("CSV_LOG_FILE", "email_status_log.csv")
JSON_LOG_FILE = os.getenv("JSON_LOG_FILE", "email_status_log.json")
SUMMARY_FILE = os.getenv("SUMMARY_FILE", "batch_summary.json")
MAX_ATTACHMENT_SIZE_MB = float(os.getenv("MAX_ATTACHMENT_SIZE_MB", "5"))
THROTTLE_SECONDS = float(os.getenv("THROTTLE_SECONDS", "3"))
SEND_ALERTS = os.getenv("SEND_ALERTS", "false").lower() in ("1","true","yes")
ALERT_RECIPIENT = os.getenv("ALERT_RECIPIENT", SENDER_EMAIL)
OPT_OUT_CSV_PATH = os.getenv("OPT_OUT_CSV_PATH", "opt_outs.csv")
OPT_OUT_HISTORY_PATH = os.getenv("OPT_OUT_HISTORY_PATH", "opt_out_history.json")
COMPLIANCE_REPORT_PATH = os.getenv("COMPLIANCE_REPORT_PATH", "compliance_report.json")
OUTLOOK_SYNC_ENABLED = os.getenv("OUTLOOK_SYNC_ENABLED", "false").lower() in ("1","true","yes")
GRAPH_ACCESS_TOKEN = os.getenv("GRAPH_ACCESS_TOKEN", "")
DRY_RUN = os.getenv("DRY_RUN", "false").lower() in ("1","true","yes")
OUTLOOK_DRY_RUN = os.getenv("OUTLOOK_DRY_RUN", "false").lower() in ("1","true","yes")
STRICT_REGIONAL_SEND_WINDOWS = os.getenv("STRICT_REGIONAL_SEND_WINDOWS", "false").lower() in ("1","true","yes")
REGION_DEFAULT = os.getenv("REGION_DEFAULT", "USA")
REGION_CONFIG = {
    "USA": {
        "timezone": "America/New_York",
        "law": "CAN-SPAM",
        "send_hour": 9,
        "channels": ["email"],
        "footer": "You may unsubscribe at any time using the link below.",
        "tone": "direct"
    },
    "AUSTRALIA": {
        "timezone": "Australia/Sydney",
        "law": "Spam Act",
        "send_hour": 8,
        "channels": ["sms", "email"],
        "footer": "You can unsubscribe from these alerts at any time.",
        "tone": "casual"
    },
    "EUROPE": {
        "timezone": "Europe/Paris",
        "law": "GDPR",
        "send_hour": 18,
        "channels": ["email", "whatsapp"],
        "footer": "You have the right to withdraw consent and unsubscribe at any time.",
        "tone": "formal"
    },
    "UK": {
        "timezone": "Europe/London",
        "law": "UK GDPR/PECR",
        "send_hour": 19,
        "channels": ["email", "push"],
        "footer": "You can unsubscribe or change preferences at any time.",
        "tone": "polite"
    }
}

EMAIL_REGEX = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

def format_currency(amount_str):
    try:
        val = float(str(amount_str).replace('$','').replace(',','').strip())
        return f"${val:,.2f}"
    except Exception:
        return amount_str

def format_timestamp(date_str):
    if not date_str:
        return "N/A"
    possible_formats = ["%Y-%m-%d %H:%M:%S","%Y-%m-%d","%m/%d/%Y %H:%M","%m/%d/%Y"]
    clean = date_str.strip()
    for fmt in possible_formats:
        try:
            dt = datetime.strptime(clean, fmt)
            return dt.strftime("%B %d, %Y")
        except ValueError:
            continue
    return date_str

def is_valid_email(email):
    return EMAIL_REGEX.match(email) is not None

def get_region_info(region_name):
    if not region_name:
        region_name = REGION_DEFAULT
    region_key = region_name.strip().upper()
    return REGION_CONFIG.get(region_key, REGION_CONFIG.get(REGION_DEFAULT, {}))

def local_time_for_region(region_name):
    region = get_region_info(region_name)
    tz_name = region.get("timezone")
    try:
        zone = ZoneInfo(tz_name)
        return datetime.now(zone)
    except Exception:
        return datetime.now()

def is_within_send_window(region_name):
    region = get_region_info(region_name)
    hour = region.get("send_hour")
    if hour is None:
        return True
    local = local_time_for_region(region_name)
    return local.hour == hour

def personalize_subject(region_name, recipient_name, invoice_date):
    region = get_region_info(region_name)
    tone = region.get("tone", "direct")
    if region_name and region_name.strip().upper() == "UK":
        return f"{recipient_name}, your invoice is ready - exclusive offer included"
    if region_name and region_name.strip().upper() == "AUSTRALIA":
        return f"{recipient_name}, your invoice is ready - special deal for you"
    if region_name and region_name.strip().upper() == "EUROPE":
        return f"Your invoice is ready - offer available for {recipient_name}"
    return f"Your Invoice is Ready - {invoice_date}"

def compliance_check(region_name, email, html_content):
    issues = []
    region = get_region_info(region_name)
    if "unsubscribe" not in html_content.lower():
        issues.append("Missing unsubscribe link")
    if "sender" not in html_content.lower() and region.get("law") in ("CAN-SPAM", "Spam Act"):
        issues.append("Missing sender identity information")
    if region.get("law") == "GDPR" and "consent" not in html_content.lower():
        issues.append("Missing GDPR consent language")
    if region.get("law") == "UK GDPR/PECR" and "preferences" not in html_content.lower():
        issues.append("Missing UK PECR preferences language")
    return issues

def apply_compliance_footer(region_name, html_content, unsubscribe_url):
    region = get_region_info(region_name)
    footer = region.get("footer", "You may unsubscribe anytime.")
    if "unsubscribe" not in html_content.lower():
        html_content += f'<p style="font-size:12px;color:#6b7280;">{footer} <a href="{unsubscribe_url}">unsubscribe</a>.</p>'
    return html_content

def is_attachment_valid(filepath):
    if not os.path.exists(filepath):
        return False, "File not found"
    size_mb = os.path.getsize(filepath) / (1024*1024)
    if size_mb > MAX_ATTACHMENT_SIZE_MB:
        return False, f"File too large ({size_mb:.2f} MB)"
    return True, "OK"

def connect_secure():
    context = ssl.create_default_context()
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=15)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(SENDER_EMAIL, APP_PASSWORD)
    return server

def connect_with_retry(max_attempts=5, base_delay=2):
    attempt = 0
    while attempt < max_attempts:
        try:
            return connect_secure()
        except Exception as e:
            attempt += 1
            wait = base_delay * (2 ** (attempt-1))
            print(c_yellow(f"[Retry {attempt}] Connection failed: {e}. Waiting {wait}s..."))
            time.sleep(wait)
    raise ConnectionError("Max retry attempts reached for SMTP connection.")

def send_with_retry(server, sender, recipient, msg, max_attempts=3, base_delay=2):
    attempt = 0
    while attempt < max_attempts:
        try:
            server.sendmail(sender, recipient, msg.as_string())
            return True, ""
        except Exception as e:
            attempt += 1
            wait = base_delay * (2 ** (attempt-1))
            print(c_yellow(f"[Retry {attempt}] Failed to send {recipient}: {e}. Waiting {wait}s..."))
            time.sleep(wait)
    return False, f"Retries exhausted: {e}"

def log_status_dual(email, name, status, details="", region=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # CSV
    file_exists = os.path.exists(CSV_LOG_FILE)
    with open(CSV_LOG_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Log_Timestamp","Recipient_Email","Recipient_Name","Region","Delivery_Status","Error_Details"])
        writer.writerow([timestamp, email, name, region or "", status, details])
    # JSON (line-delimited)
    entry = {"timestamp": timestamp, "recipient_email": email, "recipient_name": name, "region": region, "delivery_status": status, "error_details": details}
    with open(JSON_LOG_FILE, "a", encoding="utf-8") as jf:
        jf.write(json.dumps(entry) + "\n")

def write_summary(total, success, failure):
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_emails": total,
        "successful_deliveries": success,
        "failed_deliveries": failure,
        "log_files": {"csv": CSV_LOG_FILE, "json": JSON_LOG_FILE}
    }
    with open(SUMMARY_FILE, "w", encoding="utf-8") as sf:
        json.dump(summary, sf, indent=2)
    print(f"[Summary] Written to {SUMMARY_FILE}")
    return summary

def send_alert_with_summary(summary):
    try:
        server = connect_with_retry()
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = ALERT_RECIPIENT
        msg["Subject"] = "Batch Completion Alert - Email Automation"
        body = f"Batch complete. Total: {summary['total_emails']}, Success: {summary['successful_deliveries']}, Failed: {summary['failed_deliveries']}"
        msg.attach(MIMEText(body, "plain"))
        with open(SUMMARY_FILE, "rb") as f:
            attachment = MIMEBase("application", "json")
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", 'attachment; filename="batch_summary.json"')
            msg.attach(attachment)
        server.sendmail(SENDER_EMAIL, ALERT_RECIPIENT, msg.as_string())
        server.quit()
        print("[Alert] Summary email sent.")
    except Exception as e:
        print(f"[Alert Error] Could not send alert: {e}")

def load_opt_outs():
    if not os.path.exists(OPT_OUT_CSV_PATH):
        return set()
    with open(OPT_OUT_CSV_PATH, "r", encoding="utf-8") as f:
        return {line.strip().lower() for line in f if line.strip()}


def log_opt_out(email):
    email = email.strip().lower()
    if not email:
        return

    if not os.path.exists(OPT_OUT_CSV_PATH):
        with open(OPT_OUT_CSV_PATH, "w", encoding="utf-8") as f:
            f.write(email + "\n")
    else:
        existing = load_opt_outs()
        if email not in existing:
            with open(OPT_OUT_CSV_PATH, "a", encoding="utf-8") as f:
                f.write(email + "\n")

    history = []
    if os.path.exists(OPT_OUT_HISTORY_PATH):
        with open(OPT_OUT_HISTORY_PATH, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.append({"email": email, "timestamp": datetime.now().isoformat()})
    with open(OPT_OUT_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)


def load_all_recipients():
    if not os.path.exists(CSV_FILE_PATH):
        return []
    with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def generate_compliance_report(total, success, failure):
    opt_outs = sorted(load_opt_outs())
    recipients = load_all_recipients()
    region_totals = {}
    for row in recipients:
        region = row.get("region", REGION_DEFAULT).strip().upper() or REGION_DEFAULT
        region_totals.setdefault(region, {"recipient_count": 0, "law": get_region_info(region).get("law"), "timezone": get_region_info(region).get("timezone"), "channels": get_region_info(region).get("channels", [])})
        region_totals[region]["recipient_count"] += 1

    report = {
        "timestamp": datetime.now().isoformat(),
        "total_emails": total,
        "successful_deliveries": success,
        "failed_deliveries": failure,
        "opt_out_count": len(opt_outs),
        "opt_out_list": opt_outs,
        "regional_audit": [
            {
                "region": region,
                "law": info["law"],
                "timezone": info["timezone"],
                "channels": info["channels"],
                "recipient_count": info["recipient_count"],
                "proof": [
                    "Consent log",
                    "Unsubscribe record",
                    "Sender identity check",
                    "Footer compliance"
                ],
                "status": "Pending review"
            }
            for region, info in region_totals.items()
        ]
    }
    with open(COMPLIANCE_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=4)
    print(f"[Compliance] Report written to {COMPLIANCE_REPORT_PATH}")
    return report


def update_outlook_contact_unsubscribed(contact_id):
    if OUTLOOK_DRY_RUN:
        print(c_yellow(f"[Outlook Sync - DRY_RUN] Would mark contact {contact_id} as Unsubscribed."))
        return True

    if not OUTLOOK_SYNC_ENABLED:
        return False
    if not GRAPH_ACCESS_TOKEN:
        print(c_yellow("[Outlook Sync] GRAPH_ACCESS_TOKEN is not configured."))
        return False
    if requests is None:
        print(c_red("[Outlook Sync] requests library is not installed."))
        return False

    url = f"https://graph.microsoft.com/v1.0/me/contacts/{contact_id}"
    headers = {
        "Authorization": f"Bearer {GRAPH_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"categories": ["Unsubscribed"]}
    response = requests.patch(url, headers=headers, json=payload)
    if response.ok:
        print(c_green(f"[Outlook Sync] Contact {contact_id} marked Unsubscribed."))
        return True
    print(c_red(f"[Outlook Sync] Failed to update contact {contact_id}: {response.status_code} {response.text}"))
    return False


def send_transactional_batch():
    if not os.path.exists(CSV_FILE_PATH):
        print(f"[Critical Error] Missing CSV: {CSV_FILE_PATH}")
        return

    rows = []
    with open(CSV_FILE_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    opt_outs = load_opt_outs()
    total = len(rows)
    success_count = 0
    failure_count = 0

    try:
        server = connect_with_retry()
        for idx, row in enumerate(rows, start=1):
            recipient_email = row.get("email", "").strip()
            recipient_name = row.get("name", "").strip() or "Customer"
            region_name = row.get("region", REGION_DEFAULT).strip().upper() or REGION_DEFAULT
            region = get_region_info(region_name)
            token = row.get("token", "").strip()
            pdf_filename = row.get("pdf_filename", "").strip()
            invoice_date = format_timestamp(row.get("raw_date", ""))
            amount_due = format_currency(row.get("raw_amount", ""))
            channel = row.get("channel", "email").strip().lower() or "email"

            if recipient_email.lower() in opt_outs:
                msg = "Recipient has opted out"
                print(c_yellow(f"[{idx}/{total}] Skipped opted-out recipient: {recipient_email} ({region_name})"))
                log_status_dual(recipient_email, recipient_name, "SKIPPED", msg, region=region_name)
                contact_id = row.get("contact_id", "").strip()
                if contact_id:
                    update_outlook_contact_unsubscribed(contact_id)
                continue

            if not is_valid_email(recipient_email):
                msg = "Invalid email format"
                print(c_red(f"[{idx}/{total}] Skipped {recipient_email} -> {msg}"))
                log_status_dual(recipient_email, recipient_name, "FAILED", msg, region=region_name)
                failure_count += 1
                continue

            if STRICT_REGIONAL_SEND_WINDOWS and not is_within_send_window(region_name):
                local = local_time_for_region(region_name)
                msg = f"Outside scheduled send window for {region_name} ({local.strftime('%H:%M %Z')})"
                print(c_yellow(f"[{idx}/{total}] Deferred {recipient_email}: {msg}"))
                log_status_dual(recipient_email, recipient_name, "DEFERRED", msg, region=region_name)
                continue

            if not DRY_RUN:
                valid_attach, reason = is_attachment_valid(pdf_filename)
                if not valid_attach:
                    print(c_red(f"[{idx}/{total}] Skipped {recipient_email} -> {reason}"))
                    log_status_dual(recipient_email, recipient_name, "FAILED", reason, region=region_name)
                    failure_count += 1
                    continue

            portal_url = f"https://yourapp.com/{token}"
            unsubscribe_url = f"https://yourapp.com/unsubscribe?email={recipient_email}"
            subject = personalize_subject(region_name, recipient_name, invoice_date)
            base_html = f"""
                <html>
                <body style="font-family: Calibri, Arial, sans-serif; color: #222; max-width:600px;margin:auto;">
                  <h2 style="color:#0078d4">Account Statement Notification</h2>
                  <p>Dear {recipient_name},</p>
                  <p>Your statement generated on <strong>{invoice_date}</strong> is ready.</p>
                  <div style="background:#f3f2f1;padding:12px;border-left:4px solid #0078d4;">
                    <strong>Statement Details:</strong><br>
                    Total Balance Due: <span style="font-weight:bold;color:#107c41">{amount_due}</span>
                  </div>
                  <p>Attached: <strong>{pdf_filename}</strong></p>
                  <p><a href="{portal_url}" style="background:#0078d4;color:#fff;padding:10px 18px;text-decoration:none;border-radius:4px;">View Electronic Portal</a></p>
                  <p style="margin-top:18px;font-size:14px;">If you no longer wish to receive these notifications, <a href="{unsubscribe_url}">unsubscribe here</a>.</p>
                  <hr>
                  <p style="font-size:11px;color:#605e5c;">Automated transactional message. Replies not monitored.</p>
                </body>
                </html>
                """
            html = apply_compliance_footer(region_name, base_html, unsubscribe_url)
            compliance_issues = compliance_check(region_name, recipient_email, html)
            if compliance_issues:
                print(c_yellow(f"[{idx}/{total}] Compliance issues for {recipient_email} ({region_name}): {', '.join(compliance_issues)}"))

            try:
                msg = MIMEMultipart()
                msg["From"] = f"Billing Department <{SENDER_EMAIL}>"
                msg["To"] = recipient_email
                msg["Subject"] = subject
                msg.attach(MIMEText(html, "html"))

                if channel != "email":
                    print(c_yellow(f"[{idx}/{total}] Note: channel set to {channel}, email body will still be delivered."))

                if not DRY_RUN:
                    ctype, encoding = mimetypes.guess_type(pdf_filename)
                    if ctype is None:
                        ctype = "application/octet-stream"
                    maintype, subtype = ctype.split("/",1)
                    with open(pdf_filename, "rb") as pf:
                        attachment = MIMEBase(maintype, subtype)
                        attachment.set_payload(pf.read())
                    encoders.encode_base64(attachment)
                    attachment.add_header("Content-Disposition", f'attachment; filename="{os.path.basename(pdf_filename)}"')
                    msg.attach(attachment)

                if DRY_RUN:
                    ok, err = True, "DRY_RUN simulated"
                else:
                    ok, err = send_with_retry(server, SENDER_EMAIL, recipient_email, msg)
                if ok:
                    print(c_green(f"[{idx}/{total}] Sent: {recipient_email} ({region_name})"))
                    log_status_dual(recipient_email, recipient_name, "SUCCESS", "Delivered", region=region_name)
                    success_count += 1
                else:
                    print(c_red(f"[{idx}/{total}] Failed: {recipient_email} -> {err}"))
                    log_status_dual(recipient_email, recipient_name, "FAILED", err, region=region_name)
                    failure_count += 1

            except Exception as row_err:
                print(c_red(f"[{idx}/{total}] Skipped Row Error: {recipient_email} -> {row_err}"))
                log_status_dual(recipient_email, recipient_name, "FAILED", str(row_err), region=region_name)
                failure_count += 1

            time.sleep(THROTTLE_SECONDS)

        server.quit()

    except Exception as system_err:
        print(c_red(f"[Fatal Event] Run stopped due to: {system_err}"))
        return

    summary = write_summary(total, success_count, failure_count)
    generate_compliance_report(total, success_count, failure_count)
    if SEND_ALERTS:
        send_alert_with_summary(summary)

    print("\n" + "="*45)
    print("          AUTOMATION SYSTEM SUMMARY          ")
    print("="*45)
    print(f" Total Rows Analyzed    : {total}")
    print(f" Successful Deliveries  : {success_count}")
    print(f" Failed / Dropped Rows  : {failure_count}")
    print(f" Live Tracking CSV      : {CSV_LOG_FILE}")
    print(f" Live Tracking JSON     : {JSON_LOG_FILE}")
    print("="*45)

if __name__ == "__main__":
    send_transactional_batch()
