"""
Kinetic - Server Console
"""

from starlette import status
from starlette.responses import RedirectResponse

from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, APIRouter, Request
from models import Agents, Hosts, Monitors
from database import SessionLocal

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    #prefix="/",
    tags=["console"],
    responses={404: {"description": "Not found"}},
    include_in_schema=True # Will be set to false later
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
async def home(request: Request, db: DBDependency):

    # Get a list of all the active agents from db
    agent_list = db.query(Agents)

    # Create context dictionary with app title
    context = {
        "request": request,
        "title": request.app.title,
        "description": request.app.description,
        "agent_list": agent_list
    }

    # Include the app title in response.
    return templates.TemplateResponse("home.html", context=context)