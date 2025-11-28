FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jdk-headless wget unzip ca-certificates gradle \
    && rm -rf /var/lib/apt/lists/*

ENV ANDROID_SDK_ROOT=/opt/android-sdk
RUN mkdir -p $ANDROID_SDK_ROOT/cmdline-tools \
    && wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/tools.zip \
    && unzip -q /tmp/tools.zip -d $ANDROID_SDK_ROOT/cmdline-tools \
    && mv $ANDROID_SDK_ROOT/cmdline-tools/cmdline-tools $ANDROID_SDK_ROOT/cmdline-tools/latest \
    && rm /tmp/tools.zip \
    && yes | $ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager --licenses \
    && $ANDROID_SDK_ROOT/cmdline-tools/latest/bin/sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

ENV PATH="$PATH:$ANDROID_SDK_ROOT/cmdline-tools/latest/bin:$ANDROID_SDK_ROOT/platform-tools"

WORKDIR /app
COPY builder/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY builder ./builder
COPY webapp/app ./webapp/app
ENV PYTHONPATH=/app
CMD ["python", "builder/main.py"]
