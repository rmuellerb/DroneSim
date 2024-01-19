FROM nginx:latest

RUN rm /etc/nginx/conf.d/default.conf 
COPY nginx.conf /etc/nginx/conf.d
COPY ssl/privkey2.pem /etc/nginx/ssl/privkey1.pem
COPY ssl/fullchain2.pem /etc/nginx/ssl/fullchain1.pem
