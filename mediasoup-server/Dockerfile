FROM node:18-bullseye

# Install dependencies for MediaSoup
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy server code
COPY server.js ./

# Expose WebSocket port and RTC ports
EXPOSE 3001
EXPOSE 40000-40999/udp

# Start MediaSoup server
CMD ["node", "server.js"]
