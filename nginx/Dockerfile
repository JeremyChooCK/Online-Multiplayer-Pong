FROM nginx:latest

RUN apt-get update && apt-get install -y openssl && \
    mkdir /etc/nginx/ssl && \
    openssl req -newkey rsa:4096 -x509 -sha256 -days 365 -nodes -out /etc/nginx/ssl/jechoo.crt -keyout /etc/nginx/ssl/jechoo.key -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=localhost"

COPY default.conf /etc/nginx/conf.d/default.conf
