# Kinetic - Routers

## Description

Kinetic contains multiple router files located in the `kinetic/routers` directory. Each route file serves a specific purpose.

## File List

- agent_jobs.py: Operations for monitor jobs
- agents.py: CRUD operations for agents db table
- console.py: Server Console
- hosts.py: CRUD operations for hosts db table
- monitors.py: CRUD operations for monitors db table
- status.py: Healthcheck status endpoint (pending)

## Usage

`app.include_router(<filename>.router)`
