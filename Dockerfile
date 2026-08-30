FROM python:3.11-slim

# System dependencies: ODBC Driver 17 for SQL Server (pyodbc) and the
# Tesseract OCR binary (pytesseract is just a Python wrapper around it).
# The Microsoft repo's signing key must be dearmored into the exact path
# its own prod.list expects (signed-by=/usr/share/keyrings/microsoft-prod.gpg)
# — just tee-ing the raw .asc into trusted.gpg.d works on some older apt/gpg
# combinations but fails signature verification on this image's apt.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg unixodbc unixodbc-dev tesseract-ocr \
    && curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -sSL https://packages.microsoft.com/config/debian/12/prod.list -o /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download NLTK data at build time so the first request doesn't pay for
# it (and doesn't fail if the container has no outbound access at runtime).
RUN python -c "import nltk; [nltk.download(p, quiet=True) for p in ['punkt','punkt_tab','averaged_perceptron_tagger','averaged_perceptron_tagger_eng','stopwords','maxent_ne_chunker','maxent_ne_chunker_tab','words']]"

COPY . .

EXPOSE 10000
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT:-10000} --workers 2 --timeout 120 app:app"]
