""" Kinetic - Network Monitoring Tool """

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from database import engine
import models
from routers import agents, targets, monitors, console, volley, env
from starlette.staticfiles import StaticFiles
from datetime import datetime

# Create FastAPI instance
app = FastAPI(
    title="Kinetic",
    description="Kinetic is a network monitoring tool",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url="/redoc"
)

# Load SQLAlchemy mapper from models
models.Base.metadata.create_all(bind=engine)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set server start time in app
app.server_start_time = datetime.now()
app.server_timezone = datetime.now().astimezone().tzinfo

# Kinetic Environment Operations
app.include_router(env.router)

# Basic CRUD operations
app.include_router(agents.router)
app.include_router(targets.router)
app.include_router(monitors.router)

# Agent job operations
app.include_router(volley.router)

# App UI operations pass server_start_time to console.router
app.include_router(console.router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """ Favicon """
    return FileResponse("static/favicon.ico")

@app.get("/", include_in_schema=False)
async def root():
    """ Root level redirection to /console """
    raise HTTPException(status_code=307, detail="Redirecting to /console", headers={"Location": "/console"})

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)
