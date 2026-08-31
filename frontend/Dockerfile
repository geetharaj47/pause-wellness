# Stage 1: Build compilation environment
FROM node:20-alpine AS build
WORKDIR /frontend

# Copy dependency configuration
COPY package.json ./

# Install npm packages
RUN npm install

# Copy source repository
COPY . .

# Compile static distribution bundle
RUN npm run build

# Stage 2: Serve compiled code via Nginx
FROM nginx:alpine
COPY --from=build /frontend/dist /usr/share/nginx/html

# Expose default HTTP port
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
