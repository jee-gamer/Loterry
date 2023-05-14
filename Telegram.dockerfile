FROM python:3.10-slim

RUN mkdir -p "/app"
COPY bot.py /app

WORKDIR /app

ENV BotApi=""

RUN pip install aiogram
COPY old_lottery_class.py /app

ENTRYPOINT [ "python" ]

CMD ["/app/bot.py" ]