from sqlalchemy import create_engine, Column, Integer, String, Date, Text
from sqlalchemy.orm import sessionmaker, declarative_base
import os

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class MapRecord(Base):
    __tablename__ = "maps"
    id = Column(Integer, primary_key=True, index=True)
    acquisition_date = Column(Date)
    filepath = Column(Text)