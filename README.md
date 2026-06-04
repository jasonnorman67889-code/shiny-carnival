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

## Testing

1. Install test dependencies (if needed):
   ```bash
   pip install -r requirements.txt
   ```
2. Run the test suite:
   ```bash
   pytest
   ```

## Deployment

- Ensure `FLASK_SECRET_KEY` is set for production security.
- Configure environment variables for any paths or secrets used by the app.
- Use a WSGI server such as Gunicorn for production hosting:
   ```bash
   gunicorn --bind 0.0.0.0:8000 dashboard:app
   ```
- Optionally deploy to a platform that supports Python web apps, such as Heroku, Azure App Service, or a containerized environment.

### Azure App Service

1. Add `gunicorn` to `requirements.txt`.
2. Deploy the app files to Azure App Service using GitHub integration, local Git, or zip deployment.
3. Set the App Service startup command to:
   ```bash
   gunicorn --bind 0.0.0.0:$PORT dashboard:app
   ```
4. Configure environment variables in App Service settings:
   - `FLASK_SECRET_KEY`
   - any file path or secrets the app requires

## GitHub

Published at: https://github.com/jasonnorman67889-code/shiny-carnival
