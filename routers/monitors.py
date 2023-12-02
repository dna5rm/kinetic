"""
Kinetic - CRUD operations for monitors db table
"""

from typing import Annotated, Optional
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from starlette import status
from models import Agents, Hosts, Monitors
from database import SessionLocal

router = APIRouter(
    prefix="/monitors",
    tags=["monitors"]
)

def get_db():
    """ Get database """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDependency = Annotated[Session, Depends(get_db)]

class MonitorModel(BaseModel):
    """ Monitor Model """
    agent_id: int = Field(gt=0, example=1, description="Agent by ID")
    host_id: int = Field(gt=0, example=1, description="Host by ID")
    description: Optional[str] = Field(max_length=255, example="Monitoring host",
        description="Monitor description")
    protocol: Optional[str] = Field(example="icmp",
        description="Protocol to use [tcp, udp, icmp]")
    port: Optional[int] = Field(ge=0, le=65535, example=0,
        description="TCP/UDP Port number")
    dscp: Optional[int] = Field(ge=0, le=56, example=0,
        description="DSCP Value")
    pollcount: Optional[int] = Field(ge=1, le=35, example=20,
        description="Number of polling cycles")
    is_active: Optional[bool] = Field(example=True,
        description="Whether the monitor is active or not")

    @validator("protocol")
    def verify_protocol(cls, v):
        """ Verify protocol is valid """

        # only accept tcp, udp, icmp
        if v.lower() not in ("tcp", "udp", "icmp"):
            raise ValueError("Protocol must be one of: tcp, udp, icmp")
        return v.lower()

    @validator("port")
    def verify_port(cls, v, values):
        """ Verify port is valid """

        # Get the protocol value from the values dictionary
        protocol = values.get("protocol").lower()

        # Verify port is valid for protocol
        if v == 0 and protocol != "icmp":
            raise ValueError("Port for tcp or udp must be between 1 and 65535")
        if protocol == "icmp" and v != 0:
            raise ValueError("Port for icmp must be 0")
        return v

    @validator("dscp")
    def verify_dscp(cls, v):
        """ Verify dscp is valid """

        # Verify dscp is valid in tuple
        dscp = (0, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26,
                28, 30, 32, 34, 36, 38, 40, 46, 48, 56)

        # loop through tuple and raise error if not found
        if v not in dscp:
            raise ValueError(f"DSCP value should be {dscp}")
        return v

class MonitorUpdateModel(BaseModel):
    """ Monitor Update Model """
    description: Optional[str] = Field(max_length=255, example="Monitoring host",
        description="Monitor description")
    is_active: Optional[bool] = Field(example=True,
        description="Whether the monitor is active or not")

@router.get("/", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": [{
                        "id": 1,
                        "agent_id": 1,
                        "host_id": 1,
                        "description": "Monitoring host",
                        "protocol": "icmp",
                        "port": 0,
                        "dscp": 0,
                        "pollcount": 20,
                        "is_active": True
                    }]
                }
            }
        }
    }
)
async def read_monitor_all(db: DBDependency):
    """ Get all monitors """

    # Check the number of monitors in the database
    count = db.query(Monitors).count()
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Loop through all monitors and return only certain fields
    monitors = []
    for monitor in db.query(Monitors).all():
        monitors.append({
            "id": monitor.id,
            "agent_id": monitor.agent_id,
            "host_id": monitor.host_id,
            "description": monitor.description,
            "protocol": monitor.protocol,
            "port": monitor.port,
            "dscp": monitor.dscp,
            "pollcount": monitor.pollcount,
            "is_active": monitor.is_active
        })
    return monitors

@router.get("/{monitor_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "agent_id": 1,
                    "host_id": 1,
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "is_active": True
                }
            }
        }},
        404: { "content": {
            "application/json": {
                "example": {"detail": "Not Found"}
            }
        }},
    }
)
async def read_monitor_id(db: DBDependency, monitor_id: int):
    """ Get a monitor by ID """

    # Get monitor from database
    monitor = db.query(Monitors).filter(Monitors.id == monitor_id).first()

    # Return 404 if monitor does not exist
    if not monitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Return only certain fields
    return {
        "id": monitor.id,
        "agent_id": monitor.agent_id,
        "host_id": monitor.host_id,
        "description": monitor.description,
        "protocol": monitor.protocol,
        "port": monitor.port,
        "dscp": monitor.dscp,
        "pollcount": monitor.pollcount,
        "is_active": monitor.is_active
    }

@router.get("/agent/{agent_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "agent_id": 1,
                    "host_id": 1,
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "is_active": True
                }
            }
        }},
        404: { "content": {
            "application/json": {
                "example": {"detail": "Not Found"}
            }
        }},
    }
)
async def read_monitor_by_agent_id(db: DBDependency, agent_id: int):
    """ Get all monitors by agent ID """

    # Get agent from database
    agent = db.query(Agents).filter(Agents.id == agent_id).first()

    # Return 404 if agent does not exist
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Check the number of monitors in the database
    count = db.query(Monitors).filter(Monitors.agent_id == agent_id).count()
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Loop through all monitors and return only certain fields
    monitors = []
    for monitor in db.query(Monitors).filter(Monitors.agent_id == agent_id).all():
        monitors.append({
            "id": monitor.id,
            "agent_id": monitor.agent_id,
            "host_id": monitor.host_id,
            "description": monitor.description,
            "protocol": monitor.protocol,
            "port": monitor.port,
            "dscp": monitor.dscp,
            "pollcount": monitor.pollcount,
            "is_active": monitor.is_active
        })
    return monitors

@router.get("/host/{host_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "agent_id": 1,
                    "host_id": 1,
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "is_active": True
                }
            }
        }},
        404: { "content": {
            "application/json": {
                "example": {"detail": "Not Found"}
            }
        }},
    }
)
async def read_monitor_by_host_id(db: DBDependency, host_id: int):
    """ Get all monitors by host ID """

    # Get host from database
    host = db.query(Hosts).filter(Hosts.id == host_id).first()

    # Return 404 if host does not exist
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Check the number of monitors in the database
    count = db.query(Monitors).filter(Monitors.host_id == host_id).count()
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Loop through all monitors and return only certain fields
    monitors = []
    for monitor in db.query(Monitors).filter(Monitors.host_id == host_id).all():
        monitors.append({
            "id": monitor.id,
            "agent_id": monitor.agent_id,
            "host_id": monitor.host_id,
            "description": monitor.description,
            "protocol": monitor.protocol,
            "port": monitor.port,
            "dscp": monitor.dscp,
            "pollcount": monitor.pollcount,
            "is_active": monitor.is_active
        })
    return monitors

@router.post("/", status_code=status.HTTP_201_CREATED,
    responses={
        201: { "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "agent_id": 1,
                    "host_id": 1,
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "is_active": True
                }
            }
        }},
        404: { "content": {
            "application/json": {
                "example": {"detail": "Not Found"}
            }
        }},
        409: { "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "agent_id": 1,
                    "host_id": 1,
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "is_active": True
                }
            }
        }},
    }
)
async def create_monitor_id(db: DBDependency, monitor: MonitorModel):
    """ Create a monitor """

    # Get agent from database
    agent = db.query(Agents).filter(Agents.id == monitor.agent_id).first()
    # Get host from database
    host = db.query(Hosts).filter(Hosts.id == monitor.host_id).first()
    # Check if monitor already exists from post data
    exists = db.query(Monitors).filter(
        Monitors.agent_id == monitor.agent_id,
        Monitors.host_id == monitor.host_id,
        Monitors.protocol == monitor.protocol,
        Monitors.port == monitor.port,
        Monitors.dscp == monitor.dscp
    ).first()

    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found (agent_id)")
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found (host_id)")
    if exists:
        # Return 409 if monitor already exists
        raise HTTPException(
            status_code=409,
            detail=jsonable_encoder(exists, include=[
                "id", "agent_id", "host_id", "description", "protocol", "port", "dscp"
                ])
            )

    # If monitor does not exist, create and return 201 with database entry
    db_host = Monitors(**monitor.dict())
    db.add(db_host)
    db.commit()
    db.refresh(db_host)

    # Return only certain fields
    return {
        "id": db_host.id,
        "agent_id": db_host.agent_id,
        "host_id": db_host.host_id,
        "description": db_host.description,
        "protocol": db_host.protocol,
        "port": db_host.port,
        "dscp": db_host.dscp,
        "pollcount": db_host.pollcount,
        "is_active": db_host.is_active
    }

@router.put("/{monitor_id}", status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: { "content": {
            "application/json": {
                "example": {
                    "description": "Monitoring host",
                    "is_active": True
                }
            }
        }},
        404: { "content": {
            "application/json": {
                "example": {"detail": "Not Found"}
            }
        }},
    }
)
async def update_monitor_id(db: DBDependency, monitor: MonitorUpdateModel, monitor_id: int = Path(..., gt=0)):
    """ Update a monitor description and is_active and return updated monitor """

    # Get monitor from database
    db_monitor = db.query(Monitors).filter(Monitors.id == monitor_id).first()

    # Return 404 if monitor does not exist
    if not monitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Update monitor description and is_active
    db_monitor.description = monitor.description
    db_monitor.is_active = monitor.is_active
    db.commit()
    db.refresh(db_monitor)

    # Return only certain fields
    return {
        "description": monitor.description,
        "is_active": monitor.is_active
    }

@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: { "content": {
            "application/json": {
                "example": {"detail": "No Content"}
            }
        }},
        404: { "content": {
            "application/json": {
                "example": {"detail": "Not Found"}
            }
        }}
    }
)
async def delete_monitor_id(db: DBDependency, monitor_id: int = Path(..., gt=0)):
    """ Delete a monitor by ID """

    # Get monitor from database
    monitor = db.query(Monitors).filter(Monitors.id == monitor_id).first()

    # Return 404 if monitor does not exist
    if not monitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Delete monitor from database
    db.delete(monitor)
    db.commit()

    # Return 204 if monitor deleted
    return {"detail": "No Content"}