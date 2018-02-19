FROM rappdw/docker-java-python

COPY . /
RUN pip install -r requirements.txt

CMD ["export","LC_ALL=en_US.UTF-8"]
CMD ["export","LANG=en_US.UTF-8"]

ENTRYPOINT ["python"]
CMD ["/server.py"]
