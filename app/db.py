from sqlalchemy import create_engine, Column, Integer, String, Date, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres.yvuyrpbhkpsloybelbef:ribkoB-mihhi9-wiqjab@aws-0-eu-central-2.pooler.supabase.com:6543/postgres")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MapRecord(Base):
    __tablename__ = "maps"
    id = Column(Integer, primary_key=True, index=True)
    acquisition_date = Column(Date)
    filepath = Column(Text)