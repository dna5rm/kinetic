"""
Kinetic - CRUD operations for hosts db table
"""

from typing import Annotated, Optional
from pydantic import BaseModel, Field, field_validator, IPvAnyAddress
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from starlette import status
from models import Hosts
from database import SessionLocal
from uuid import uuid4 as UUID

router = APIRouter(
    prefix="/hosts",
    tags=["hosts"]
)

def get_db():
    """ Get database """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDependency = Annotated[Session, Depends(get_db)]

class HostModel(BaseModel):
    """ Host Request Model """
    address: str = Field(..., example="192.0.2.42")
    description: Optional[str] = Field(max_length=255, example="This is host 42")
    is_active: Optional[bool] = Field(example=True)

    @field_validator('address')
    def address_must_be_valid_ip(cls, v):
        """ Validate IP address """
        try:
            IPvAnyAddress(v)
        except ValueError as exc:
            raise ValueError('Must be a valid IP address') from exc
        return v

@router.get("/", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": [{
                    "id": "00000000-0000-0000-0000-000000000000",
                    "address": "192.0.2.42",
                    "description": "This is host 42",
                    "is_active": True
                    }]
                }
            }
        }
    }
)
async def read_host_all(db: DBDependency):
    """ Get all hosts """
    # Check the number of hosts in the database
    count = db.query(Hosts).count()
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return db.query(Hosts).all()

@router.get("/{host_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "address": "192.0.2.42",
                    "description": "This is host 42",
                    "is_active": True
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
async def read_host_id(db: DBDependency, host_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Get host by id """
    host = db.query(Hosts).filter(Hosts.id == host_id).first()
    if not host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return host

@router.post("/", status_code=status.HTTP_201_CREATED,
    responses={
        201: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "address": "192.0.2.42",
                    "description": "This is host 42",
                    "is_active": True
                    }
                }
            }
        }
    }
)
async def create_host_id(db: DBDependency, host: HostModel):
    """ Create a host """

    # Check if host already exists from post data
    exists = db.query(Hosts).filter(Hosts.address == host.address).first()

    # Return 409 if host already exists
    if exists:
        raise HTTPException(status_code=409, detail=jsonable_encoder(exists))

    # If host does not exist, create and return 201 with database entry
    db_host = Hosts(**host.dict())

    # Generate UUID for host
    db_host.id = str(UUID())

    # Add host to database
    db.add(db_host)
    db.commit()
    db.refresh(db_host)
    return db_host

@router.put("/{host_id}", status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "address": "192.0.2.42",
                    "description": "This is host 42",
                    "is_active": True
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
async def update_host_id(db: DBDependency, host: HostModel, host_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Update a host """
    db_host = db.query(Hosts).filter(Hosts.id == host_id).first()
    if not db_host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if host:
        db_host.address = host.address
        db_host.description = host.description
        db_host.is_active = host.is_active
        db.commit()
        db.refresh(db_host)
    return db_host

@router.delete("/{host_id}", status_code=status.HTTP_204_NO_CONTENT,
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
async def delete_host_id(db: DBDependency, host_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Delete a host """
    db_host = db.query(Hosts).filter(Hosts.id == host_id).first()
    if not db_host:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Host not found")
    db.delete(db_host)
    db.commit()

    # Return 204 if monitor deleted
    return {"detail": "No Content"}
