FROM python:3.11-slim
WORKDIR /app
COPY builder/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY builder ./builder
COPY webapp/app ./webapp/app
ENV PYTHONPATH=/app
CMD ["python", "builder/main.py"]
