FROM python:alpine3.19
RUN apk update \
  && apk add build-base \
    font-freefont rrdtool rrdtool-dev
WORKDIR /srv
COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
ENV PYTHONUNBUFFERED 1
COPY . .
EXPOSE 80
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]