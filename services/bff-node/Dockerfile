FROM node:22-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund

COPY otel.js src ./

EXPOSE 8000 9001

CMD ["node", "-r", "./otel.js", "src/index.js"]
