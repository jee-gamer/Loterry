FROM python:3.10-slim

RUN pip install aiohttp redis

RUN mkdir -p "/app/tests/data"
COPY ./app.py /app
COPY ./client.py /app
COPY ./tests/data/blocks.json /app/tests/data

WORKDIR /app

ENTRYPOINT [ "python" ]

CMD ["/app/app.py" ]