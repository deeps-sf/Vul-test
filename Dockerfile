# Use the official Node.js 16 image.
# https://hub.docker.com/_/node
FROM node:16

# Create and change to the app directory.
WORKDIR /usr/src/app

# Copy package.json and package-lock.json to the container
COPY package*.json ./

# Install production dependencies.
RUN npm install --only=production

# Copy local code to the container
COPY . .

# Expose port 8080 to the outside once the container has launched
EXPOSE 8080

# Run the application
CMD ["npm", "start"]


FROM centos:7.9.2009
cd go && git checkout go1.25.5 && \

updated to cd go && git checkout go1.25.6 && \
