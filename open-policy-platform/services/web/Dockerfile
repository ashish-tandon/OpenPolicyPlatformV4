FROM node:18-alpine
WORKDIR /app
RUN apk add --no-cache curl
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]