"""
Kinetic - Generate RRD graph
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
