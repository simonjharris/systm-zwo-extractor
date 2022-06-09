FROM python:3.9-slim
ENV TZ=Europe/London
RUN apt-get update
WORKDIR /app
RUN pip install gunicorn uvicorn fastapi requests
COPY . /app
CMD python main.py