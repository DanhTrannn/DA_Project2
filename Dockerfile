FROM postgres:16

RUN apt-get update \
    && apt-get install -y --no-install-recommends ruby \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /data
COPY install.sql /data/
COPY data/ /data/
COPY update_csvs.rb /data/
RUN cd /data && ruby update_csvs.rb && rm update_csvs.rb

COPY install.sh /docker-entrypoint-initdb.d/
WORKDIR /data/
