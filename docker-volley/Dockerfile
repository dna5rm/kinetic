FROM python:alpine3.19
RUN apk update
WORKDIR /srv
COPY ../volley.py .
RUN pip install --upgrade pip
RUN pip install pydantic requests scapy
ENV PYTHONUNBUFFERED 1
CMD ["watch", "timeout", "90", "python", "/srv/volley.py"]