FROM python:3.8

LABEL maintainer="KienLe TV"

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir flask werkzeug

EXPOSE 5000
ENV FLASK_RUN_HOST=0.0.0.0
ENV PORT=5000

CMD ["python", "hello-k8s.py"]
