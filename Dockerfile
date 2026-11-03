FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
WORKDIR /app

COPY requirements.txt requirements-llm.txt ./
RUN pip install -r requirements.txt -r requirements-llm.txt

COPY src ./src
COPY docker/entrypoint.sh ./entrypoint.sh

RUN useradd --create-home appuser && mkdir -p /data/index && chown appuser /data/index && chmod +x entrypoint.sh
USER appuser

# Los documentos y el padrón se montan como volúmenes de solo lectura; las credenciales van por entorno.
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8501/_stcore/health')" || exit 1
ENTRYPOINT ["./entrypoint.sh"]
