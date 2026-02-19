# Python ka lightweight version use karenge
FROM python:3.10-slim-buster

# Working directory set karte hain
WORKDIR /app

# System dependencies install karte hain (git aur ffmpeg zaroori hain)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Requirements file copy karke libraries install karte hain
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Baaki sara code copy karte hain
COPY . .

# Bot ko start karne ki command
CMD ["python3", "main.py"]
