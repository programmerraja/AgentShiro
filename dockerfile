FROM python:3.11-slim

# RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir torch torchvision transformers pillow accelerate sentencepiece

WORKDIR /app
COPY run_lfm.py /app/run_lfm.py

CMD ["python", "/app/run_lfm.py"]