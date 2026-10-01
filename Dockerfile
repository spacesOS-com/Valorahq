# REVIEW ONLY: pin the reviewed nginx image digest before staging.
FROM nginx:1.28.0-alpine
COPY consumer/ /srv/consumer/
COPY deploy/nginx.conf /etc/nginx/nginx.conf
RUN nginx -t
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
