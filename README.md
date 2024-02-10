# Kinetic
> This is currently being rewritten to use FastAPI

Kinetic is a network monitoring tool

## Permission issues when using scapy as a non-root user

If you don't want to run as root you can give Python to generate packets by doing:

`sudo setcap cap_net_raw+ep /usr/bin/python3.11`
