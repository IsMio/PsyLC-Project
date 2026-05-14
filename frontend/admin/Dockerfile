FROM node:22-alpine AS builder

WORKDIR /app

RUN corepack enable

COPY package.json ./
RUN pnpm install --no-frozen-lockfile

COPY . .
ARG VITE_API_BASE_URL=/
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
RUN pnpm build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80
