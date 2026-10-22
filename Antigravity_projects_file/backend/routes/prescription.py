import json
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Dict, Any
from backend.services.ocr_service import ocr_service
from backend.config import UPLOADS_DIR
from backend.database import get_db_connection

router = APIRouter(prefix="/api/prescription", tags=["Prescription OCR"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}

@router.post("/upload")
async def upload_prescription(
    patient_id: str = Form(...),
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file format '{file_ext}'. Please upload JPG, PNG, or PDF.")

    # Secure file save
    safe_filename = f"{patient_id}_{int(Path(file.filename).stat().st_mtime if hasattr(Path(file.filename), 'stat') else 1000)}_{file.filename}"
    saved_path = UPLOADS_DIR / safe_filename

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run OCR processing
    result = ocr_service.process_prescription(str(saved_path), patient_id)

    # Save to SQLite database
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO prescriptions (patient_id, file_path, ocr_text, detected_medicines_json, confidence_score)
        VALUES (?, ?, ?, ?, ?)
        """, (
            patient_id,
            str(saved_path),
            result["extracted_text"],
            json.dumps(result["detected_medicines"]),
            0.88 if result["confidence_level"] == "High" else 0.55
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error persisting prescription to DB: {e}")

    return result
