# Kinetic

Kinetic is a network monitoring tool that utilizes an agent-based monitoring approach. It is designed to facilitate efficient and scalable monitoring of various systems across a WAN. Kinetic operates using a server-client architecture, where the Kinetic server listens for requests from agents, referred to as "volley agents". The server assigns a list of tests for the agents to perform. Upon completing these tests, the agents report the results back to the server.

## Features

- **Agent-based Testing:** Kinetic employs an agent-based monitoring architecture, distributing the monitoring workload across multiple agents. This ensures scalability and efficiency, offering a variety of vantage points across a WAN.
- **API First:** The configuration and maintenance of Kinetic are performed via an API, ensuring flexibility and ease of automation.
- **Centralized Monitoring:** Kinetic consolidates test results from the agents, providing a centralized location for monitoring and analyzing the health and performance of the monitored systems.
- **Intuitive Interface:** The user console is designed to be clean, user-friendly, and conducive for data exploration and viewing.
- **Simplicity:** Kinetic Monitors are capable of collecting and graphing round-trip times of ICMP or TCP packets, offering straightforward insights into network performance.

## Getting Started

To begin using Kinetic, first clone the Kinetic repository using `git clone https://github.com/dna5rm/kinetic.git`. There are two ways to run Kinetic: locally or using Docker.

1. Run the Kinetic server.
2. Configure the volley agents.
3. Specify the targets to be monitored.
4. Set up the individual monitors.
5. Deploy the volley agents.

### Running Kinetic Locally

1. Install the required dependencies: `pip install -r requirements.txt`.
2. Start the Kinetic server: `python main.py`.

### Running Kinetic as a Docker Container

1. Create the following `docker-compose.yml`

```yaml
---
services:
  kinetic:
    container_name: kinetic_server
    build: https://github.com/dna5rm/kinetic.git
    image: kinetic
    ports:
      - 8080:80
    volumes:
      - data:/srv/data
    restart: unless-stopped
volumes:
  data:
```

2. `docker compose up -d`

### Running the Agent as a Docker Container

1. Create the following `Dockerfile`

```bash
FROM python:alpine
ARG volley="https://github.com/dna5rm/kinetic/raw/master/volley.py"

ENV PYTHONUNBUFFERED 1

WORKDIR /srv

ADD ${volley} /srv/volley.py

RUN apk -U upgrade
RUN pip install --upgrade pip
RUN pip install pydantic requests scapy

CMD ["watch", "timeout", "90", "python", "/srv/volley.py"]
```

2. Building the image: `docker build -t "kinetic/volley" .`

3. Running the image: `docker run --name "kinetic_volley" --env KINETIC_AGENT_ID="00000000-0000-0000-0000-000000000000" --env KINETIC_SERVER="https://kinetic.local" -d "kinetic/volley"`

## Known Issues

### Permission Issues with Scapy locally as a Non-root User

If you encounter permission issues when running `volley.py` locally, you can grant your non-root users the capability to generate packets using scapy with the following command:

`sudo setcap cap_net_raw+ep /usr/bin/python3.11`
