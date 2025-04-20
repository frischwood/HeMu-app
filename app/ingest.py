import os
import time
from datetime import datetime
from convert import convert_netcdf_to_cog
from db import SessionLocal, MapRecord
from sqlalchemy.exc import OperationalError

VARIABLE = os.environ["VARIABLE"]
DATA_DIR = os.environ["DATA_DIR"]

def ingest_new_data():
    for i in range(5):
        try:
            db = SessionLocal()
            break
        except OperationalError as e:
            print(f"DB connection failed. Retry {i+1}/5...")
            time.sleep(5)
    else:
        raise RuntimeError("Could not connect to the DB after retries.")
    
    print("🚀 ingest.py is running...")
    db = SessionLocal()
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".nc"):
            continue
        path = os.path.join(DATA_DIR, filename)
        try:
            cog_path, timestamp, vmin, vmax = convert_netcdf_to_cog(path, variable_name=VARIABLE)
            print(f"cog_path: {cog_path}")
            print(f"Timestamp: {timestamp}")
            # Modify the path to match what titiler expects
            relative_path = os.path.relpath(str(cog_path), "data/cogs")
            titiler_path = f"/opt/cogs/{relative_path}"
            # Check if already in DB
            exists = db.query(MapRecord).filter_by(acquisition_datetime=timestamp).first()
            if exists:
                print(f"✅ Already ingested: {filename}")
                continue
            # Insert into DB
            record = MapRecord(acquisition_datetime=timestamp, filepath=titiler_path, vmin=vmin, vmax=vmax)
            db.add(record)
            db.commit()
            print(f"✅ Ingested: {filename} with path {titiler_path}")
        except Exception as e:
            print(f"❌ Failed to ingest {filename}: {e}")
    db.close()

if __name__ == "__main__":
    ingest_new_data()