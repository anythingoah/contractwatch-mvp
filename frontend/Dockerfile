FROM node:26-slim AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:26-slim
WORKDIR /app
COPY --from=build /app ./
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000', r => process.exit(r.statusCode < 500 ? 0 : 1)).on('error', () => process.exit(1))"
CMD ["npm", "start"]
