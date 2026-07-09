FROM python:3.12-slim

# ffmpeg es necesario para que yt-dlp una video+audio y para extraer el MP3
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p downloads logs

ENV PYTHONUNBUFFERED=1

# La plataforma (Railway/Render) inyecta la variable PORT automáticamente;
# app/config.py ya la lee con os.getenv("PORT", "5000").
CMD ["python", "main.py"]
