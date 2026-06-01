FROM python:3.13.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget \
        curl \
        unzip \
        ffmpeg \
        ca-certificates \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libc6 \
        libcairo2 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libx11-xcb1 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        xdg-utils \
        chromium \
        chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install MediaMTX (replace version as needed)
COPY stream/mediamtx/mediamtx /usr/local/bin/mediamtx
RUN chmod +x /usr/local/bin/mediamtx

# Set environment variables for Chromium/Chromedriver
ENV PATH="/usr/lib/chromium/:${PATH}"

# Copy your code
WORKDIR /app
COPY prr_experiments /app/prr_experiments
COPY experiment /app/experiment
COPY stream/mediamtx/mediamtx /usr/local/bin/mediamtx
RUN chmod +x /usr/local/bin/mediamtx

# Install Python dependencies
RUN pip install PyYAML==6.0.3 selenium==4.38.0 requests

# Expose ports if needed (e.g., for MediaMTX)
EXPOSE 8554 8888

# Default command
#CMD ["python", "prr_experiments/garden.py"]
CMD [ "/bin/sh" ]
