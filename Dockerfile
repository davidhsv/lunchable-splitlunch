# Use Python base image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Install uv (Python package installer/build tool)
RUN pip install --no-cache-dir uv

# Install pipx
RUN pip install --no-cache-dir pipx && \
    pipx ensurepath

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock README.md ./
COPY lunchable_splitlunch/ ./lunchable_splitlunch/

# Build the project using uv
RUN uv build

# Install the built wheel using pipx
RUN pipx install dist/lunchable_splitlunch-*.whl --force

# Create a script to run the refresh command with hardcoded flags
# This script will source environment variables from /app/env.sh
RUN echo '#!/bin/bash\n\
set -a\n\
[ -f /app/env.sh ] && source /app/env.sh\n\
set +a\n\
# Hardcoded command: refresh with dated-after and allow-self-paid flags\n\
splitlunch refresh --dated-after "2025-11-06T16:30:00" --allow-self-paid' > /app/run-refresh.sh && \
    chmod +x /app/run-refresh.sh

# Set up cron job to run every 2 minutes
RUN echo '*/2 * * * * root /app/run-refresh.sh >> /var/log/splitlunch.log 2>&1' > /etc/cron.d/splitlunch && \
    chmod 0644 /etc/cron.d/splitlunch && \
    crontab /etc/cron.d/splitlunch

# Create log file
RUN touch /var/log/splitlunch.log

# Set environment variables (can be overridden via docker run -e)
ENV SPLITWISE_CONSUMER_KEY=""
ENV SPLITWISE_CONSUMER_SECRET=""
ENV SPLITWISE_API_KEY=""
ENV LUNCHMONEY_ACCESS_TOKEN=""

# Create entrypoint script that writes env vars to file for cron to use
RUN echo '#!/bin/bash\n\
# Write environment variables to file for cron to access\n\
printenv | grep -E "^(SPLITWISE_|LUNCHMONEY_)" > /app/env.sh\n\
# Start cron daemon\n\
cron\n\
# Tail the log file to keep container running\n\
tail -f /var/log/splitlunch.log' > /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Start cron in foreground
CMD ["/app/entrypoint.sh"]
