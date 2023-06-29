FROM python:3.11-slim-buster

RUN mkdir "/db"
RUN mkdir "/runtime"
WORKDIR /runtime

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

RUN ["chmod", "+x", "/runtime/docker-entrypoint.sh"]

ENTRYPOINT ["/runtime/docker-entrypoint.sh"]
CMD ["dataservice"]
