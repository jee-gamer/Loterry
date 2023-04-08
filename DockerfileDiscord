FROM python:3.10-slim

RUN mkdir -p "/app"
COPY DiscordBotFile/discordBot.py /app

WORKDIR /app

ENV BotApi=""

RUN pip install discord
COPY lottery.py /app

ENTRYPOINT [ "python" ]

CMD ["/app/discordBot.py" ]