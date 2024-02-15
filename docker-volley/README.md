# Docker Image for the Kinetic Volley.py Agent only.

This Docker image is designed to build a small container that runs only the Kinetic Volley.py agent. The agent requires the following environment variables to be set when it is called: `KINETIC_AGENT_ID` and `KINETIC_SERVER`.

## Usage

To build and use this Docker image, you can follow these steps:


```bash
docker build -t "kinetic/volley:testing" .
docker run --name "volley" --env KINETIC_AGENT_ID="00000000-0000-0000-0000-000000000000" --env KINETIC_SERVER="https://kinetic.local" -d "kinetic/volley:testing"
```