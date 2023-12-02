# Kinetic
> This is currently being rewritten to use FastAPI

Kinetic is a network monitoring tool

## Modules

pip install fastapi
pip install "uvicorn[standard]"
pip install sqlalchemy

## Permission issues

If you don't have to run as root you can give Python the same capabilities as /bin/ping, by doing:

`sudo setcap cap_net_raw+ep /usr/bin/python3.11`
