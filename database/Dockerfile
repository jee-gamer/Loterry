FROM python:3.11-slim-buster

RUN mkdir "/db"
WORKDIR /database

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

RUN ["chmod", "+x", "/database/docker-entrypoint.sh"]

ENTRYPOINT ["/database/docker-entrypoint.sh"]
CMD ["dataservice"]