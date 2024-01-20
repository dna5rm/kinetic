"""
Kinetic - CRUD operations for agents db table
"""

from typing import Annotated, Optional, Union
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from starlette import status
from models import Env
from database import SessionLocal

router = APIRouter(
    prefix="/env",
    tags=["environment"]
)

# allowed environment keys
allowed_keys = [
    "NOTIFY_EMAIL", # email to send notifications to
    "NOTIFY_ENABLED", # enable/disable notifications
    "NOTIFY_PERIOD", # notification period in seconds
    "SMTP_SERVER", # smtp server to use
    "SMTP_PORT", # smtp port to use
    "SMTP_USERNAME", # smtp username to use
    "SMTP_PASSWORD", # smtp password to use
]

def get_db():
    """ Get database """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDependency = Annotated[Session, Depends(get_db)]

class EnvModel(BaseModel):
    """ Environment Model """
    # constrain key to any value within allowed_keys
    key: str = Field(..., description="Environment variable name", pattern="|".join(allowed_keys))
    value: Union[str, int, bool] = Field(..., description="Environment variable value")

@router.get("/", status_code=status.HTTP_200_OK,
    summary="Get all environment key value pairs",
    description="Display all environment key value pairs",
    responses={
        200: {
            "description": "Successful operation",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No Content"
                    }
                }
            }
        },
        204: {"description": "No Content"}
    }
)
async def read_env_all(db: DBDependency):
    """ Get all environment keys """
    env = db.query(Env).all()
    if not env:
        raise HTTPException(status_code=204, detail="No Content")
    return jsonable_encoder(env)

@router.post("/", status_code=status.HTTP_201_CREATED,
    summary="Create an environment key value pair",
    description="Create an environment key value pair",
    responses={
        201: {
            "description": "Successful operation",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Created"
                    }
                }
            }
        },
        400: {"description": "Environment key already exists"}
    }
)
async def create_env(db: DBDependency, body: EnvModel):
    """ Create an allowed environment key value pair """

    # check if environment key already exists
    env = db.query(Env).filter(Env.key == body.key).first()
    if env:
        raise HTTPException(status_code=400, detail="Environment key already exists")

    # create environment key
    env = Env(key=body.key, value=body.value)
    db.add(env)
    db.commit()
    db.refresh(env)
    return {"detail": "Created"}

@router.get("/{key}", status_code=status.HTTP_200_OK,
    summary="Get an environment key value pair",
    description="Get an environment key value pair",
    responses={
        200: {
            "description": "Successful operation",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No Content"
                    }
                }
            }
        },
        204: {"description": "No Content"}
    }
)
async def read_env(db: DBDependency, key: str = Path(..., description="Environment variable name")):
    """ Get an environment key value pair """
    env = db.query(Env).filter(Env.key == key).first()
    if not env:
        raise HTTPException(status_code=204, detail="No Content")
    return jsonable_encoder(env)

@router.put("/{key}", status_code=status.HTTP_200_OK,
    summary="Update an environment key value pair",
    description="Update an environment key value pair",
    responses={
        200: {
            "description": "Successful operation",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Updated"
                    }
                }
            }
        },
        204: {"description": "No Content"}
    }
)
async def update_env(db: DBDependency, key: str = Path(..., description="Environment key name"), body: EnvModel = None):
    """ Update an environment key value pair """
    env = db.query(Env).filter(Env.key == key).first()
    if not env:
        raise HTTPException(status_code=204, detail="No Content")
    env.value = body.value
    db.commit()
    return {"detail": "Updated"}

@router.delete("/{key}", status_code=status.HTTP_200_OK,
    summary="Delete an environment key",
    description="Delete an environment key",
    responses={
        200: {
            "description": "Successful operation",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Deleted"
                    }
                }
            }
        },
        204: {"description": "No Content"}
    }
)
async def delete_env(db: DBDependency, key: str = Path(..., description="Environment key name")):
    """ Delete an environment key """
    env = db.query(Env).filter(Env.key == key).first()
    if not env:
        raise HTTPException(status_code=204, detail="No Content")
    db.delete(env)
    db.commit()
    return {"detail": "Deleted"}