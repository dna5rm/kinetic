"""
Kinetic - Server Console
"""

from starlette import status
from starlette.responses import RedirectResponse

from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from models import Agents, Hosts, Monitors
from database import SessionLocal
from datetime import datetime
from humanize import naturaldelta
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/console",
    tags=["console"],
    responses={404: {"description": "Not found"}},
    include_in_schema=False
)

def get_db():
    """ Get database """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDependency = Annotated[Session, Depends(get_db)]
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def console_home(request: Request, db: DBDependency):

    # get a list of all agents where is_active is True
    agents = db.query(Agents).filter(Agents.is_active == True).all()

    # Create context dictionary with app title
    context = {
        "request": request,
        "title": request.app.title,
        "description": request.app.description,
        "agents": agents,
        "stats": {
            "active_agents": len(agents),
            "active_hosts": db.query(Hosts).filter(Hosts.is_active == True).count(),
            "active_monitors": db.query(Monitors).filter(Monitors.is_active == True).count(),
            "total_agents": db.query(Agents).count(),
            "total_hosts": db.query(Hosts).count(),
            "total_monitors": db.query(Monitors).count(),
            "server_start_time": request.app.server_start_time,
            "server_run_time": naturaldelta(datetime.now() - request.app.server_start_time)
        }
    }

    # Include the app title in response.
    return templates.TemplateResponse("home.html", context=context)

@router.get("/agent/{agent_id}", response_class=HTMLResponse)
# get agent_id from path and pass it to console_agent
async def console_agent(request: Request, agent_id: int, db: DBDependency):
    """ Console Agent """
    # get agent from database by agent_id
    agent = db.query(Agents).filter(Agents.id == agent_id).first()

    # if agent esists and is active
    if agent and agent.is_active:

        # Create context dictionary with active monitor data
        context = {
            "request": request,
            "title": request.app.title,
            "agent": agent,
            "monitor": db.query(Monitors).filter(Monitors.agent_id == agent_id, Monitors.is_active == True).all()
        }

        return templates.TemplateResponse("agent.html", context=context)
        
    # Default raise HTTPException with 404 status code
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"agent_id not found")
