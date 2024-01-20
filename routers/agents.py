"""
Kinetic - CRUD operations for agents db table
"""

from typing import Annotated, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from starlette import status
from models import Agents
from database import SessionLocal
from uuid import uuid4 as UUID

router = APIRouter(
    prefix="/agents",
    tags=["agents"]
)

def get_db():
    """ Get database """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

DBDependency = Annotated[Session, Depends(get_db)]

class AgentModel(BaseModel):
    """ Agent Model """
    name: str = Field(min_length=4, max_length=16, example="agent1")
    description: Optional[str] = Field(max_length=255, example="This is agent1")
    is_active: Optional[bool] = Field(example=True)

@router.get("/", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": [{
                    "id": "00000000-0000-0000-0000-000000000000",
                    "name": "agent1",
                    "description": "This is agent1",
                    "is_active": True
                    }]
                }
            }
        }
    }
)
async def read_agent_all(db: DBDependency):
    """ Get all agents """
    # Check the number of agents in the database
    count = db.query(Agents).count()
    if count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return db.query(Agents).all()

@router.get("/{agent_id}", status_code=status.HTTP_200_OK,
    responses={
        200: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "name": "agent1",
                    "description": "This is agent1",
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
async def read_agent_id(db: DBDependency, agent_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Get agent by id """
    agent = db.query(Agents).filter(Agents.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent

@router.post("/", status_code=status.HTTP_201_CREATED,
    responses={
        201: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "name": "agent1",
                    "description": "This is agent1",
                    "is_active": True
                    }
                }
            }
        }
    }
)
async def create_agent_id(db: DBDependency, agent: AgentModel):
    """ Create an agent """

    # Check if agent already exists from post data
    exists = db.query(Agents).filter(Agents.name == agent.name).first()

    # Return 409 if agent already exists
    if exists:
        raise HTTPException(status_code=409, detail=jsonable_encoder(exists))

    # If agent does not exist, create and return 201 with database entry
    db_agent = Agents(**agent.dict())

    # Generate UUID for agent
    db_agent.id = str(UUID())

    # Add agent to database
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent

@router.put("/{agent_id}", status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: { "content": {
            "application/json": {
                "example": {
                    "id": "00000000-0000-0000-0000-000000000000",
                    "name": "agent1",
                    "description": "This is agent1",
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
async def update_agent_id(db: DBDependency, agent: AgentModel, agent_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Update an agent """
    db_agent = db.query(Agents).filter(Agents.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if agent:
        db_agent.name = agent.name
        db_agent.description = agent.description
        db_agent.is_active = agent.is_active
        db.commit()
        db.refresh(db_agent)
    return db_agent

@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT,
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
async def delete_agent_id(db: DBDependency, agent_id: str = Path(..., min_length=36, max_length=36, pattern="^[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}$")):
    """ Delete an agent """
    db_agent = db.query(Agents).filter(Agents.id == agent_id).first()
    if not db_agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    db.delete(db_agent)
    db.commit()

    # Return 204 if monitor deleted
    return {"detail": "No Content"}

@router.get("/name/{agent_name}", status_code=status.HTTP_200_OK, summary="Get a single agent by name")
async def read_agent_name(db: DBDependency, agent_name: str = Path(..., min_length=4, max_length=16)):
    """ Get agent by name """
    agent = db.query(Agents).filter(Agents.name == agent_name).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent            