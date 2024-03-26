FROM python:alpine

ENV PYTHONUNBUFFERED 1

WORKDIR /srv

COPY . .

RUN apk -U upgrade
RUN apk add --no-cache build-base font-freefont rrdtool rrdtool-dev
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers", "--forwarded-allow-ips", "*"]
