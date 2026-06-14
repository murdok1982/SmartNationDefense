FROM node:20-alpine
WORKDIR /app
RUN addgroup -S sesis && adduser -S sesis -G sesis
COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps
COPY . .
RUN chown -R sesis:sesis /app
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=10s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1
USER sesis
CMD ["npm", "run", "dev"]
