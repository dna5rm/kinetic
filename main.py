""" Kinetic - Network Monitoring Tool """

import uvicorn
from fastapi import FastAPI, HTTPException
from database import engine
import models
from routers import agents, hosts, monitors

app = FastAPI(
    title="Kinetic",
    description="Kinetic is a network monitoring tool",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url="/redoc"
)

models.Base.metadata.create_all(bind=engine)

app.include_router(agents.router)
app.include_router(hosts.router)
app.include_router(monitors.router)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """ Favicon """
    return None

@app.get("/", include_in_schema=False)
async def root():
    """ Root """
    raise HTTPException(status_code=200, detail="Kinetic is running")

if __name__ == '__main__':
    uvicorn.run(app, port=8080, host="127.0.0.1")
