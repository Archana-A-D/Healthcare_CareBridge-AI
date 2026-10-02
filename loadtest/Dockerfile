FROM python:3.12-slim

WORKDIR /loadtest
RUN pip install --no-cache-dir "locust>=2.32,<3" "redis>=5,<7"
COPY locustfile.py /loadtest/locustfile.py

EXPOSE 8089
ENTRYPOINT ["locust"]
CMD ["-f", "/loadtest/locustfile.py", "--host", "http://frontend", "--web-host", "0.0.0.0"]
