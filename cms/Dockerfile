# Valora CMS service. Build from the repository root:  docker build -f cms/Dockerfile .
# Node runs the server; Python renders exact previews with the site's own templates.
FROM node:24-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY _build ./_build
COPY assets ./assets
COPY cms ./cms
COPY index.html ./index.html
COPY guides ./guides
# Generates the stylesheet the article preview uses.
RUN python3 _build/insights_site.py
ENV NODE_ENV=production PORT=8000 CMS_STORAGE=github CMS_SITE_ROOT=/app CMS_DB_PATH=/data/cms.sqlite
VOLUME /data
EXPOSE 8000
USER node
CMD ["node", "cms/server.js"]
