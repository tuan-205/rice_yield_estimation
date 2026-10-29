FROM python:3.12-slim
WORKDIR /app
COPY web/api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY web/api /app/web/api
COPY web/dist /app/web/dist
EXPOSE 8080
CMD ["sh", "-c", "uvicorn web.api.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
