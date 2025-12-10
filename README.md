# TasteBook

A Flask-based recipe sharing web app.

# Admin creation
By default to login to admin profile use email:admin@example.com password:123456 if db is not present/deleted or new is needed use the following command: python .\scripts\create_admin.py --username yourusername --reset --password "yourpassword"

## Quickstart (Local, development)

1. Create a virtual environment and install dependencies

```powershell
python -m venv venv; .\venv\Scripts\Activate; pip install -r requirements.txt
```

2. Create `.env` from `.env.example` and set environment variables

3. Run the app locally

```powershell
python app.py
```

4. Visit http://127.0.0.1:5000

## Production (Docker)

1. Build and run with Docker Compose

```powershell
docker compose up --build
```

2. App will be available at http://localhost:8000

## Improvements suggested for production

- Use a real database (Postgres in docker-compose or managed RDS)
- Configure S3 or cloud storage for user uploads
- Use Flask-Migrate for DB migrations
- Use Gunicorn or Waitress for WSGI, and use Nginx in front for SSL, static files, caching

## Database migrations (Flask-Migrate)

This project uses `Flask-Migrate` (Alembic) for schema migrations. From PowerShell:

```powershell
# set the FLASK APP for the flask CLI (PowerShell)
$env:FLASK_APP = 'app.py'
# create migrations folder (only once)
flask db init
# create an initial migration
flask db migrate -m "Initial migration"
flask db upgrade
```

If you prefer to use the provided `manage.py` helper, use the Flask CLI commands above or the custom click commands defined in `manage.py`.

## Environment variables

Create a `.env` file in the project root (see `.env.example` if present) containing at minimum:

```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///dev.db
```

## Running in production

Use a WSGI server such as `gunicorn` and configure reverse proxy (Nginx) and TLS. Example (Linux):

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
- Add CSRF protection using Flask-WTF or server-side tokens for APIs
- Set secure session cookie flags and secure headers using Flask-Talisman
- Add full test coverage (pytest) and CI/CD (GitHub Actions) for build and tests
- Configure logging with structured logs and error reporting (Sentry)

## Security notes

- Avoid using `SECRET_KEY` hard-coded. Use a secure secret in environment variables.
- Restrict allowed file upload extensions and enforce size limits (already configured in `app.py`).

