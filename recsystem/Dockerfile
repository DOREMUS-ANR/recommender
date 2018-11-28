FROM python:3.6.5

COPY . /
RUN pip install -r requirements_server.txt

CMD ["export","LC_ALL=en_US.UTF-8"]
CMD ["export","LANG=en_US.UTF-8"]

ENTRYPOINT ["python"]
CMD ["/server.py", "-c","/config/config_prod.json"]
