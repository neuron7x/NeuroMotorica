FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -U pip && pip install -e ".[dev]"
EXPOSE 8000
CMD ["neuromotorica", "run-api", "--host", "0.0.0.0", "--port", "8000"]
