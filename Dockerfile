FROM python:alpine3.19
RUN apk -U upgrade
RUN apk add --no-cache build-base font-freefont rrdtool rrdtool-dev
WORKDIR /srv
COPY . .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENV PYTHONUNBUFFERED 1
EXPOSE 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--forwarded-allow-ips", "*"]
