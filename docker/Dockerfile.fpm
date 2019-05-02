FROM ruby:2.5-slim-stretch
MAINTAINER Ashish Kulkarni <ashish@kulkarni.dev>

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        gcc \
        libarchive-tools \
        make \
        rpm \
        unzip \
        xz-utils \
        zip \
    && \
    apt-get clean && \
    rm --recursive /var/lib/apt/lists/*

RUN gem install fpm -v 1.10.2

ENTRYPOINT [ "fpm" ]
CMD [ "--help" ]
