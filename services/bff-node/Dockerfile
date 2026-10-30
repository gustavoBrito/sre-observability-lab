FROM node:22-alpine

WORKDIR /app

# Dependency layer first, so local code edits do not reinstall packages
COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund

COPY otel.js server.js ./

EXPOSE 8000 9001

CMD ["node", "-r", "./otel.js", "server.js"]
