# Stage 1: Build (Keep this the same)
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve with Caddy
FROM caddy:2-alpine

# Copy the build output to Caddy's default directory
COPY --from=build /app/dist /usr/share/caddy

# Copy your new Caddyfile
COPY Caddyfile /etc/caddy/Caddyfile

# Caddy uses the PORT env var automatically based on the Caddyfile above
EXPOSE 80
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]