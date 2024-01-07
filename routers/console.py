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
from humanize import naturaldelta, naturaltime
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dataclasses import dataclass

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

# Dataclass to report monitor stats
@dataclass
class MonitorStats:
    """ Monitor Stats """

    # Monitor
    id: int
    description: str
    protocol: str
    port: int
    dscp: str

    # HOST
    host_address: str
    host_description: str
    last_change: str
    last_update: str

    # Current
    current_median: float
    current_loss: float

    # Average
    average_median: float
    average_minimum: float
    average_maximum: float
    average_stddev: float
    average_loss: float

@router.get("/", response_class=HTMLResponse)
async def console_home(request: Request, db: DBDependency):
    """ Console - Home """

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
    """ Console - Monitors by Agent """
    # get agent from database by agent_id
    agent = db.query(Agents).filter(Agents.id == agent_id).first()
    agent_naturaltime = naturaltime(agent.last_seen)

    # if agent esists and is active
    if agent and agent.is_active:

        # get a list of all monitors where is_active is True
        monitors = db.query(Monitors).filter(Monitors.agent_id == agent_id, Monitors.is_active == True).all()

        # create a list of MonitorStats objects of each monitor
        monitor_stats = []

        # for each monitor
        for monitor in monitors:

            # lookup host.name and host.address from host_id
            host_address = db.query(Hosts).filter(Hosts.id == monitor.host_id).first().address
            host_description = db.query(Hosts).filter(Hosts.id == monitor.host_id).first().description
            host_is_active = db.query(Hosts).filter(Hosts.id == monitor.host_id).first().is_active

            # if host is active
            if host_is_active:

                # get pollcount from monitor
                pollcount = monitor.pollcount

                # get last update times from monitor and convert to naturaldelta
                # remove the word "ago" from the string
                last_change = naturaltime(monitor.last_change).replace(" ago", "")
                last_update = naturaltime(monitor.last_update)

                # get current stats from monitor
                current_median = monitor.current_median
                current_min = monitor.current_min
                current_max = monitor.current_max
                current_stddev = monitor.current_stddev
                current_loss = int((monitor.current_loss / pollcount) * 100)

                # threshold based on stddev of min and max.
                # If stddev is greater than 10% of the difference between min and max, then the monitor is considered unstable
                current_median_threshold = (current_max - current_min) * 0.10

                if current_stddev > current_median_threshold:
                    current_median_color = "bg-warning"
                elif current_median > current_max:
                    current_median_color = "bg-danger"
                else:
                    current_median_color = "bg-success"
                
                # current loss threshold
                if current_loss > 10:
                    current_loss_color = "bg-warning"
                elif current_loss > 20:
                    current_loss_color = "bg-danger"
                else:
                    current_loss_color = "bg-success"

                # get average stats from monitor
                average_median = monitor.avg_median
                average_minimum = monitor.avg_min
                average_maximum = monitor.avg_max
                average_stddev = monitor.avg_stddev
                average_loss = int((monitor.avg_loss / pollcount) * 100)

                # threshold based on stddev of min and max.
                # If stddev is greater than 10% of the difference between min and max, then the monitor is considered unstable
                average_median_threshold = (average_maximum - average_minimum) * 0.10

                if average_stddev > average_median_threshold:
                    average_median_color = "bg-warning"
                elif average_median > average_maximum:
                    average_median_color = "bg-danger"
                else:
                    average_median_color = "bg-success"

                average_minimum_threshold = (average_maximum - average_minimum) * 0.10

                if average_minimum < average_minimum_threshold:
                    average_minimum_color = "bg-warning"
                elif average_minimum > average_maximum:
                    average_minimum_color = "bg-danger"
                else:
                    average_minimum_color = "bg-success"
                
                average_maximum_threshold = (average_maximum - average_minimum) * 0.10
                
                if average_maximum > average_maximum_threshold:
                    average_maximum_color = "bg-warning"
                elif average_maximum < average_minimum:
                    average_maximum_color = "bg-danger"
                else:
                    average_maximum_color = "bg-success"

                average_stddev_threshold = (average_maximum - average_minimum) * 0.10
                
                if average_stddev > average_stddev_threshold:
                    average_stddev_color = "bg-warning"
                elif average_stddev > average_maximum:
                    average_stddev_color = "bg-danger"
                else:
                    average_stddev_color = "bg-success"

                # average loss threshold
                if average_loss > 10:
                    average_loss_color = "bg-warning"
                elif average_loss > 20:
                    average_loss_color = "bg-danger"
                else:
                    average_loss_color = "bg-success"

                # create a MonitorStats object of the monitor
                monitor_stats.append(MonitorStats(
                    id=monitor.id,
                    description=monitor.description,
                    protocol=monitor.protocol,
                    port=monitor.port,
                    dscp=monitor.dscp,
                    host_description=host_description,
                    host_address=host_address,
                    last_change=last_change,
                    current_median=current_median,
                    current_loss=current_loss,
                    average_median=average_median,
                    average_minimum=average_minimum,
                    average_maximum=average_maximum,
                    average_stddev=average_stddev,
                    average_loss=average_loss,
                    last_update=last_update
                ))

        # Create context dictionary with active monitor data
        context = {
            "request": request,
            "title": request.app.title,
            "agent": agent,
            "agent_naturaltime": agent_naturaltime,
            "stats": monitor_stats,
            "monitor_colors": {
                "current_median": current_median_color,
                "current_loss": current_loss_color,
                "average_median": average_median_color,
                "average_minimum": average_minimum_color,
                "average_maximum": average_maximum_color,
                "average_stddev": average_stddev_color,
                "average_loss": average_loss_color
            }
        }

        return templates.TemplateResponse("agent.html", context=context)
        
    # Default raise HTTPException with 404 status code
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"agent_id not found")

@router.get("/host/{host_id}", response_class=HTMLResponse)
async def console_host(request: Request, host_id: int, db: DBDependency):
    # Default raise HTTPException with 404 status code
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"host_id not found")

@router.get("/monitor/{monitor_id}", response_class=HTMLResponse)
async def console_monitor(request: Request, monitor_id: int, db: DBDependency):
    # Default raise HTTPException with 404 status code
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"monitor_id not found")