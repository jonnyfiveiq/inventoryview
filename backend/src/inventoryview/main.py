"""FastAPI application factory and lifespan."""

import logging
import logging.config
import re
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from inventoryview.config import Settings, get_settings
from inventoryview.database import check_age_extension, close_pool, ensure_graph_exists, init_pool
from inventoryview.schemas.errors import ErrorCode, error_response
from inventoryview.services.vault import init_vault, vault_key_holder

# Patterns to redact from log output
_SECRET_PATTERNS = re.compile(
    r"(passphrase|password|secret|token|auth_tag|nonce|encrypted_secret|salt)"
    r"\s*[=:]\s*\S+",
    re.IGNORECASE,
)


class SecretFilter(logging.Filter):
    """Filter that redacts secret values from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            args = record.args if isinstance(record.args, tuple) else (record.args,)
            new_args = []
            for arg in args:
                if isinstance(arg, str):
                    new_args.append(_SECRET_PATTERNS.sub(r"\1=***REDACTED***", arg))
                else:
                    new_args.append(arg)
            record.args = tuple(new_args)
        record.msg = _SECRET_PATTERNS.sub(r"\1=***REDACTED***", str(record.msg))
        return True


def configure_logging(debug: bool = False) -> None:
    """Configure structured logging with secret filtering."""
    level = "DEBUG" if debug else "INFO"
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "secret_filter": {
                "()": SecretFilter,
            },
        },
        "formatters": {
            "json": {
                "format": '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "filters": ["secret_filter"],
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    })


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""
    settings: Settings = app.state.settings

    # Initialize database pool
    try:
        pool = await init_pool(settings.database_url)
    except Exception as e:
        logger.error(
            "Failed to connect to database: %s. "
            "Check DATABASE_URL, database availability, disk space, and permissions.",
            e,
        )
        sys.exit(1)

    # Check AGE extension (FR-019)
    if not await check_age_extension(pool):
        logger.error(
            "Apache AGE extension not found on the connected PostgreSQL instance. "
            "Please install the AGE extension or use the embedded database."
        )
        await close_pool()
        sys.exit(1)

    # Ensure graph exists
    await ensure_graph_exists(pool, settings.graph_name)

    # Initialize vault key derivation
    await init_vault(settings.vault_passphrase, pool)

    # Generate JWT secret if not configured
    if not settings.jwt_secret:
        import secrets

        settings.jwt_secret = secrets.token_urlsafe(32)
        logger.warning(
            "No IV_JWT_SECRET configured - generated ephemeral secret. "
            "Tokens will be invalidated on restart. Set IV_JWT_SECRET for persistence."
        )

    app.state.pool = pool
    logger.info("InventoryView started on %s:%d", settings.host, settings.port)

    yield

    vault_key_holder.clear_key()
    await close_pool()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create the FastAPI application."""
    if settings is None:
        settings = get_settings()

    configure_logging(debug=settings.debug)

    app = FastAPI(
        title="InventoryView",
        version="0.1.0",
        description="Infrastructure inventory with graph-based data model",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.state.settings = settings

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=400,
            content=error_response(ErrorCode.VALIDATION_ERROR, str(exc)),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content=error_response(ErrorCode.INTERNAL_ERROR, "An unexpected error occurred"),
        )

    # Mount API v1 router
    from inventoryview.api.v1.router import router as v1_router

    app.include_router(v1_router, prefix="/api/v1")

    # Serve frontend SPA static files if the UI directory exists
    import os
    from pathlib import Path

    ui_dir = Path(os.environ.get("IV_UI_DIR", "/app/ui"))
    if ui_dir.is_dir() and (ui_dir / "index.html").is_file():
        from fastapi.staticfiles import StaticFiles
        from fastapi.responses import FileResponse

        # Serve hashed asset files directly
        if (ui_dir / "assets").is_dir():
            app.mount("/assets", StaticFiles(directory=str(ui_dir / "assets")), name="assets")

        # Serve root-level static files (favicon, etc.) and SPA fallback
        @app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            file_path = ui_dir / full_path
            if full_path and ".." not in full_path and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(ui_dir / "index.html"))

        logger.info("Serving frontend UI from %s", ui_dir)

    return app


# Module-level app instance for uvicorn
app = create_app()
