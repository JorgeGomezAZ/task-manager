from fastapi import FastAPI

from app.routers import auth, tasks

app = FastAPI(
    title="Task Manager API",
    description="A task management API with JWT authentication.",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/", tags=["health"])
def health_check():
    return {"status": "ok"}
