FROM rappdw/docker-java-python

COPY . /
RUN mkdir /data
RUN mkdir /data/all_connections
RUN mkdir /emb
RUN pip install --no-cache-dir -r requirements.txt

CMD ["export","LC_ALL=en_US.UTF-8"]
CMD ["export","LANG=en_US.UTF-8"]

ENTRYPOINT ["python"]
CMD ["server.py"]
