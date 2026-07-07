# ==========================================
# STAGE 1: Build the React frontend
# ==========================================
FROM node:20-alpine AS builder
WORKDIR /app

# Install dependencies first (for caching layers)
COPY package.json ./
RUN npm install

# Copy source code and build the production static files
COPY vite.config.js index.html ./
COPY src/ ./src/
COPY public/ ./public/
RUN npm run build

# ==========================================
# STAGE 2: Set up the Python FastAPI server
# ==========================================
FROM python:3.11-slim
WORKDIR /server

# Set system environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend server code
COPY server/ ./

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /dist

# Expose port (default for local, overridden by Cloud Run PORT env)
EXPOSE 8000

# Start backend server binding to the PORT environment variable (default 8000)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
