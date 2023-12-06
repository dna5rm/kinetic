"""
Kinetic - CRUD operations for monitors db table
"""

from typing import Annotated, Optional
from pydantic import BaseModel, Field, field_validator
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
        description="Protocol to use [tcp or icmp]")
    port: Optional[int] = Field(ge=0, le=65535, example=0,
        description="TCP Port number")
    dscp: Optional[str] = Field(example="BE", description="DSCP Value")
    pollcount: Optional[int] = Field(ge=1, le=35, example=20,
        description="Number of polling cycles")
    is_active: Optional[bool] = Field(example=True,
        description="Whether the monitor is active or not")

    @field_validator("protocol")
    def verify_protocol(cls, v):
        """ Verify protocol is valid """

        # only accept tcp, udp, icmp
        if v.lower() not in ("tcp", "icmp"):
            raise ValueError("Protocol must be one of: tcp, icmp")
        return v.lower()

    @field_validator('port')
    def validate_port(cls, v):
        """ Validate port """
        if v < 0 or v > 65535:
            raise ValueError("Port must be a number between 0 and 65535")
        return v

    @field_validator('dscp')
    def validate_tos(cls, v):
        """
        Check if there is a TOS value.
        If input is a string, convert to upper case and check if it is in the map.
        """

        # Define TOS hex mapping of DSCP names
        dscp_name_map = {
            "CS0": 0x00, "BE": 0x00,
            "CS1": 0x20, "AF11": 0x28, "AF12": 0x30, "AF13": 0x38,
            "CS2": 0x40, "AF21": 0x48, "AF22": 0x50, "AF23": 0x58,
            "CS3": 0x60, "AF31": 0x68, "AF32": 0x70, "AF33": 0x78,
            "CS4": 0x80, "AF41": 0x88, "AF42": 0x90, "AF43": 0x98,
            "CS5": 0xA0, "EF": 0xB8,
            "CS6": 0xC0,
            "CS7": 0xE0
        } #dscp_name_map[key]

        # if input is a string, convert to upper case and check if it is in the map
        if isinstance(v, str):
            v = v.upper()
            if v in dscp_name_map:
                return v.upper()
            else:
                raise ValueError("Invalid DSCP name provided. Must be one of the following:", list(dscp_name_map.keys()))

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