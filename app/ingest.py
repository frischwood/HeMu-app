import os
import time
from datetime import datetime
from convert import convert_netcdf_to_cog
from db import SessionLocal, MapRecord
from sqlalchemy.exc import OperationalError
DATA_DIR = "data/netcdf"  # directory where new NetCDF files appear
VARIABLE = "SISGHI-No-Horizon" # default variable to extract

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
            cog_path, timestamp = convert_netcdf_to_cog(path, variable_name=VARIABLE)
            print(f"cog_path: {cog_path}")
            date = datetime.strptime(timestamp, "%Y-%m-%d").date()
            # Check if already in DB
            exists = db.query(MapRecord).filter_by(acquisition_date=date).first()
            if exists:
                print(f"✅ Already ingested: {filename}")
                continue
            # Insert into DB
            record = MapRecord(acquisition_date=date, filepath=str(cog_path))
            db.add(record)
            db.commit()
            print(f"✅ Ingested: {filename}")
        except Exception as e:
            print(f"❌ Failed to ingest {filename}: {e}")
    db.close()

if __name__ == "__main__":
    ingest_new_data()