# WebView App Generator

Multi-service FastAPI application that generates Android WebView app bundles (APK/AAB) for user-supplied URLs. Includes authentication, role-based authorization, keystore approvals, and a background builder that simulates Android builds.

## Features
- **User authentication & roles**: JWT-based login/registration with `admin` and `user` roles.
- **App projects**: Create, list, view, update, and upload icons for WebView-based Android apps (package name, URL, SDK targets, versioning).
- **Keystore lifecycle**: Per-project keystore generation with admin-gated download approvals and secure file serving when allowed.
- **Build jobs**: Trigger build jobs per app, monitor status/logs, and download simulated APK/AAB artifacts after success.
- **Admin workflows**: Approve or reject keystore download requests via dedicated admin endpoints and pages.
- **Web UI**: Basic Jinja2 templates for login, registration, dashboard, app detail, and admin keystore request review.

## Architecture
- **webapp (FastAPI)**: Serves APIs and HTML pages, manages JWT auth, CRUD for app projects/keystores/builds. Uses SQLAlchemy ORM and Alembic migrations against MySQL. Static assets and templates live under `webapp/app/static` and `webapp/app/templates`.
- **builder (worker)**: Polling worker that processes pending `BuildJob` records, simulates Android project scaffolding, writes dummy APK/AAB artifacts, and updates job logs/statuses.
- **database**: MySQL 8 instance shared by both services.
- **Shared volumes**: `/data/keystores`, `/data/artifacts`, and `/data/icons` mounted to persist generated keystores, build outputs, and uploaded icons.

## Project layout
```
.
├── docker-compose.yml
├── alembic/                # Alembic migration environment and versions
├── webapp/                 # FastAPI service (APIs, templates, static assets)
│   ├── app/
│   │   ├── main.py         # App factory & router registration
│   │   ├── models.py       # SQLAlchemy models for users, projects, keystores, builds, requests
│   │   ├── auth.py         # JWT utilities and password hashing helpers
│   │   ├── routers/        # Auth, app, keystore, admin, and build routes
│   │   ├── templates/      # Jinja2 templates (login, register, dashboard, app detail, admin)
│   │   └── static/         # CSS and other assets
│   └── requirements.txt
└── builder/                # Background build worker
    ├── main.py             # Polling loop to process pending BuildJobs
    └── requirements.txt
```

## Running with Docker Compose
1. Ensure Docker and Docker Compose are installed.
2. Build and start the stack:
   ```bash
   docker-compose up --build
   ```
3. The FastAPI app is available on [http://localhost:8000](http://localhost:8000). MySQL is exposed on port 3306 for debugging.
4. Data volumes are stored under `./data/keystores`, `./data/artifacts`, and `./data/icons` on the host.

## Configuration
Environment variables used in `docker-compose.yml` (override as needed):
- `DATABASE_URL`: MySQL connection string for SQLAlchemy.
- `JWT_SECRET`, `JWT_ALGORITHM`: JWT signing configuration for the webapp.
- `KEYSTORE_DIR`, `ARTIFACT_DIR`, `ICON_DIR`: Mounted storage paths for keystores, build artifacts, and uploaded icons.

## Database migrations
Alembic is configured at the repository root. The webapp container runs with SQLAlchemy models creating tables on startup; you can run migrations locally with:
```bash
alembic upgrade head
```
Ensure `DATABASE_URL` is set in the environment when running Alembic commands.

## Development notes
- The builder currently **simulates** Android project generation and signing; replace the TODOs with real Gradle/Android SDK commands when wiring to actual build tooling.
- Keystore generation is stubbed and stores passwords in plain text pending integration with secure storage/encryption.
