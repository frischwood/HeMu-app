# Heliomont DML Application

## Prerequisites
- Docker Desktop
- Git

## Setup
1. Clone the repository:
```bash
git clone https://github.com/frischwood/HeMu-app.git
cd HeMu-app 
```

2. Environment Configuration:
   - Copy the environment template:
   ```bash
   cp app/docker/.env.template app/docker/.env
   ```
   - Fill in the required environment variables in `.env`:
     - `DATABASE_URL`: Your PostgreSQL connection string
     - `TITILER_API_PREFIX`: Default `/cog`
     - `CORS_ORIGINS`: Default `*`
     - `CORS_METHODS`: Default `GET,POST,OPTIONS`
     - `CORS_HEADERS`: Default `*`

3. Start the application:
```bash
cd app/docker
docker compose up -d
```

4. Access the application:
   - Frontend: http://localhost:3000
   - TiTiler service: http://localhost:8001
   - Backend API: http://localhost:8000

## Directory Structure
```
heliomont_dml/
├── app/
│   ├── docker/
│   │   ├── docker-compose.yml
│   │   ├── .env
│   │   └── .env.template
│   ├── frontend/
│   ├── data/
│   │   └── cogs/
│   └── app/
└── README.md
```