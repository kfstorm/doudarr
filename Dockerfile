FROM python:3.11.8-alpine3.19

RUN mkdir /app
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/* /app/doudarr/

VOLUME "/app/cache"

EXPOSE 8000

ENTRYPOINT [ "uvicorn", "doudarr.main:app", "--host", "0.0.0.0"]
