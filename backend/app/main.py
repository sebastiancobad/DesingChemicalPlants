"""
ChemScale — FastAPI Application Entry Point.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.econ_router import router as econ_router
from app.api.v1.hx_router import router as hx_router
from app.api.v1.piping_router import router as piping_router
from app.api.v1.pump_router import router as pump_router
from app.api.v1.separator_router import router as separator_router
from app.api.v1.materials_router import router as materials_router
from app.api.v1.layout_router import router as layout_router

# Path to the built frontend
FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

app = FastAPI(
    title="ChemScale",
    description=(
        "Chemical Engineering Design and Sizing Platform — "
        "Thermodynamic calculations, equipment sizing, and economic evaluation "
        "adhering to ASME, API, TEMA, and ISA standards."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(hx_router)
app.include_router(econ_router)
app.include_router(piping_router)
app.include_router(pump_router)
app.include_router(separator_router)
app.include_router(materials_router)
app.include_router(layout_router)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "version": app.version}


# Serve frontend static assets (JS, CSS, images)
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="static-assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """Serve the React SPA — any non-API route returns index.html."""
        # Try to serve a real file first (e.g. vite.svg, favicon)
        file_path = FRONTEND_DIR / full_path
        if full_path and file_path.is_file():
            return FileResponse(file_path)
        # Otherwise return index.html for React Router to handle
        return FileResponse(FRONTEND_DIR / "index.html")
