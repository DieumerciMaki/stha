FROM node:24-bookworm-slim AS interface
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /project
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY backend/requirements*.txt /project/backend/
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend /project/backend
COPY models /project/models
COPY samples /project/samples
COPY --from=interface /build/dist /project/frontend/dist
ENV PYTHONPATH=/project/backend
CMD ["sh","-c","python -m alembic -c backend/alembic.ini upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001"]
