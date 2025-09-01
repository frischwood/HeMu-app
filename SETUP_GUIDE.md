# Heliomont DML Application - Setup Guide

## 🚀 Quick Start

The application has been updated with several critical fixes. Follow these steps to get it running:

### 1. Verify Environment Configuration

Make sure your `.env` file in the `docker/` directory has all required variables:

```bash
cd docker
cat .env
```

Should contain:
```
DATABASE_URL=postgresql://your_db_connection_string
TITILER_API_PREFIX=/cog
CORS_ORIGINS=*
CORS_METHODS=GET,POST,OPTIONS
CORS_HEADERS=*
DATA_DIR=data/netcdf
VARIABLE=SISGHI-No-Horizon
DATETIME_FORMAT=%Y%m%dT%H%M%S
```

### 2. Start the Application

```bash
cd docker
docker compose up -d
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Health Check**: http://localhost:8000/health
- **TiTiler Service**: http://localhost:8001

## 🔧 What Was Fixed

### Critical Fixes Applied:

1. **✅ Added Frontend Service**
   - Added nginx-based frontend service to docker-compose.yml
   - Created custom nginx configuration with API proxying
   - Updated frontend JavaScript to use relative URLs

2. **✅ Fixed Environment Variables**
   - Added missing `DATA_DIR`, `VARIABLE`, `DATETIME_FORMAT` to backend service
   - All services now have proper environment configuration

3. **✅ Improved Cron Ingestion**
   - Changed from one-time execution to continuous monitoring (5-minute intervals)
   - Added proper error handling and logging

4. **✅ Enhanced Error Handling**
   - Added health check endpoint (`/health`)
   - Improved database connection retry logic
   - Better logging throughout the application

5. **✅ Database Initialization**
   - Added startup script to ensure database tables are created
   - Proper database connection waiting logic

6. **✅ Fixed API Routing**
   - Frontend now properly routes API calls through nginx proxy
   - TiTiler requests are proxied correctly

## 📁 Updated Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend      │    │    TiTiler      │
│   (nginx:3000)  │◄──►│  (FastAPI:8000)  │◄──►│   (:8001)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐               │
         │              │   PostgreSQL    │               │
         │              │   (Supabase)    │               │
         │              └─────────────────┘               │
         │                                                │
         └────────────────┐         ┌────────────────────┘
                          ▼         ▼
                 ┌─────────────────────────┐
                 │    File System          │
                 │  data/netcdf/ → COGs    │
                 └─────────────────────────┘
                          ▲
                          │
                 ┌─────────────────┐
                 │  Cron Ingest    │
                 │ (5-min cycle)   │
                 └─────────────────┘
```

## 🔍 Monitoring & Debugging

### Check Service Status
```bash
docker compose ps
```

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f cron-ingest
```

### Test Database Connection
```bash
curl http://localhost:8000/health
```

### Test Data Ingestion
Place NetCDF files in `data/netcdf/` directory and check logs:
```bash
docker compose logs -f cron-ingest
```

## 🐛 Troubleshooting

### Common Issues:

1. **Database Connection Errors**
   - Verify `DATABASE_URL` in `.env` file
   - Check network connectivity to Supabase

2. **No Data Showing**
   - Ensure NetCDF files are in `data/netcdf/`
   - Check cron-ingest logs for processing errors
   - Verify COG files are created in `data/cogs/`

3. **Frontend Not Loading**
   - Check if all services are running
   - Verify nginx configuration is correct

4. **TiTiler Errors**
   - Ensure COG files exist in `data/cogs/`
   - Check file permissions and paths

### Still Not Working?

The application now has much better error handling and logging. Check the logs for specific error messages:

```bash
docker compose logs backend | grep ERROR
docker compose logs cron-ingest | grep "❌"
```

## 🚀 Next Steps

The application should now start successfully! The main remaining work is in the HeMu machine learning component, which contains several `NotImplementedError` placeholders that need to be completed based on your specific ML requirements.
