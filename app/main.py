from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import select
from datetime import date
from db import SessionLocal, MapRecord, Base, engine
from utils import build_spatiotemporal_query
import tempfile
import zipfile
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Try to create database tables, but don't fail if database is unavailable
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully")
except Exception as e:
    logger.error(f"❌ Database connection failed: {e}")
    logger.info("⚠️ Starting without database connection - some endpoints will not work")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# allow_credentials=True,

@app.get("/health")
def health_check():
    """Health check endpoint to verify database connectivity"""
    try:
        db = SessionLocal()
        # Test database connection
        db.execute(select(1))
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": "disconnected", "error": str(e)}

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
    """Get available timestamps with value ranges"""
    datetime_format = os.getenv('DATETIME_FORMAT', '%Y%m%dT%H%M%S')
    
    try:
        db = SessionLocal()
        # Fetch datetime, vmin, and vmax
        results = db.execute(
            select(
                MapRecord.acquisition_datetime,
                MapRecord.vmin,
                MapRecord.vmax
            )
        ).fetchall()
        
        # Return list of dicts with all needed information
        timestamps = sorted([{
            'datetime': r[0].strftime(datetime_format),
            'vmin': r[1],
            'vmax': r[2]
        } for r in results], key=lambda x: x['datetime'])
        
        db.close()
        logger.info(f"✅ Returned {len(timestamps)} timestamps from database")
        return timestamps
        
    except Exception as e:
        logger.error(f"❌ Failed to get timestamps from database: {e}")
        
        # Fallback: read from filesystem
        try:
            import glob
            import re
            
            cog_path = "/app/data/cogs"
            cog_files = glob.glob(f"{cog_path}/*.tif")
            
            timestamps = []
            for file_path in cog_files:
                filename = os.path.basename(file_path)
                # Extract datetime from filename: SISGHI-No-Horizon_20240103T102743.tif
                match = re.search(r'(\d{8}T\d{6})', filename)
                if match:
                    datetime_str = match.group(1)
                    timestamps.append({
                        'datetime': datetime_str,
                        'vmin': 0,  # Default values since we can't read from TIFF metadata easily
                        'vmax': 1000
                    })
            
            timestamps = sorted(timestamps, key=lambda x: x['datetime'])
            logger.info(f"✅ Returned {len(timestamps)} timestamps from filesystem")
            return timestamps
            
        except Exception as fs_error:
            logger.error(f"❌ Filesystem fallback also failed: {fs_error}")
            return []