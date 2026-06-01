# EmailAutomation (Email batch sender)

Files in this folder:

- `test_email.py` : Diagnostic/test script to verify SMTP credentials and send a single test email.
- `send_emails.py` : Batch processing engine that reads `users.csv` and sends transactional emails with attachments.
- `users.csv` : Recipient data matrix (email,name,token,pdf_filename,region,channel,raw_date,raw_amount).
- `opt_outs.csv` : Self-service unsubscribe list.
- `opt_out_history.json` : Timestamped opt-out event history.
- `email_status_log.csv` / `email_status_log.json` : Generated logs (created at runtime).
- `batch_summary.json` : Generated summary after each run.
- `compliance_report.json` : Latest generated compliance audit report.
- `.env` : Environment variables (SMTP credentials). DO NOT COMMIT this file to source control.
- `receipt_101.pdf`, `invoice_202.pdf` : Example placeholder attachments.

Setup

1. (Optional) Create a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

1. Install optional dependencies:

```powershell
python -m pip install python-dotenv colorama
```

1. Edit `.env` and set `SENDER_EMAIL` and `APP_PASSWORD` (use an App Password if your account requires it).

Run

1. Run the diagnostic test:

```powershell
python test_email.py
```

1. If successful, run the batch:

```powershell
python send_emails.py
```

Dashboard

1. Install dashboard dependencies:

```powershell
python -m pip install -r requirements.txt
```

1. Set dashboard passwords in `.env` if desired (optional):

```text
DASHBOARD_ADMIN_PASS=adminpass
DASHBOARD_VIEWER_PASS=viewerpass
```

1. Start the dashboard:

```powershell
python dashboard.py
```

1. Open the dashboard in your browser:

```text
http://127.0.0.1:5000/
```

Additional features:

- Unsubscribe portal: `http://127.0.0.1:5000/unsubscribe`
- Opt-out trend API: `/opt-outs` (admin only)
- Compliance report: `/compliance-report` (admin only)
- Transformation insights: `/transformation-insights` (admin only)
- Corporate strategy nexus: `/strategy-nexus` (admin only)
- Transcendent intelligence core: `/transcendent-core` (admin only)
- Legacy preservation framework: `/legacy-framework` (admin only)
- Multiversal simulation engine: `/multiversal-simulations` (admin only)
- Eternal governance continuum: `/governance-continuum` (admin only)
- Singularity governance matrix: `/singularity-matrix` (admin only)
- Infinite continuity engine: `/continuity-engine` (admin only)
  - Cosmic‑Eternal Nexus: `/cosmic-nexus` (admin only)
  - Omniversal strategy continuum: `/omniversal-continuum` (admin only)

Default credentials:

- admin / adminpass
- viewer / viewerpass

Admin users can access `/logs`, `/export/csv`, `/export/json`, `/opt-outs`, and `/compliance-report`.
Viewer users can still see only dashboard summaries and are blocked from detailed logs, exports, and compliance endpoints.

Notes & Safety

- Keep `.env` private. Do not commit credentials.
- Ensure you have permission to email the recipients listed in `users.csv`.
- Use `SEND_ALERTS=true` in `.env` to receive a completion alert (will attach `batch_summary.json`).
- For region orchestration, add `region` and `channel` fields to `users.csv`.
- Set `STRICT_REGIONAL_SEND_WINDOWS=true` in `.env` to enforce local send windows for each region.

Troubleshooting

- If authentication fails, create an App Password in your Microsoft account and set `APP_PASSWORD` in `.env`.
- If emails are blocked, verify network firewall and SMTP access for outbound port 587.
- To enable Outlook contact sync for unsubscribes, set `OUTLOOK_SYNC_ENABLED=true` and provide `GRAPH_ACCESS_TOKEN` in `.env`.
  - For safe testing without contacting Microsoft Graph, also set `OUTLOOK_DRY_RUN=true` to simulate contact updates.
