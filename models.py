""" Database Models """

from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Float, DateTime, BigInteger
from sqlalchemy.orm import relationship, backref
from database import Base
from uuid import uuid4 as UUID

# Define the table to store environment variables
class Env(Base):
    """ Environment Table """
    __tablename__ = "env"

    key         = Column(String, primary_key=True, index=True, nullable=False)
    value       = Column(String, index=True, default="", nullable=True)

# Define the Agents model
class Agents(Base):
    """ Agents Table """
    __tablename__ = "agents"

    id          = Column(String, primary_key=True, index=True, default=str(UUID()))
    name        = Column(String, unique=True, index=True, nullable=False)
    address     = Column(String, unique=True, index=True, nullable=True)
    description = Column(String, index=True, default="")
    last_seen   = Column(DateTime, default=datetime.now())
    is_active   = Column(Boolean, default=True, nullable=False)

# Define the Hosts model
class Hosts(Base):
    """ Hosts Table """
    __tablename__ = "hosts"

    id          = Column(String, primary_key=True, index=True, default=str(UUID()))
    address     = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, index=True, default="")
    is_active   = Column(Boolean, default=True, nullable=False)

# Define the Monitors model
class Monitors(Base):
    """ Monitors Table """
    __tablename__ = "monitors"

    id             = Column(String, primary_key=True, index=True, default=str(UUID()))
    description    = Column(String, index=True, default="")
    sample         = Column(BigInteger, default=0)
    current_loss   = Column(Integer, default=0)
    current_median = Column(Float, default=0)
    current_min    = Column(Float, default=0)
    current_max    = Column(Float, default=0)
    current_stddev = Column(Float, default=0)
    avg_loss       = Column(Integer, default=0)
    avg_median     = Column(Float, default=0)
    avg_min        = Column(Float, default=0)
    avg_max        = Column(Float, default=0)
    avg_stddev     = Column(Float, default=0)
    prev_loss      = Column(Integer, default=0)
    last_clear     = Column(DateTime, default=datetime.now())
    last_down      = Column(DateTime, default=datetime.now())
    last_update    = Column(DateTime, default=datetime.now())
    total_down     = Column(Integer, default=0)
    agent_id       = Column(String, ForeignKey('agents.id'), nullable=False)
    host_id        = Column(String, ForeignKey('hosts.id'), nullable=False)
    protocol       = Column(String, default="icmp")
    port           = Column(Integer, default=0)
    dscp           = Column(String, default="BE")
    pollcount      = Column(Integer, default=20)
    pollinterval   = Column(Integer, default=60)
    is_active      = Column(Boolean, default=True, nullable=False)

    agent          = relationship("Agents", backref=backref("monitors", cascade="all, delete-orphan"))
    host           = relationship("Hosts", backref=backref("monitors", cascade="all, delete-orphan"))

"""
# Define the table to store the user accounts
class Users(Base):
    __tablename__ = "users"

    id          = Column(String, primary_key=True, index=True, default=str(UUID()))
    username    = Column(String, unique=True, index=True, nullable=False)
    password    = Column(String, index=True, nullable=False)
    is_active   = Column(Boolean, default=True, nullable=False)
    is_admin    = Column(Boolean, default=False, nullable=False)
"""