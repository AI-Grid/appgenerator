FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jdk-headless wget unzip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV ANDROID_SDK_ROOT=/opt/android-sdk

WORKDIR /app
COPY builder/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY builder ./builder
COPY webapp/app ./webapp/app
ENV PYTHONPATH=/app
CMD ["python", "builder/main.py"]
