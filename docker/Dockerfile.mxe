FROM debian:stretch

RUN apt-get update && apt-get install -y -q --no-install-recommends \
    autoconf \
    automake \
    autopoint \
    bash \
    bison \
    bzip2 \
    flex \
    g++ \
    g++-multilib \
    gettext \
    git \
    gperf \
    intltool \
    libc6-dev-i386 \
    libgdk-pixbuf2.0-dev \
    libltdl-dev \
    libssl-dev \
    libtool-bin \
    libxml-parser-perl \
    make \
    openssl \
    p7zip-full \
    patch \
    perl \
    pkg-config \
    python \
    ruby \
    scons \
    sed \
    unzip \
    wget \
    xz-utils \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/mxe/mxe.git /opt/mxe \
    && cd /opt/mxe \
    && git checkout 8a0bc9f7 \
    && make MXE_TARGETS="i686-w64-mingw32.static x86_64-w64-mingw32.static" \
        cc zlib openssl libpng jpeg
# ===== 8a0bc9f7 =====
# zlib      1.2.11
# openssl   1.1.0h
# libpng    1.6.34
# jpeg      9c
# ====================

ENV PATH="${PATH}:/opt/mxe/usr/bin" CFLAGS=-w CXXFLAGS=-w
