"""
Kinetic - CRUD operations for monitors db table
"""

from os import remove
from hashlib import md5
from datetime import datetime
from typing import Annotated, Optional
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from starlette import status
from models import Agents, Hosts, Monitors
from database import SessionLocal
from uuid import uuid4 as UUID

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
    agent_id: str = Field(..., pattern="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", description="Agent by id")
    host_id: str = Field(..., pattern="^[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}$", description="Host by id")
    description: Optional[str] = Field(max_length=255, example="Monitoring host",
        description="Monitor description")
    protocol: Optional[str] = Field(example="icmp",
        description="Protocol to use [tcp or icmp]")
    port: Optional[int] = Field(ge=0, le=65535, example=0,
        description="TCP Port number")
    dscp: Optional[str] = Field(example="BE", description="DSCP Value")
    pollcount: Optional[int] = Field(ge=1, le=35, example=20,
        description="Number of polling cycles")
    pollinterval: Optional[int] = Field(ge=1, le=3600, example=60,
        description="Polling interval in seconds")
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
                        "id": "00000000-0000-0000-0000-000000000000",
                        "agent_id": "00000000-0000-0000-0000-000000000000",
                        "host_id": "00000000-0000-0000-0000-000000000000",
                        "description": "Monitoring host",
                        "protocol": "icmp",
                        "port": 0,
                        "dscp": 0,
                        "pollcount": 20,
                        "pollinterval": 60,
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
            "pollinterval": monitor.pollinterval,
            "is_active": monitor.is_active
        })
    return monitors

@router.get("/{monitor_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "agent_id": "00000000-0000-0000-0000-000000000000",
                    "host_id": "00000000-0000-0000-0000-000000000000",
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "pollinterval": 60,
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
async def read_monitor_id(db: DBDependency, monitor_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
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
        "pollinterval": monitor.pollinterval,
        "is_active": monitor.is_active
    }

@router.get("/agent/{agent_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "agent_id": "00000000-0000-0000-0000-000000000000",
                    "host_id": "00000000-0000-0000-0000-000000000000",
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "pollinterval": 60,
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
async def read_monitor_by_agent_id(db: DBDependency, agent_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
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
            "pollinterval": monitor.pollinterval,
            "is_active": monitor.is_active
        })
    return monitors

@router.get("/host/{host_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "agent_id": "00000000-0000-0000-0000-000000000000",
                    "host_id": "00000000-0000-0000-0000-000000000000",
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "pollinterval": 60,
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
async def read_monitor_by_host_id(db: DBDependency, host_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
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
            "pollinterval": monitor.pollinterval,
            "is_active": monitor.is_active
        })
    return monitors

@router.post("/", status_code=status.HTTP_201_CREATED,
    responses={
        201: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "agent_id": "00000000-0000-0000-0000-000000000000",
                    "host_id": "00000000-0000-0000-0000-000000000000",
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "pollinterval": 60,
                    "is_active": True
                }
            }
        }},
        400: { "content": {
            "application/json": {
                "example": {"detail": "Bad Request"}
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
                    "id": "00000000-0000-0000-0000-000000000000",
                    "agent_id": "00000000-0000-0000-0000-000000000000",
                    "host_id": "00000000-0000-0000-0000-000000000000",
                    "description": "Monitoring host",
                    "protocol": "icmp",
                    "port": 0,
                    "dscp": 0,
                    "pollcount": 20,
                    "pollinterval": 60,
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
    if monitor.protocol == "tcp" and monitor.port == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad Request (port)")

    # If monitor does not exist, create and return 201 with database entry
    db_monitor = Monitors(**monitor.dict())

    # Generate UUID for agent
    db_monitor.id = str(UUID())

    # Add agent to database
    db.add(db_monitor)
    db.commit()
    db.refresh(db_monitor)

    # Return only certain fields
    return {
        "id": db_monitor.id,
        "agent_id": db_monitor.agent_id,
        "host_id": db_monitor.host_id,
        "description": db_monitor.description,
        "protocol": db_monitor.protocol,
        "port": db_monitor.port,
        "dscp": db_monitor.dscp,
        "pollcount": db_monitor.pollcount,
        "pollinterval": db_monitor.pollinterval,
        "is_active": db_monitor.is_active
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
async def update_monitor_id(db: DBDependency, monitor: MonitorUpdateModel, monitor_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
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

@router.patch("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT,
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
async def clear_monitor_stats(db: DBDependency, monitor_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Clear monitor stats by ID """

    # Get monitor from database
    db_monitor = db.query(Monitors).filter(Monitors.id == monitor_id).first()

    # Return 404 if monitor not found
    if not db_monitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Zero out: sample, avg_loss, avg_median, avg_min, avg_max, avg_stddev, total_down
    for field in db_monitor.__table__.columns:
        if field.name in ("sample", "avg_loss", "avg_median", "avg_min", "avg_max", "avg_stddev", "total_down"):
            setattr(db_monitor, field.name, 0)

    # Update last_clear to current time
    db_monitor.last_clear = datetime.now()

    # Commit changes
    db.commit()
    db.refresh(db_monitor)

    # Return 204 if cleared
    return {"detail": "No Content"}

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
async def delete_monitor_id(db: DBDependency, monitor_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Delete a monitor by ID """

    # Get monitor from database
    monitor = db.query(Monitors).filter(Monitors.id == monitor_id).first()

    # Return 404 if monitor does not exist
    if not monitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    # Delete monitor from database
    db.delete(monitor)
    db.commit()

    # delete the rrd file
    rrd_file = "rra_data/" + md5((str(monitor.agent_id) + "-" + str(monitor_id)).encode()).hexdigest() + ".rrd"
    # check if file exists if so delete it
    try:
        remove(rrd_file)
    except OSError:
        pass

    # Return 204 if monitor deleted
    return {"detail": "No Content"}