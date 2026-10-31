"""FastAPI application factory."""

from fastapi import FastAPI

from evaluator.api.routers import assignments, submissions


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title="Programming Evaluator",
        description="AI-assisted programming assignment evaluation platform",
        version="0.1.0",
    )

    app.include_router(assignments.router)
    app.include_router(submissions.router)

    @app.get("/health", tags=["system"])
    def health_check() -> dict:
        """Verify the application is running."""
        return {"status": "healthy"}

    return app


app = create_app()

