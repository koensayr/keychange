# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the application code
COPY . /app/

# Install Python dependencies
RUN pip install --no-cache-dir ".[examples]"

# Create a non-root user
RUN useradd -m -r appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose any necessary ports (for SRT streaming)
EXPOSE 9999

# Default command to run the help
CMD ["keychange", "--help"]
