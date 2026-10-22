import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import FRONTEND_DIR, BASE_DIR
from backend.database import init_db

# Import all route modules
from backend.routes.patient import router as patient_router
from backend.routes.sensor import router as sensor_router
from backend.routes.prediction import router as prediction_router
from backend.routes.xai import router as xai_router
from backend.routes.prescription import router as prescription_router
from backend.routes.medication import router as medication_router
from backend.routes.fda import router as fda_router
from backend.routes.analysis import router as analysis_router
from backend.routes.report import router as report_router
from backend.routes.system import router as system_router
from backend.routes.pharmacy import router as pharmacy_router

app = FastAPI(
    title="MediSafe AI",
    description="AI-Powered Disease Risk Classification & Medication Safety Decision Support",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
def on_startup():
    init_db()

# Register API routers
app.include_router(prediction_router)
app.include_router(patient_router)
app.include_router(sensor_router)
app.include_router(xai_router)
app.include_router(prescription_router)
app.include_router(medication_router)
app.include_router(pharmacy_router)
app.include_router(fda_router)
app.include_router(analysis_router)
app.include_router(report_router)
app.include_router(system_router)

# Mount static frontend
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "MediSafe AI API Operational. Frontend initializing."}

if __name__ == "__main__":
    import uvicorn
    from backend.config import HOST, PORT
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=False)

