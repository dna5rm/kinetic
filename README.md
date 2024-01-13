# Kinetic
> This is currently being rewritten to use FastAPI

Kinetic is a network monitoring tool

## Modules

- fastapi
- humanize
- jinja2
- requests
- rrdtool
- scapy
- sqlalchemy
- uvicorn[standard]

## Permission issues when using scapy

If you don't want to run as root you can give Python to generate packets by doing:

`sudo setcap cap_net_raw+ep /usr/bin/python3.11`
