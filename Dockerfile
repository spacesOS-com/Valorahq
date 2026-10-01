# Pinned to operator local RepoDigest receipt 2026-10-01T03:14:51Z.
FROM nginx@sha256:df221db836e1754089190208cee7eeda94f233197056426eda74a43ab1abeac2
COPY consumer/ /srv/consumer/
COPY deploy/nginx.conf /etc/nginx/nginx.conf
RUN nginx -t
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
