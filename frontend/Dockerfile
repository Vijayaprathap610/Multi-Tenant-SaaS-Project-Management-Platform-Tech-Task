# Build stage: Node 24 (Maintenance LTS until 2028-04-30; see docs/versions.md)
FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
# Install from the lockfile when present; lifecycle scripts are off so a hijacked package cannot run code at install time.
RUN if [ -f package-lock.json ]; then npm ci --ignore-scripts; else npm install --ignore-scripts; fi
COPY . .
RUN npm run build

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
