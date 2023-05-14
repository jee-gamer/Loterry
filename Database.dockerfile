FROM python:3.10-slim

RUN mkdir -p "/app"
COPY Database/database/model.py /app
# query is just a test script


WORKDIR /app

ENV BotApi=""

RUN pip install sqlAlchemy
#COPY old_lottery_class.py /app

ENTRYPOINT [ "python" ]

CMD ["/app/model.py" ]