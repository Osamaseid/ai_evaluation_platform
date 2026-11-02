"""FastAPI application factory for the AI-Powered Programming Evaluation Platform."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from evaluator.api.errors import register_exception_handlers
from evaluator.api.routers import (
    assignments,
    auth,
    evaluations,
    instructors,
    students,
    submissions,
)


def create_app() -> FastAPI:
    """Build and configure the FastAPI backend application."""
    app = FastAPI(
        title="AI Programming Evaluation Platform",
        description="Comprehensive backend API for automated programming assignment evaluation, deterministic grading, and Gemini AI pedagogical code review.",
        version="1.0.0",
        openapi_tags=[
            {"name": "authentication", "description": "User registration, JWT login/logout, profile, and password management"},
            {"name": "students", "description": "Student profiles, submission lists, and evaluation reports"},
            {"name": "instructors", "description": "Instructor administration, students, assignments, rubrics, and manual review overrides"},
            {"name": "assignments", "description": "Programming assignment definitions and test case specifications"},
            {"name": "submissions", "description": "GitHub repository URL and file upload submissions"},
            {"name": "evaluation", "description": "10-step evaluation execution, test results breakdown, AI feedback, and final reports"},
            {"name": "system", "description": "System health and operational monitoring"},
        ],
    )

    # Enable CORS for frontend integration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",
        ],
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register centralized domain exception handlers
    register_exception_handlers(app)

    # Register API routers
    app.include_router(auth.router)
    app.include_router(students.router)
    app.include_router(instructors.router)
    app.include_router(assignments.router)
    app.include_router(submissions.router)
    app.include_router(evaluations.router)

    @app.get("/health", tags=["system"], summary="Application health check")
    def health_check() -> dict:
        """Verify the backend service is operational."""
        return {"status": "healthy", "service": "programming-evaluator-api"}

    # Mount built React frontend SPA if dist folder exists
    import os
    from fastapi.staticfiles import StaticFiles

    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend/dist"))
    if not os.path.exists(dist_dir):
        dist_dir = os.path.abspath(os.path.join(os.getcwd(), "frontend", "dist"))

    if os.path.exists(dist_dir) and os.path.isdir(dist_dir):
        app.mount("/", StaticFiles(directory=dist_dir, html=True), name="static")

    return app


app = create_app()
