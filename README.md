# Gunicorn
Like most Django applications, Kinetic runs as a WSGI application behind an HTTP server.

## Configuration

Kinetic ships with a default configuration file for gunicorn.
To use it, copy /opt/kinetic/contrib/gunicorn.py to /opt/kinetic/gunicorn.py.

## Building a virtual environment.

```
mkdir /opt/kinetic/venv
python3 -m venv /opt/kinetic/venv
source /opt/kinetic/venv/bin/activate
pip -r /opt/kinetic/requirements.txt
```

## systemd Setup

We'll use systemd to control both gunicorn and Kinetic's background worker process.
First, copy contrib/netbox.service and contrib/netbox-rq.service to the /etc/systemd/system/ directory and reload the systemd daemon:

```
cp -v /opt/kinetic/contrib/*.service /etc/systemd/system/
systemctl daemon-reload
```

Then, start the kinetic service and enable them to initiate at boot time:

```
systemctl start kinetic
systemctl enable kinetic
```

Note: If the Kinetic service fails to start, issue the command journalctl -eu kinetic to check for log messages that may indicate the problem.
