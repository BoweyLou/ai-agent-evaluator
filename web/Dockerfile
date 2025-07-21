FROM node:18-alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev for building)
RUN npm install

# Copy app source
COPY . .

# Build the app for production
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Install serve for production
RUN npm install -g serve

# Change ownership of app directory
RUN chown -R nodejs:nodejs /app

USER nodejs

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000 || exit 1

# Expose port
EXPOSE 3000

# Start app with serve in production, or dev server in development
CMD ["sh", "-c", "if [ \"$NODE_ENV\" = \"production\" ]; then serve -s build -l 3000; else npm start; fi"]