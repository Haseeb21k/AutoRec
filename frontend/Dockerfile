# Stage 1: Build
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Copy config to 'templates' dir to enable auto-envsubst
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Default backend URL to prevent crash if not set (but should be set in Railway)
ENV BACKEND_URL=http://localhost:8000

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]