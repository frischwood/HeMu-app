from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from datetime import date
from db import SessionLocal, MapRecord, Base, engine
from utils import build_spatiotemporal_query
import tempfile
import zipfile
import os

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# allow_credentials=True,

@app.get("/download")
def download_data(start_date: date, end_date: date,
                  xmin: float, ymin: float, xmax: float, ymax: float):
    db = SessionLocal()
    sql = build_spatiotemporal_query(start_date, end_date, (xmin, ymin, xmax, ymax))
    result = db.execute(sql, {
        "start": start_date, "end": end_date,
        "xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax
    })
    files = [r['filepath'] for r in result]

    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    with zipfile.ZipFile(temp_zip.name, 'w') as z:
        for f in files:
            z.write(f, os.path.basename(f))
    return FileResponse(temp_zip.name, filename="download.zip")

# @app.get("/timestamps")
# def list_timestamps():
#     db = SessionLocal()
#     results = db.query(MapRecord).order_by(MapRecord.acquisition_date).all()
#     return [r.acquisition_date.isoformat() for r in results]


@app.get("/timestamps")
def get_timestamps():
    db = SessionLocal()
    try:
        results = db.execute(select(MapRecord.acquisition_date)).fetchall()
        return sorted([r[0].isoformat() for r in results])
    finally:
        db.close()