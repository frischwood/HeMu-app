import os
import time
import logging
from datetime import datetime
from convert import convert_netcdf_to_cog
from db import SessionLocal, MapRecord
from sqlalchemy.exc import OperationalError
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

VARIABLE = os.environ["VARIABLE"]
DATA_DIR = os.environ["DATA_DIR"]

def ingest_new_data():
    # Retry database connection
    for i in range(5):
        try:
            db = SessionLocal()
            db.execute(text("SELECT 1"))  # Test connection with proper syntax
            break
        except OperationalError as e:
            logger.warning(f"DB connection failed. Retry {i+1}/5... Error: {e}")
            time.sleep(5)
        except Exception as e:
            logger.error(f"Database error: {e}")
            # Continue without database - process files anyway
            db = None
            break
    else:
        logger.error("Could not connect to the DB after 5 retries.")
        db = None
    
    logger.info("🚀 ingest.py is running...")
    
    # Check if data directory exists
    if not os.path.exists(DATA_DIR):
        logger.error(f"Data directory does not exist: {DATA_DIR}")
        return
    
    processed_count = 0
    error_count = 0
    
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".nc"):
            continue
            
        path = os.path.join(DATA_DIR, filename)
        try:
            cog_path, timestamp, vmin, vmax = convert_netcdf_to_cog(path, variable_name=VARIABLE)
            logger.info(f"Converted: {filename} -> {cog_path}")
            logger.info(f"Timestamp: {timestamp}, Value range: [{vmin}, {vmax}]")
            
            # Modify the path to match what titiler expects
            relative_path = os.path.relpath(str(cog_path), "data/cogs")
            titiler_path = f"/opt/cogs/{relative_path}"
            
            # Only try database operations if we have a connection
            if db is not None:
                try:
                    # Check if already in DB
                    exists = db.query(MapRecord).filter_by(acquisition_datetime=timestamp).first()
                    if exists:
                        logger.info(f"✅ Already ingested: {filename}")
                        continue
                        
                    # Insert into DB
                    record = MapRecord(
                        acquisition_datetime=timestamp, 
                        filepath=titiler_path, 
                        vmin=float(vmin), 
                        vmax=float(vmax)
                    )
                    db.add(record)
                    db.commit()
                    logger.info(f"✅ Ingested: {filename} with path {titiler_path}")
                except Exception as db_error:
                    logger.error(f"⚠️ Database operation failed for {filename}: {db_error}")
                    logger.info(f"✅ File converted but not recorded in database: {filename}")
            else:
                logger.info(f"✅ File converted (no database): {filename}")
                
            processed_count += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to ingest {filename}: {str(e)}")
            error_count += 1
            
    if db is not None:
        db.close()
    logger.info(f"Ingestion complete. Processed: {processed_count}, Errors: {error_count}")

if __name__ == "__main__":
    ingest_new_data()