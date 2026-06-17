# task-manager

A RESTful task management API built with **FastAPI**, **SQLAlchemy**, **Alembic**, and **JWT authentication**.

## Features

- **Authentication**: Register and login with email/password. Passwords hashed with `passlib[bcrypt]`. JWTs issued via `python-jose`.
- **Task CRUD**: Create, list, update, and delete tasks. All task routes are protected and scoped to the authenticated user.
- **Database**: PostgreSQL (default) with SQLAlchemy ORM. Schema managed with Alembic migrations.
- **Interactive docs**: Available at `/docs` (Swagger UI).

## Project Structure

```
task-manager/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── database.py       # SQLAlchemy engine & session
│   ├── models.py         # User and Task ORM models
│   ├── schemas.py        # Pydantic request/response schemas
│   ├── security.py       # Password hashing & JWT utilities
│   ├── dependencies.py   # get_current_user dependency
│   └── routers/
│       ├── auth.py       # POST /auth/register, POST /auth/login
│       └── tasks.py      # GET/POST/PUT/DELETE /tasks
├── alembic/              # Alembic migration environment
│   └── versions/         # Migration scripts
├── tests/
│   └── test_api.py       # Integration tests (pytest)
├── alembic.ini
└── requirements.txt
```

## Quick Start

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure PostgreSQL
export DATABASE_URL=******localhost:5432/task_manager

# 4. Run the Alembic migration
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** to explore and test the API interactively.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/register` | — | Register a new user |
| POST | `/auth/login` | — | Login and receive a JWT |
| GET | `/tasks/` | ✅ | List all tasks for the current user |
| POST | `/tasks/` | ✅ | Create a new task |
| PUT | `/tasks/{id}` | ✅ | Update a task |
| DELETE | `/tasks/{id}` | ✅ | Delete a task |

## Running Tests

```bash
pytest tests/ -v
```
