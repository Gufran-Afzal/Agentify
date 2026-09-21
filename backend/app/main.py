import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.database.connection import get_connection
from backend.app.database.schema import init_db
from backend.app.database.seed import seed_db

from backend.app.api.products import router as products_router
from backend.app.api.keywords import router as keywords_router
from backend.app.api.content import router as content_router
from backend.app.api.research import router as research_router
from backend.app.api.opportunities import router as opportunities_router
from backend.app.api.briefs import router as briefs_router
from backend.app.api.drafts import router as drafts_router
from backend.app.api.publishing import router as publishing_router
from backend.app.api.dashboard import router as dashboard_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("adaptive_content")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Adaptive Content Intelligence backend...")
    conn = get_connection()
    try:
        init_db(conn)
        seed_db(conn)
        logger.info("Database schema initialized and seed records verified.")
    finally:
        conn.close()
    yield
    logger.info("Adaptive Content Intelligence backend shutting down.")

def create_app() -> FastAPI:
    app = FastAPI(
        title="Adaptive Content Intelligence",
        description=(
            "Content intelligence and operations platform for ecommerce stores. "
            "Analyzes product catalogs and search demand to uncover high-intent content "
            "opportunities, generate structured briefs and drafts, and manage publishing."
        ),
        version="1.0.0",
        lifespan=lifespan
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global unhandled exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred."}
        )

    # Basic endpoints
    @app.get("/", tags=["General"])
    def home():
        return {
            "message": "Adaptive Content Intelligence is running!",
            "version": "1.0.0",
            "docs": "/docs"
        }

    @app.get("/health", tags=["General"])
    def health():
        return {
            "status": "ok",
            "environment": settings.ENVIRONMENT
        }

    # Register API routers
    app.include_router(dashboard_router)
    app.include_router(products_router)
    app.include_router(keywords_router)
    app.include_router(content_router)
    app.include_router(research_router)
    app.include_router(opportunities_router)
    app.include_router(briefs_router)
    app.include_router(drafts_router)
    app.include_router(publishing_router)

    return app

app = create_app()
