FROM python:3.10-slim

RUN mkdir -p "/app"
COPY ./app.py /app
COPY ./client.py /app


WORKDIR /app

RUN pip install aiohttp redis


ENTRYPOINT [ "python" ]

CMD ["/app/app.py" ]