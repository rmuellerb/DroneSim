FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf 
COPY nginx.conf /etc/nginx/conf.d
COPY ssl/privkey1.pem /etc/nginx/ssl/privkey1.pem
COPY ssl/fullchain1.pem /etc/nginx/ssl/fullchain1.pem
