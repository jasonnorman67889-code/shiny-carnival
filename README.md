# shiny-carnival

A Flask-based Email Automation Dashboard with session-authenticated admin access, role-aware RBAC, control loop orchestration, observability endpoints, and analytics support.

## Features

- Session-based login with admin/viewer roles
- Admin-only RBAC for logs, exports, compliance reports, and analytics
- Phase 2 control loop status and cycle execution endpoints
- Health and metrics endpoints for observability
- External CSS styling for login and dashboard pages
- GitHub-ready repository with documentation and automated testing support

## Local Run

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app:
   ```bash
   python dashboard.py
   ```
3. Open `http://127.0.0.1:5000` in your browser.

## Demo credentials

- admin / adminpass
- viewer / viewerpass

## GitHub

Published at: https://github.com/jasonnorman67889-code/shiny-carnival
