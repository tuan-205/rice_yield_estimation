FROM python:3.12-slim
WORKDIR /app
COPY web/api/requirements.txt /app/web/api/requirements.txt
COPY notebook/requirements-training.txt /app/notebook/requirements-training.txt
RUN pip install --no-cache-dir -r web/api/requirements.txt
COPY web/api /app/web/api
COPY web/dist /app/web/dist
COPY models/model_comparison /app/models/model_comparison
EXPOSE 8080
CMD ["sh", "-c", "uvicorn web.api.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
