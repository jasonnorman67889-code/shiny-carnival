# EmailAutomation

This folder contains a simple Outlook SMTP email automation system.

## Files

- `test_email.py` - Verification and diagnostic script for SMTP credentials and attachment delivery.
- `send_emails.py` - Batch processing engine that reads `users.csv` and sends transactional emails with PDF attachments.
- `users.csv` - Recipient data matrix.
- `receipt_101.pdf` - Example PDF attachment.
- `invoice_202.pdf` - Example PDF attachment.
- `.env` - Local credentials and SMTP settings (not committed to source control).
- `email_status_log.csv` - Generated log file for email delivery results.
- `email_status_log.json` - Generated structured log file for monitoring.
- `batch_summary.json` - Generated run summary.

## Setup

1. Copy the folder to your local machine.
2. Install dependencies (optional):
   ```bash
   python -m pip install python-dotenv
   ```
3. Update `.env` with your Outlook SMTP credentials.
4. Confirm `users.csv` contains your recipients and that `receipt_101.pdf` and `invoice_202.pdf` exist.

## Run

1. Verify your connection:
   ```bash
   python test_email.py
   ```
2. If the diagnostic test succeeds, run the batch:
   ```bash
   python send_emails.py
   ```

## Notes

- Use an Outlook app password, not your regular account password.
- `send_emails.py` writes both CSV and JSON logs for each delivery attempt.
- The script also writes `batch_summary.json` after each run.
