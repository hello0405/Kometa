# Self-contained build from source — no kometateam/kometa:base required.
# Compatible with Synology legacy docker build (no BuildKit cache mounts).
FROM python:3.13-slim

ENV TINI_VERSION=v0.19.0
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV BRANCH_NAME=tmdb-proxy
ENV KOMETA_DOCKER=True
ENV KOMETA_WEB_PORT=8787

COPY requirements.txt /requirements.txt

RUN echo "**** install system packages & python deps ****" \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      tzdata gcc g++ git wget curl \
      libffi-dev libxml2-dev libxslt1-dev zlib1g-dev libjpeg62-turbo-dev \
 && wget -O /tini "https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini-$(dpkg --print-architecture | awk -F- '{print $NF}')" \
 && chmod +x /tini \
 && pip3 install --no-cache-dir --upgrade -r /requirements.txt \
 && apt-get purge -y gcc g++ libffi-dev libxml2-dev libxslt1-dev zlib1g-dev libjpeg62-turbo-dev \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/* /requirements.txt /tmp/* /var/tmp/*

COPY . /

# Wire TMDB_PROXY env support into modules/tmdb.py
RUN python3 /scripts/wire_tmdb_proxy.py

VOLUME /config
WORKDIR /
EXPOSE 8787
# Web UI is the only long-running process (scheduler + locked runs).
# CLI still available: python3 /kometa.py --run ...
ENTRYPOINT ["/tini", "-s", "python3", "/webui/app.py"]
