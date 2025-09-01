#!/bin/bash

echo "🚀 Starting Heliomont DML Application..."

# Test database connection but don't block startup
echo "⏳ Testing database connection..."
python -c "
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

try:
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('✅ Database connection successful')
except Exception as e:
    print(f'⚠️ Database connection failed: {e}')
    print('⚠️ Starting without database - some features may not work')
" || echo "⚠️ Database check failed, continuing anyway..."

# Create database tables if possible
echo "📋 Creating database tables..."
python -c "
try:
    from db import Base, engine
    Base.metadata.create_all(bind=engine)
    print('✅ Database tables created')
except Exception as e:
    print(f'⚠️ Could not create tables: {e}')
" || echo "⚠️ Table creation failed, continuing anyway..."

# Start the application
echo "🚀 Starting FastAPI application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
