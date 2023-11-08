FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d
COPY nginx-selfsigned.key /etc/nginx/ssl/nginx-selfsigned.key
COPY nginx-selfsigned.crt /etc/nginx/ssl/nginx-selfsigned.crt
