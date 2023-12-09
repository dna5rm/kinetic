"""
Kinetic - Operations for monitor jobs
"""

from datetime import datetime, timedelta
from typing import Annotated, Optional
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path, Request
from fastapi.encoders import jsonable_encoder
from starlette import status
from models import Agents, Hosts, Monitors
from database import SessionLocal
from rrd_handler import RRDHandler

router = APIRouter(
    prefix="/agent",
    tags=["jobs"],
    include_in_schema=True # Will be False when complete
)

def get_db():
    """ Get database """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDependency = Annotated[Session, Depends(get_db)]

class JobSubmissionModel(BaseModel):
    """
    Job submission model

    Input:
    {"id": 1, "results": [7.78, 6.4, 3.88, 3.63, 3.15, 3.66, 2.27, 5.81, 7.19, 3.22, 3.58, 4.79, 0.9, 3.33, 4.16, 0.87, 1.16, 1.13, 3.56, 3.67]}
    {"id": 2, "results": [5.53, 2.66, 5.73, 4.39, 2.65]}

    ID: Monitor job id
    Results: List of latency results
    """
    id: int = Field(..., gt=0)
    results: list[float] = Field(..., min_items=1, max_items=35)

    @field_validator("results")
    def validate_results(cls, v):
        """ Validate results list """
        # length must be between 1 and 35 items
        if len(v) < 1 or len(v) > 35:
            raise ValueError("results must be between 1 and 35 items")
        # each item must be an int or "U"
        for item in v:
            if not isinstance(item, float) and item != "U":
                raise ValueError("results must be a list of integers or 'U'")
        return v

@router.get("/{agent_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": [{
                        "host_id": 1,
                        "address": "192.0.2.42",
                        "protocol": "icmp",
                        "port": 0,
                        "dscp": "BE",
                        "pollcount": 20
                    }]
                }
            }
        },
        404: { "content": {
            "application/json": {
                "example": {
                    "detail": "Not Found"
                    }
                }
            }
        }
    }
)
async def read_agent_job(request: Request, db: DBDependency, agent_id: int = Path(..., gt=0)):
    """ Get all monitor jobs by agent id """

    # Get agent address from request
    if request.headers.get('X-Forwarded-For'):
        agent_address = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        agent_address = request.client.host

    # Get agent from database
    agent = db.query(Agents).filter(Agents.id == agent_id).filter(Agents.is_active == True).first()

    # If agent exists
    if agent:
        response = []

        # Update agent address if changed
        if agent.address != agent_address:
            agent.address = agent_address
        
        # Update agent last_seen
        agent.last_seen = datetime.now()
        db.commit()

        # Get all monitor jobs by agent id with last_update older than pollinterval
        monitors = db.query(Monitors).filter(Monitors.agent_id == agent_id).filter(Monitors.is_active == True).all()
        monitors = [monitor for monitor in monitors if monitor.last_update < datetime.now() - timedelta(seconds=monitor.pollinterval)]
        
        # Lookup host names by host id
        for monitor in monitors:
            host = db.query(Hosts).filter(Hosts.id == monitor.host_id).filter(Hosts.is_active == True).first()

            if host:
                # Append host monitor to the response
                response.append({
                    "id": monitor.id,
                    "address": host.address,
                    "protocol": monitor.protocol,
                    "port": monitor.port,
                    "dscp": monitor.dscp,
                    "pollcount": monitor.pollcount
                })
    else:
        # Agent not found
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Return the response
    return response

@router.put("/{agent_id}", status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: { "content": {
            "application/json": {
                "example": {
                    "status": "success"
                    }
                }
            }
        },
        404: { "content": {
            "application/json": {
                "example": {
                    "detail": "Not Found"
                    }
                }
            }
        }
    }
)
async def update_agent_job(request: Request, db: DBDependency, agent_id: int = Path(..., gt=0), job: JobSubmissionModel = None):
    """ Update monitor job by agent id """

    # get the id from the request body. This is the monitor job id
    job_id = job.id
    job_results = job.results

    # Get agent address from request
    if request.headers.get('X-Forwarded-For'):
        agent_address = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        agent_address = request.client.host

    # Get agent from database
    agent = db.query(Agents).filter(Agents.id == agent_id).filter(Agents.is_active == True).first()

    # If agent exists
    if agent:
        # Update agent address if changed
        if agent.address != agent_address:
            agent.address = agent_address
        
        # Update agent last_seen
        agent.last_seen = datetime.now()
        db.commit()

        # Get monitor job by id
        monitor = db.query(Monitors).filter(Monitors.id == job_id).filter(Monitors.is_active == True).first()

        # If monitor job exists
        if monitor:
            # Update monitor job results
            latencies = jsonable_encoder(job_results)
            valid = [x for x in latencies if isinstance(x, float)]
            monitor.sample += 1

            # Previous Volley Loss
            monitor.prev_loss = monitor.current_loss

            # Current Volley Stats
            monitor.current_loss = monitor.pollcount - len(valid)
            monitor.current_median = round(sorted(valid)[len(valid) // 2], 2)
            monitor.current_min = round(min(valid), 2)
            monitor.current_max = round(max(valid), 2)
            monitor.current_stddev = round((sum([((x - monitor.current_median) ** 2) for x in valid]) / len(valid)) ** 0.5, 2)
            
            # Aveage Volley Stats
            monitor.avg_loss = round(((monitor.avg_loss * (monitor.sample - 1)) + monitor.current_loss) / monitor.sample)
            monitor.avg_median = round(((monitor.avg_median * (monitor.sample - 1)) + monitor.current_median) / monitor.sample, 2)
            monitor.avg_min = round(((monitor.avg_min * (monitor.sample - 1)) + monitor.current_min) / monitor.sample, 2)
            monitor.avg_max = round(((monitor.avg_max * (monitor.sample - 1)) + monitor.current_max) / monitor.sample, 2)
            monitor.avg_stddev = round(((monitor.avg_stddev * (monitor.sample - 1)) + monitor.current_stddev) / monitor.sample, 2)

            # Update last_change row if current_loss is 100% or 0%
            if monitor.current_loss == 0 or monitor.current_loss == monitor.pollcount:
                monitor.last_change = datetime.now()

            # Update monitor job last_update
            monitor.last_update = datetime.now()
            monitor.results = jsonable_encoder(job_results)

            # Commit changes to database
            db.commit()

            # run RRHandler
            RRDHandler(agent_id=agent.id, monitor_id=monitor.id, step=monitor.pollinterval, results=job_results)
            
        else:
            # Monitor job not found
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Return success
    return { "status": "success" }