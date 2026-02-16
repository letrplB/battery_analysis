FROM python:3.13-slim

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY battery_cycle_analyzer/ battery_cycle_analyzer/

# Streamlit config
COPY .streamlit/ .streamlit/

EXPOSE 8501

HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

WORKDIR /app/battery_cycle_analyzer

ENTRYPOINT ["streamlit", "run", "src/gui_modular.py", "--server.port=8501", "--server.address=0.0.0.0"]
