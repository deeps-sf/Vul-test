FROM python:3.8-alpine
RUN apk add --update git
RUN pip -v install --upgrade pip


