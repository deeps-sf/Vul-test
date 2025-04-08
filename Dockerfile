FROM node:16-alpine
WORKDIR /usr/src/app
COPY package.json package-lock.json ./
RUN npm install --force
RUN npm install react-scripts@latest --force
RUN apk update && apk add --no-cache go
COPY . .
RUN npm run build:prod
CMD npm run start:prod
