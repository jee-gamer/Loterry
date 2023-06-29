FROM python:3.10-slim

RUN mkdir -p "/app"
COPY discordBot.py /app

WORKDIR /app

ENV BotApi=""

RUN pip install discord
COPY old_lottery_class.py /app

ENTRYPOINT [ "python" ]

CMD ["/app/discordBot.py" ]