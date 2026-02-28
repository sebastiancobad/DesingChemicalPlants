"""
ChemScale — FastAPI Application Entry Point.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.econ_router import router as econ_router
from app.api.v1.hx_router import router as hx_router
from app.api.v1.piping_router import router as piping_router
from app.api.v1.pump_router import router as pump_router
from app.api.v1.separator_router import router as separator_router
from app.api.v1.materials_router import router as materials_router
from app.api.v1.layout_router import router as layout_router

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

# Register routers
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
