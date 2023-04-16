FROM python:3.10-slim

RUN mkdir -p "/app"
COPY Database/database/model.py /app
# uhh use query or model??


WORKDIR /app

ENV BotApi=""

RUN pip install sqlAlchemy
#COPY lottery.py /app

ENTRYPOINT [ "python" ]

CMD ["/app/model.py" ]