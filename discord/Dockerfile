FROM python:3.10-slim

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p "/app"
RUN mkdir -p "/app/BackendClient"
COPY ./backendClient.py /app/BackendClient
COPY discordBot.py /app
COPY . /app
WORKDIR /app

ENV BotApi=""

ENTRYPOINT [ "python" ]

CMD ["/app/discordBot.py" ]