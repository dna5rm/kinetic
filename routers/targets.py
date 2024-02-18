"""
Kinetic - CRUD operations for Targets db table
"""

from typing import Annotated, Optional
from pydantic import BaseModel, Field, field_validator, IPvAnyAddress
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from starlette import status
from models import Targets
from database import SessionLocal
from uuid import uuid4 as UUID

router = APIRouter(
    prefix="/targets",
    tags=["targets"]
)

def get_db():
    """ Get database """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDependency = Annotated[Session, Depends(get_db)]

class TargetModel(BaseModel):
    """ Target Request Model """
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
async def read_target_all(db: DBDependency):
    """ Get all targets """
    # Check the number of targets in the database
    count = db.query(Targets).count()
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return db.query(Targets).all()

@router.get("/{target_id}", status_code=status.HTTP_200_OK,
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
async def read_target_id(db: DBDependency, target_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Get target by id """
    target = db.query(Targets).filter(Targets.id == target_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return target

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
async def create_target_id(db: DBDependency, target: TargetModel):
    """ Create a target """

    # Check if target already exists from post data
    exists = db.query(Targets).filter(Targets.address == target.address).first()

    # Return 409 if target already exists
    if exists:
        raise HTTPException(status_code=409, detail=jsonable_encoder(exists))

    # If target does not exist, create and return 201 with database entry
    db_target = Targets(**target.dict())

    # Generate UUID for target
    db_target.id = str(UUID())

    # Add target to database
    db.add(db_target)
    db.commit()
    db.refresh(db_target)
    return db_target

@router.put("/{target_id}", status_code=status.HTTP_202_ACCEPTED,
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
async def update_target_id(db: DBDependency, target: TargetModel, target_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Update a target """
    db_target = db.query(Targets).filter(Targets.id == target_id).first()
    if not db_target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if target:
        db_target.address = target.address
        db_target.description = target.description
        db_target.is_active = target.is_active
        db.commit()
        db.refresh(db_target)
    return db_target

@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT,
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
async def delete_target_id(db: DBDependency, target_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Delete a target """
    db_target = db.query(Targets).filter(Targets.id == target_id).first()
    if not db_target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target not found")
    db.delete(db_target)
    db.commit()

    # Return 204 if monitor deleted
    return {"detail": "No Content"}

@router.get("/address/{address}", status_code=status.HTTP_200_OK, summary="Get a single target by address")
async def read_target_address(db: DBDependency, address: str = Path(..., min_length=7, max_length=45)):
    """ Get target by address """

    # raise an error if address fails IPvAnyAddress validation
    try:
        IPvAnyAddress(address)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid IP address") from exc
    
    # Check if target already exists from post data
    target = db.query(Targets).filter(Targets.address == address).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return target