# Kinetic - Routers

## Description

Kinetic contains multiple router files located in the `kinetic/routers` directory. Each route file serves a specific purpose.

## File List

- routers/agents.py: CRUD operations for agents db table
- routers/console.py: Server Console
- routers/hosts.py: CRUD operations for hosts db table
- routers/monitors.py: CRUD operations for monitors db table
- routers/volley.py: Job handling for volley agents.

## Usage

`app.include_router(<filename>.router)`
