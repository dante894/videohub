FROM python:3.12-slim

# ffmpeg: para que yt-dlp una video+audio y extraiga el MP3.
# curl/unzip: necesarios para instalar Deno.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Deno: yt-dlp lo usa como runtime de JavaScript para desofuscar firmas de
# YouTube. Sin esto, YouTube devuelve una lista de formatos incompleta y
# las descargas fallan con "Requested format is not available".
RUN curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh -s -- -y \
    && deno --version

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads logs

ENV PYTHONUNBUFFERED=1

# La plataforma (Railway/Render) inyecta la variable PORT automáticamente;
# app/config.py ya la lee con os.getenv("PORT", "5000").
CMD ["python", "main.py"]
