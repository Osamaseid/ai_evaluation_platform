"""FastAPI application factory for the AI-Powered Programming Evaluation Platform."""

from fastapi import FastAPI

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

    return app


app = create_app()
