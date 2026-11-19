# PromptCraft AI — AI-Powered Website & Application Generator

PromptCraft AI is a web platform that translates natural-language prompts into functional, self-contained web applications with a live interactive studio, syntax-highlighted source code viewer, sandboxed live preview, iteration loop, and one-click ZIP download.

---

## 1. Technology Stack

- **Rendering Architecture**: Server-Side Rendering (SSR) via **Django Template Engine**
- **Frontend**: HTML5, Modern CSS3, Vanilla JavaScript (No React, Vue, or frontend frameworks)
- **Backend**: Python 3.14, Django 6.1
- **Database**: PostgreSQL (with automatic SQLite fallback for local development)
- **AI Engine**: Google Gemini API (`google-genai` SDK / Gemini 2.5)
- **Packaging**: Python native `zipfile` module
- **Authentication**: Django built-in authentication system & CSRF protection

---

## 2. Key Features

1. **Prompt-to-App Engine**: Generates complete, functional, multi-file applications (Attendance Systems, To-Do Planners, Scientific Calculators, Form Builders, Study Planners, Student Management Systems, etc.).
2. **Interactive 3-Pane Studio Workspace**:
   - **File Explorer**: Browse the complete file and folder structure.
   - **Source Code Viewer**: Tabbed inspection of generated HTML, CSS, JavaScript, and Markdown files with line numbering, file size metadata, and one-click copy.
   - **Sandboxed Live Preview**: Embedded iframe with responsive device toggles (Desktop 100%, Tablet 768px, Mobile 375px) and live reload.
3. **Application Modification & Iteration**: Submit follow-up prompts to modify, expand, or restyle an existing application with version history tracking (`v1`, `v2`, ...).
4. **ZIP Project Download**: Download clean, production-ready `.zip` archives of the complete source code directly to your machine.
5. **Project Management Dashboard**: Search, filter by category, monitor status, and manage all generated applications.

---

## 3. Project Architecture & Modular Structure

```
Promptcraft-AI/
├── promptcraft/                     # Core Project Configuration
│   ├── settings.py                  # Database, Apps, Middleware, Security & CSP
│   ├── urls.py                      # Main URL router
│   ├── wsgi.py & asgi.py
│
├── apps/                            # Modular Django Applications
│   ├── accounts/                    # Auth: Signup, Login, Logout, User Profile
│   ├── dashboard/                   # User project listing, metrics & search
│   ├── generator/                   # Prompt submission & generation orchestration
│   └── projects/                    # 3-Pane Studio, File Viewer, Preview & ZIP export
│
├── services/                        # Decoupled Business Logic
│   ├── gemini_service.py            # Google Gemini API client & structured JSON schema
│   ├── code_generator.py            # Multi-file parsing, project scaffolding & DB sync
│   ├── file_manager.py              # Strict path traversal guards & safe disk I/O
│   ├── zip_service.py               # In-memory streaming ZIP generator with secret exclusion
│   └── sandbox_service.py           # Sandboxed preview delivery with strict CSP
│
├── templates/                       # Server-Side Rendered Django Templates
│   ├── base.html                    # Master layout with navbar & message alerts
│   ├── accounts/                    # login.html, signup.html, profile.html
│   ├── dashboard/                   # home.html (landing), index.html (dashboard)
│   ├── generator/                   # new.html (prompt intake & template presets)
│   └── projects/                    # workspace.html (3-pane studio), confirm_delete.html
│
├── static/                          # Static Assets
│   ├── css/                         # base.css, workspace.css
│   └── js/                          # main.js, generator.js, workspace.js
│
└── media/                           # Generated Project Files
    └── generated_projects/<uuid>/   # Safe workspace directory per project
```

---

## 4. Security Architecture

- **No Server-Side Code Execution**: AI-generated code runs exclusively in the user's browser client (HTML5/CSS3/Vanilla JS with `localStorage`). The Django server never executes arbitrary generated code.
- **Sandboxed Live Preview**: Preview iframes enforce `sandbox="allow-scripts allow-forms allow-modals"` and strict `Content-Security-Policy: default-src 'self' 'unsafe-inline' data: blob:; connect-src 'none'; frame-ancestors 'self';`. The sandbox explicitly disallows `allow-same-origin`, isolating generated scripts from PromptCraft AI authentication cookies and sessions.
- **Path Traversal Guards**: Every file read and write operation uses `is_relative_to` / `commonpath` verification against the project's designated directory to prevent `../` attacks.
- **Secret Isolation**: Configuration secrets (`GEMINI_API_KEY`, `SECRET_KEY`, `.env`) are never accessible to workspaces or included in downloadable `.zip` archives.

---

## 5. Quickstart & Installation

### 1. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update `.env` with your settings:
```ini
SECRET_KEY=your-secure-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# PostgreSQL (Set USE_SQLITE_FALLBACK=False when PostgreSQL server is running)
DB_ENGINE=postgresql
DB_NAME=promptcraft_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
USE_SQLITE_FALLBACK=True

# Google Gemini API
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### 2. Apply Database Migrations
```bash
python manage.py migrate
```

### 3. Run Automated Tests
```bash
python manage.py test
```

### 4. Start the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.
