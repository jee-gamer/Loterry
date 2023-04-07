FROM python:3.10-slim

RUN mkdir -p "/app"
COPY ./discordBot.py /app

WORKDIR /app

ENV BotApi="MTA5MjcyNDc0NTQxNTQzMDE1NA.G_OCFi.szV8bVK2E6XdhX84XjlntPOEXyCCxhtvM3qS34"

RUN pip install discord
COPY ./lottery.py /app

ENTRYPOINT [ "python" ]

CMD ["/app/discordBot.py" ]