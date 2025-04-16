FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    cron \
    gdal-bin libgdal-dev libgeos-dev libproj-dev \
    netcdf-bin libnetcdf-dev \
    build-essential curl git unzip \
    && rm -rf /var/lib/apt/lists/*

# Set GDAL environment variables (optional, sometimes needed)
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_VERSION=3.6.0

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
